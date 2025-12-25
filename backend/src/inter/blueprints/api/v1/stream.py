from asyncio import Queue, create_task, gather
from datetime import datetime
from http.client import CREATED, OK
import json
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
import aiortc.codecs
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

    @connection.on("connectionstatechange")
    async def _():
        print(f"tx connectionstatechange", connection.connectionState)
        if connection.connectionState == "connected":
            for queue in user.stream.client_ws_queues:
                await queue.put({"type": "stream_started"})

        if connection.connectionState == "closed":
            for track in user.stream.tracks:
                track.stop()
            user.stream.tracks = []
            user.stream.relay = aiortc.contrib.media.MediaRelay()
            for client in user.stream.clients:
                for track in client.tracks:
                    track.stop()
            await connection.close()
            user.stream.connection = None

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
    def _(t: MediaStreamTrack):
        print(f"tx track")
        user.stream.tracks.append(t)

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


@stream.websocket("/<string:username>/ws")
async def ws(username: str):
    streamer = users.find_by_username(username)
    if not streamer:
        return quart.Response(status=404)
    stream = streamer.stream
    queue: Queue[dict[str, str]] = Queue(maxsize=10)
    stream.client_ws_queues.append(queue)

    async def rx():
        while True:
            data = await websocket.receive_json()
            match data["type"]:
                case "candidate":
                    if stream.connection:
                        await stream.connection.addIceCandidate(
                            RTCIceCandidate(**data["candidate"])
                        )
                    for client in stream.clients:
                        await client.connection.addIceCandidate(
                            RTCIceCandidate(**data["candidate"])
                        )
                case _:
                    pass

    async def tx():
        while True:
            message = await queue.get()
            await websocket.send_json(message)

    await gather(create_task(rx()), create_task(tx()))


@stream.route("/<string:username>/tx", methods=["POST", "PATCH"])
async def stream_tx(username: str):
    print("TX endpoint called:", username)
    return quart.Response(status=OK)


@stream.route("/<string:username>/tx", methods=["DELETE"])
async def stream_tx_delete(username: str):
    print("TX endpoint deleted at username:", username)
    return quart.Response(status=OK)


@stream.route("/<string:username>/rx", methods=["POST", "PATCH"])
async def _(username: str):
    streamer = users.find_by_username(username)
    if not streamer:
        return abort(404)
    stream = streamer.stream
    viewer = User.from_session() if "session_token" in request.cookies else None
    client = Client(
        RTCPeerConnection(
            RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
        )
    )

    @client.connection.on("connectionstatechange")
    async def _():
        print(f"connectionstatechange", client.connection.connectionState)
        if client.connection.connectionState == "closed":
            await client.connection.close()
            if client.chat:
                client.chat.close()
            for track in client.tracks:
                track.stop()
            stream.clients.remove(client)

    @client.connection.on("datachannel")
    def _(channel: RTCDataChannel):
        print(f"datachannel", channel)
        client.chat = channel

        channel.send(
            json.dumps(
                {
                    "time": int(datetime.now().timestamp()),
                    "message": "Connected to chat! Hola",
                    "username": "[System]",
                    "colour": 0,
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
                                "time": int(datetime.now().timestamp()),
                                "message": data,
                                "username": viewer.username,
                                "colour": viewer.colour,
                            }
                        )
                    )

    @client.connection.on("icecandidate")
    def _(candidate: RTCIceCandidate):
        print(f"icecandidate", candidate)

    @client.connection.on("icecandidateerror")
    def _():
        print(f"icecandidateerror")

    @client.connection.on("iceconnectionstatechange")
    def _():
        print(f"iceconnectionstatechange", client.connection.iceConnectionState)

    @client.connection.on("negotiationneeded")
    def _():
        print(f"negotiationneeded")

    @client.connection.on("signalingstatechange")
    def _():
        print(f"signalingstatechange", client.connection.signalingState)

    @client.connection.on("track")
    def _(track: MediaStreamTrack):
        print(f"track")

    stream.clients.append(client)
    for track in stream.tracks:
        new_track = stream.relay.subscribe(track)
        client.connection.addTransceiver(new_track, "sendonly")
        client.tracks.append(new_track)
    for transceiver in client.connection.getTransceivers():
        if transceiver.kind == "video":
            transceiver.setCodecPreferences(
                [
                    codec
                    for codec in aiortc.codecs.get_capabilities("video").codecs
                    if codec.name in ["H264", "rtx", "red", "ulpfec"]
                ]
            )
        if transceiver.kind == "audio":
            transceiver.setCodecPreferences(
                [
                    codec
                    for codec in aiortc.codecs.get_capabilities("audio").codecs
                    if codec.name == "PCMU"
                ]
            )

    await client.connection.setRemoteDescription(
        RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
    )
    answer = await client.connection.createAnswer()
    await client.connection.setLocalDescription(answer)
    return quart.Response(
        answer.sdp,
        status=CREATED,
        content_type="application/sdp",
    )
