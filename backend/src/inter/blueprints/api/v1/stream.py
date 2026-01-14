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

from inter.models.client import Client
from inter.common import users
from inter.models.poll import Option, Poll
from inter.models.user import User


stream = quart.Blueprint("stream", __name__, url_prefix="/stream/")


@stream.route("/", methods=["POST", "DELETE"])
async def start_stream():
    token = request.headers.get("Authorization")
    if not token:
        return abort(401)
    user = users.find_by_token(token[len("Bearer ") :])
    if not user:
        return abort(401)
    connection = RTCPeerConnection(
        RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
    )
    user.stream.connection = connection
    user.stream.start = datetime.now(timezone.utc).timestamp()
    for follower in user.get_notified():
        notify = follower.get_notify(user)
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
            follower.set_notify(user, None)

    @connection.on("connectionstatechange")
    async def _():
        print(f"tx connectionstatechange", connection.connectionState)

        if connection.connectionState == "closed":
            if user.stream.video:
                user.stream.video.stop()
            if user.stream.audio:
                user.stream.audio.stop()
            user.stream.video = None
            user.stream.audio = None
            user.stream.relay = aiortc.contrib.media.MediaRelay()
            for client in user.stream.clients:
                for track in client.tracks:
                    track.stop()
            await connection.close()
            user.stream.connection = None
            user.stream.start = None
            user.stream.clients = []

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
    def _(track: RemoteStreamTrack):
        print(f"tx track", track)
        if track.kind == "video":
            user.stream.video = track
        elif track.kind == "audio":
            user.stream.audio = track

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


@stream.route("/<string:username>/tx", methods=["POST", "PATCH"])
async def stream_tx(username: str):
    print("TX endpoint called:", username)
    return quart.Response(status=OK)


@stream.route("/<string:username>/tx", methods=["DELETE"])
async def stream_tx_delete(username: str):
    print("TX endpoint deleted at username:", username)
    return quart.Response(status=OK)


@stream.route("/auth", methods=["GET"])
async def ws_auth():
    if "session_token" not in request.cookies:
        return quart.Response(status=UNAUTHORIZED)
    user = User.from_session()
    data = (
        f"{user.username}\n{int((datetime.now() + timedelta(seconds=10)).timestamp())}"
    )
    signature = hmac.new(
        environ["STREAM_WS_AUTH_KEY"].encode(),
        data.encode(),
        sha256,
    ).hexdigest()
    return quart.Response(f"{data}\n{signature}")


@stream.websocket("/<string:username>/ws")
async def ws(username: str):
    streamer = users.find_by_username(username)
    if not streamer:
        return quart.Response(status=NOT_FOUND)
    stream = streamer.stream
    client = None
    candidates: list[RTCIceCandidate] = []

    async def rx():
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
                            viewer = users.find_by_username(username)
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
                        viewer.id if viewer else None,
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

                    @connection.on("datachannel")
                    def _(channel: RTCDataChannel):
                        print(f"datachannel", channel)
                        match channel.label:
                            case "chat":
                                new_client.chat = channel
                                for message in [*stream.chat]:
                                    channel.send(message)
                                channel.send(
                                    json.dumps(
                                        {
                                            "type": "system",
                                            "message": "Connected to chat! Hola",
                                        }
                                    )
                                )

                                @channel.on("message")
                                def _(data: str):
                                    if not viewer:
                                        return
                                    print("message", data)
                                    text, replying = itemgetter("text", "replying")(
                                        json.loads(data)
                                    )
                                    message = json.dumps(
                                        {
                                            "type": "message",
                                            "time": int(datetime.now().timestamp()),
                                            "message": text,
                                            "replying": replying,
                                            "username": viewer.username,
                                            "colour": viewer.colour,
                                            "id": urandom(16).hex(),
                                        }
                                    )
                                    stream.chat.append(message)
                                    for client in stream.clients:
                                        if client.chat:
                                            client.chat.send(message)

                            case "poll":
                                new_client.poll = channel

                                def update(client: Client = new_client):
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
                                                or client.viewer == streamer.id
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
                                                    update_poll(poll)
                                                    for poll in stream.polls
                                                ],
                                            }
                                        )
                                    )

                                def update_all():
                                    for client in stream.clients:
                                        update(client)

                                update()

                                @channel.on("message")
                                def _(data: str):
                                    class Update(TypedDict):
                                        type: Literal["update"]

                                    class Start(TypedDict):
                                        type: Literal["start"]
                                        question: str
                                        options: list[str]
                                        duration: float

                                    class Vote(TypedDict):
                                        type: Literal["vote"]
                                        poll: str
                                        option: int

                                    parsed: Update | Vote | Start = json.loads(data)
                                    match parsed["type"]:
                                        case "update":
                                            update()
                                        case "start":
                                            # TODO include moderators
                                            if (
                                                not viewer
                                                or viewer.username != streamer.username
                                            ):
                                                return
                                            poll = Poll(
                                                parsed["question"],
                                                [
                                                    Option(text)
                                                    for text in parsed["options"]
                                                ],
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
                                            if not poll:
                                                return
                                            option = (
                                                poll.options[parsed["option"]]
                                                if 0
                                                <= parsed["option"]
                                                < len(poll.options)
                                                else None
                                            )
                                            if not option:
                                                return
                                            option.users.add(viewer.id)
                                            update_all()
                                        case _:
                                            pass

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

                case "tracks":
                    if client:
                        connection = client.connection
                        for track in (stream.audio, stream.video):
                            if not track:
                                continue
                            relayed = stream.relay.subscribe(track)
                            connection.addTrack(relayed)
                        if stream.audio or stream.video:
                            offer = await connection.createOffer()
                            await connection.setLocalDescription(offer)
                            await client.tx_queue.put(
                                {
                                    "type": "renegotiate",
                                    "sdp": {
                                        "sdp": connection.localDescription.sdp,
                                        "type": connection.localDescription.type,
                                    },
                                }
                            )

                case "renegotiate":
                    if client:
                        await client.connection.setRemoteDescription(
                            RTCSessionDescription(
                                data["sdp"]["sdp"], data["sdp"]["type"]
                            )
                        )

                case _:
                    pass

    async def tx():
        while True:
            if client:
                message = await client.tx_queue.get()
                await websocket.send_json(message)
            await sleep(0)

    await gather(create_task(rx()), create_task(tx()))
