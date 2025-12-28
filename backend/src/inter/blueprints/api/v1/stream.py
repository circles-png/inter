from asyncio import Queue, create_task, gather
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
from http.client import CREATED, NOT_FOUND, OK, UNAUTHORIZED
import json
from os import environ
import secrets
from typing import Any
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

from inter.models.client import Client
from inter.common import users
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

    tracks: list[None | RemoteStreamTrack] = [None, None]

    @connection.on("connectionstatechange")
    async def _():
        print(f"tx connectionstatechange", connection.connectionState)
        if connection.connectionState == "connected":
            for queue in user.stream.client_ws_queues:
                await queue.put({"type": "stream_started"})

        if connection.connectionState == "closed":
            for track in user.stream.tracks or []:
                track.stop()
            user.stream.tracks = None
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
        nonlocal tracks
        if track.kind == "video":
            tracks[0] = track
        elif track.kind == "audio":
            tracks[1] = track
        if all(tracks):
            user.stream.tracks = (tracks[0], tracks[1])  # type: ignore
            print("Stream tracks set:", user.stream.tracks)

    await connection.setRemoteDescription(
        RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
    )
    await connection.setLocalDescription(await connection.createAnswer())
    return quart.Response(
        connection.localDescription.sdp,
        status=CREATED,
        content_type="application/sdp",
        headers={"Location": f"{request.host_url}api/v1/stream/{user.username}/tx"},
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
    tx_queue: Queue[dict[str, Any]] = Queue(maxsize=10)
    stream.client_ws_queues.append(tx_queue)
    client = None

    async def rx():
        nonlocal client
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
                        viewer.username if viewer else None,
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
                        new_client.chat = channel

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
                            for client in stream.clients:
                                if client.chat:
                                    client.chat.send(
                                        json.dumps(
                                            {
                                                "type": "message",
                                                "time": int(datetime.now().timestamp()),
                                                "message": data,
                                                "username": viewer.username,
                                                "colour": viewer.colour,
                                            }
                                        )
                                    )

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

                    if stream.tracks:
                        video, audio = stream.tracks
                        connection.addTrack(stream.relay.subscribe(video))
                        connection.addTrack(stream.relay.subscribe(audio))

                    answer = await connection.createAnswer()
                    await connection.setLocalDescription(answer)

                    await tx_queue.put(
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
                    # if stream.connection:
                    #     await stream.connection.addIceCandidate(
                    #         candidate
                    #     )
                    if client:
                        await client.connection.addIceCandidate(candidate)
                case _:
                    pass

    async def tx():
        while True:
            message = await tx_queue.get()
            await websocket.send_json(message)

    await gather(create_task(rx()), create_task(tx()))
