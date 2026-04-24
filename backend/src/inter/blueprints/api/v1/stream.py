"""
Endpoints for managing streams, including starting a stream, connecting to a stream, and managing
chat and polls through WebSockets and WebRTC.
"""

from asyncio import create_task, gather, sleep
import base64
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
from http.client import CREATED, NOT_FOUND, OK, UNAUTHORIZED
import json
from operator import itemgetter
from os import environ, urandom
import secrets
from typing import Literal, TypedDict
from aiortc import (
    MediaStreamTrack,
    RTCConfiguration,
    RTCDataChannel,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
import aiortc
from aiortc.rtcrtpreceiver import RemoteStreamTrack
from aiortc.sdp import candidate_from_sdp
import aiortc.contrib.media
from quart import abort, request, websocket
import quart
from pywebpush import WebPushException, webpush_async  # type: ignore
from sqlalchemy import select

from inter.models.client import Client
from inter.models.db.moderation import Moderation
from inter.models.poll import Option, Poll
from inter.common import get_session
from inter.models.stream import Stream


stream = quart.Blueprint("stream", __name__, url_prefix="/stream/")
streams: dict[int, Stream] = {}


@stream.route("/", methods=["POST", "DELETE"])
async def start_stream():
    """
    Start a stream for the user associated with the given stream token. Implements WHIP for
    compatibility with streaming software.
    """
    from inter.models.db.user import User

    async with get_session() as session, session.begin():
        token = request.headers.get("Authorization")
        if not token:
            return abort(UNAUTHORIZED)
        user = await User.find_by_token(session, token[len("Bearer ") :])
        if not user:
            return abort(UNAUTHORIZED)
        connection = RTCPeerConnection(
            RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
        )
        user_id = user.id
        stream = streams[user_id]
        stream.connection = connection

        @connection.on("connectionstatechange")
        async def _():
            print(f"tx connectionstatechange", connection.connectionState)
            if connection.connectionState == "connected":
                stream.start = datetime.now(timezone.utc).timestamp()
                async with get_session() as session, session.begin():
                    user = await session.get(User, user_id)
                    if not user:
                        return
                    for client in stream.clients:
                        if client.chat:
                            client.chat.send(
                                json.dumps(
                                    {
                                        "type": "system",
                                        "message": f"{user.username} is live!",
                                    }
                                )
                            )

                    for follower in await user.get_notified(session):
                        notify = await follower.get_notify(user, session)
                        if not notify:
                            continue
                        endpoint, p256dh, auth = notify
                        try:
                            await webpush_async(
                                {
                                    "endpoint": endpoint,
                                    "keys": {
                                        "p256dh": base64.urlsafe_b64encode(p256dh),
                                        "auth": base64.urlsafe_b64encode(auth),
                                    },
                                },
                                json.dumps(
                                    {
                                        "displayName": user.display_name,
                                        "username": user.username,
                                        "url": f"http://{request.host}/@{user.username}/watch",
                                    }
                                ),
                                environ["PRIVATE_VAPID_KEY"],
                                {"sub": f"mailto:matthew.li10@education.nsw.gov.au"},
                            )
                        except WebPushException as exception:
                            print(repr(exception))
                            await follower.set_notify(user, session)

            if connection.connectionState == "closed":
                if stream.video:
                    stream.video.stop()
                if stream.audio:
                    stream.audio.stop()
                stream.video = None
                stream.audio = None
                stream.relay = aiortc.contrib.media.MediaRelay()
                for client in stream.clients:
                    for track in client.tracks:
                        track.stop()
                await connection.close()
                connection.remove_all_listeners()
                stream.connection = None
                stream.start = None
                stream.clients = []

        @connection.on("datachannel")
        def _():
            print(f"tx datachannel")

        @connection.on("icecandidate")
        def _(candidate: RTCIceCandidate):
            print(f"tx icecandidate", candidate)

        @connection.on("icecandidateerror")
        def _():
            print(f"tx icecandidateerror")

        @connection.on("iceconnectionstatechange")
        def _():
            print(f"tx iceconnectionstatechange", connection.iceConnectionState)

        @connection.on("negotiationneeded")
        def _():
            print(f"tx negotiationneeded")

        @connection.on("signalingstatechange")
        def _():
            print(f"tx signalingstatechange", connection.signalingState)

        @connection.on("track")
        async def _(track: RemoteStreamTrack):
            print(f"tx track", track)
            if track.kind == "video":
                stream.video = track
            elif track.kind == "audio":
                stream.audio = track
            if stream.video and stream.audio:
                for client in stream.clients:
                    relayed = stream.relay.subscribe(stream.video)
                    client.connection.addTrack(relayed)
                    relayed = stream.relay.subscribe(stream.audio)
                    client.connection.addTrack(relayed)

        await connection.setRemoteDescription(
            RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
        )
        await connection.setLocalDescription(await connection.createAnswer())
        return quart.Response(
            connection.localDescription.sdp,
            status=CREATED,
            content_type="application/sdp",
            headers={
                "Location": f"{request.host_url}api/v1/stream/{user.username}/tx",
                "Link": '<stun:stun.l.google.com:19302>; rel="ice-server"',
            },
        )


@stream.route("/<string:username>/tx", methods=["DELETE"])
async def stream_tx_delete(username: str):
    """
    Receive a request to delete the stream for the user with the given username.
    """
    # TODO authenticate this route and implement it
    print("TX endpoint deleted at username:", username)
    return quart.Response(status=OK)


@stream.route("/auth", methods=["GET"])
async def ws_auth():
    """
    Authenticate a WebSocket connection for streaming by generating a token.
    """
    from inter.models.db.user import User

    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        data = f"{user.username}\n{int((datetime.now() + timedelta(seconds=10)).timestamp())}"
        signature = hmac.new(
            environ["STREAM_WS_AUTH_KEY"].encode(),
            data.encode(),
            sha256,
        ).hexdigest()
        return quart.Response(f"{data}\n{signature}")


@stream.websocket("/<string:username>/ws")
async def ws(username: str):
    """
    Handle a client's WebSocket connection for watching a stream.
    Every message from the client is a JSON object with a "type" field matching one of
    - "connect": Authenticate the client if a token is provided, establish a WebRTC connection, and
        manage their chat and poll data channels. Both data channels are created by the client
        and identified by their label ("chat" and "poll" respectively).
    - "candidate": Add the provided ICE candidate to the client's WebRTC connection on this side.
    """
    from inter.models.db.user import User

    async with get_session() as session, session.begin():
        streamer = await User.find_by_username(session, username)
        if not streamer:
            return quart.Response(status=NOT_FOUND)
        streamer_id = streamer.id
        stream = streams[streamer_id]
    client = None
    candidates: list[RTCIceCandidate] = []

    async def rx():
        """
        Receive task responsible for handling messages from the client through its WebSocket.
        """
        nonlocal client, stream
        while True:
            data = await websocket.receive_json()
            match data["type"]:
                case "connect":
                    if data["token"]:
                        username, expire, signature = data["token"].splitlines()
                        if datetime.now().timestamp() < float(
                            expire
                        ) and secrets.compare_digest(
                            hmac.new(
                                environ["STREAM_WS_AUTH_KEY"].encode(),
                                f"{username}\n{expire}".encode(),
                                sha256,
                            ).hexdigest(),
                            signature,
                        ):
                            async with get_session() as session, session.begin():
                                user = await User.find_by_username(session, username)
                                viewer = user.id if user else None
                        else:
                            viewer = None
                    else:
                        viewer = None
                    new_client = Client(
                        RTCPeerConnection(
                            RTCConfiguration(
                                [RTCIceServer(urls=["stun:stun.l.google.com:19302"])]
                            )
                        ),
                        viewer,
                    )
                    connection = new_client.connection
                    stream.clients.append(new_client)

                    @connection.on("connectionstatechange")
                    async def _():
                        print(f"connectionstatechange", connection.connectionState)
                        if connection.connectionState == "closed":
                            await connection.close()
                            if new_client.chat:
                                new_client.chat.close()
                            for track in new_client.tracks:
                                track.stop()
                            if new_client in stream.clients:
                                stream.clients.remove(new_client)

                    async def manage_chat(channel: RTCDataChannel):
                        """
                        Manage the client's chat data channel by relaying messages between the
                        client and the stream's chat.
                        """
                        new_client.chat = channel
                        for message in [*stream.chat]:
                            channel.send(message)
                        channel.send(
                            json.dumps(
                                {
                                    "type": "system",
                                    "message": "Connected to chat!",
                                }
                            )
                        )

                        @channel.on("message")
                        async def _(data: str):
                            if not viewer:
                                return
                            print("message", data)
                            text, replying = itemgetter("text", "replying")(
                                json.loads(data)
                            )
                            async with get_session() as session, session.begin():
                                user = await session.get(User, viewer)
                                if not user:
                                    return
                                moderation = await session.scalar(
                                    select(Moderation).where(
                                        Moderation.subject == streamer_id,
                                        Moderation.target == viewer,
                                    )
                                )
                                if moderation:
                                    if moderation.duration is None:
                                        channel.send(
                                            json.dumps(
                                                {
                                                    "type": "system",
                                                    "message": "You are banned from chatting.",
                                                }
                                            )
                                        )
                                        return
                                    if (
                                        moderation.start + moderation.duration
                                        > datetime.now().timestamp()
                                    ):
                                        channel.send(
                                            json.dumps(
                                                {
                                                    "type": "system",
                                                    "message": f"You are timed out for {int(moderation.start + moderation.duration - datetime.now().timestamp())} more seconds.",
                                                }
                                            )
                                        )
                                        return
                                    else:
                                        await session.delete(moderation)

                                message = json.dumps(
                                    {
                                        "type": "message",
                                        "time": int(datetime.now().timestamp()),
                                        "message": text,
                                        "replying": replying,
                                        "username": user.username,
                                        "colour": user.colour,
                                        "id": urandom(16).hex(),
                                    }
                                )

                            stream.chat.append(message)
                            for client in stream.clients:
                                if client.chat:
                                    client.chat.send(message)

                    async def manage_polls(channel: RTCDataChannel):
                        """
                        Manage the client's poll data channel by updating the client with the
                        state of current polls and replicating votes between clients.
                        """
                        new_client.poll = channel

                        def update(client: Client = new_client):
                            """
                            Update the client with the current state of polls, including vote counts
                            if the poll is finished or if the client is authorised to see them.
                            """
                            if not client.poll:
                                return

                            def update_poll(poll: Poll):
                                show_votes = poll.finished or (
                                    client.viewer
                                    and (
                                        any(
                                            any(
                                                user == client.viewer
                                                for user in option.users
                                            )
                                            for option in poll.options
                                        )
                                        or client.viewer == streamer_id
                                    )  # TODO include moderators
                                )
                                return {
                                    "id": poll.id,
                                    "question": poll.question,
                                    "options": (
                                        [
                                            {
                                                "text": option.text,
                                                "percent": (
                                                    len(option.users)
                                                    / sum(
                                                        len(option.users)
                                                        for option in poll.options
                                                    )
                                                    * 100
                                                    if any(
                                                        option.users
                                                        for option in poll.options
                                                    )
                                                    else 0
                                                ),
                                            }
                                            for option in poll.options
                                        ]
                                        if show_votes
                                        else [
                                            {"text": option.text}
                                            for option in poll.options
                                        ]
                                    ),
                                    "duration": poll.duration,
                                    "start": poll.start,
                                }

                            client.poll.send(
                                json.dumps(
                                    {
                                        "type": "update",
                                        "polls": [
                                            update_poll(poll) for poll in stream.polls
                                        ],
                                    }
                                )
                            )

                        def update_all():
                            for client in stream.clients:
                                update(client)

                        update()

                        @channel.on("message")
                        async def _(data: str):
                            class Update(TypedDict):
                                """
                                Request to receive an update on the current polls.
                                """

                                type: Literal["update"]

                            class Start(TypedDict):
                                """
                                Request to start a new poll.
                                """

                                type: Literal["start"]
                                question: str
                                options: list[str]
                                duration: float

                            class Vote(TypedDict):
                                """
                                Request to vote on an existing poll.
                                """

                                type: Literal["vote"]
                                poll: str
                                option: int

                            parsed: Update | Vote | Start = json.loads(data)
                            match parsed["type"]:
                                case "update":
                                    update()
                                case "start":
                                    async with (
                                        get_session() as session,
                                        session.begin(),
                                    ):
                                        user = await session.get(User, viewer)
                                        # TODO include moderators
                                        if not user or user.id != streamer_id:
                                            return
                                    poll = Poll(
                                        parsed["question"],
                                        [Option(text) for text in parsed["options"]],
                                        parsed["duration"],
                                        datetime.now().timestamp(),
                                    )
                                    stream.polls.append(poll)

                                    async def delete_poll():
                                        await sleep(poll.duration + 60)
                                        stream.polls.remove(poll)
                                        update_all()

                                    create_task(delete_poll())
                                    update_all()
                                case "vote":
                                    if not viewer:
                                        return
                                    poll = next(
                                        (
                                            poll
                                            for poll in stream.polls
                                            if poll.id == parsed["poll"]
                                        ),
                                        None,
                                    )
                                    if not poll or poll.finished:
                                        return
                                    option = (
                                        poll.options[parsed["option"]]
                                        if 0 <= parsed["option"] < len(poll.options)
                                        else None
                                    )
                                    if not option:
                                        return
                                    option.users.add(viewer)
                                    update_all()
                                case _:
                                    pass

                    @connection.on("datachannel")
                    async def _(channel: RTCDataChannel):
                        print(f"datachannel", channel)
                        match channel.label:
                            case "chat":
                                await manage_chat(channel)
                            case "poll":
                                await manage_polls(channel)
                            case _:
                                pass

                    @connection.on("iceconnectionstatechange")
                    def _():
                        print(
                            f"iceconnectionstatechange",
                            connection.iceConnectionState,
                        )

                    @connection.on("negotiationneeded")
                    def _():
                        print(f"negotiationneeded")

                    @connection.on("signalingstatechange")
                    def _():
                        print(f"signalingstatechange", connection.signalingState)

                    @connection.on("track")
                    def _(track: MediaStreamTrack):
                        print(f"track")

                    await connection.setRemoteDescription(
                        RTCSessionDescription(data["sdp"]["sdp"], data["sdp"]["type"])
                    )

                    if stream.video and stream.audio:
                        relayed = stream.relay.subscribe(stream.video)
                        connection.addTrack(relayed)
                        relayed = stream.relay.subscribe(stream.audio)
                        connection.addTrack(relayed)

                    for transceiver in connection.getTransceivers():
                        transceiver.sender.transport._role = "server"  # type: ignore

                    await connection.setLocalDescription(
                        await connection.createAnswer()
                    )

                    for candidate in candidates:
                        await connection.addIceCandidate(candidate)

                    await new_client.tx_queue.put(
                        {
                            "type": "connect",
                            "sdp": {
                                "sdp": connection.localDescription.sdp,
                                "type": connection.localDescription.type,
                            },
                        }
                    )

                    client = new_client

                case "candidate":
                    candidate = candidate_from_sdp(data["candidate"]["candidate"])
                    candidate.sdpMid = data["candidate"]["sdpMid"]
                    candidate.sdpMLineIndex = data["candidate"]["sdpMLineIndex"]
                    if client:
                        await client.connection.addIceCandidate(candidate)
                    else:
                        candidates.append(candidate)

                case _:
                    pass

    async def tx():
        """
        Transmit task responsible for sending messages to the client through its WebSocket.
        """
        while True:
            if client:
                message = await client.tx_queue.get()
                await websocket.send_json(message)
            await sleep(0)

    await gather(create_task(rx()), create_task(tx()))
