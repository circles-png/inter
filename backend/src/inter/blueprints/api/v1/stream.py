from asyncio import Queue, ensure_future, gather
from datetime import datetime
from functools import reduce
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
from quart import abort, request, websocket
import quart

from inter.models.client import Client
from inter.models.message import EmoteFragment, Fragment
from inter.models.stream import Stream
from inter.common import users, emotes

stream = quart.Blueprint("stream", __name__, url_prefix="/stream/")


@stream.route("/", methods=["POST", "DELETE"])
async def start_stream():
    token = request.headers.get("Authorization")
    if not token:
        return abort(401)
    stream = Stream(
        RTCPeerConnection(
            RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
        ),
    )
    user = users.find_by_token(token[7:])
    if not user:
        return abort(401)
    user.stream = stream

    @stream.connection.on("connectionstatechange")
    async def _():
        print(f"tx connectionstatechange", stream.connection.connectionState)
        for queue in stream.client_ws_queues:
            await queue.put({"type": "stream_started"})

    @stream.connection.on("datachannel")
    def _():
        print(f"tx datachannel")

    @stream.connection.on("icecandidate")
    def _(candidate: RTCIceCandidate):
        print(f"tx icecandidate", candidate)

    @stream.connection.on("icecandidateerror")
    def _():
        print(f"tx icecandidateerror")

    @stream.connection.on("iceconnectionstatechange")
    def _():
        print(f"tx iceconnectionstatechange", stream.connection.iceConnectionState)

    @stream.connection.on("negotiationneeded")
    def _():
        print(f"tx negotiationneeded")

    @stream.connection.on("signalingstatechange")
    def _():
        print(f"tx signalingstatechange", stream.connection.signalingState)

    @stream.connection.on("track")
    def _(t: MediaStreamTrack):
        print(f"tx track")
        stream.tracks.append(t)

    await stream.connection.setRemoteDescription(
        RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
    )
    await stream.connection.setLocalDescription(await stream.connection.createAnswer())
    return quart.Response(
        stream.connection.localDescription.sdp,
        status=CREATED,
        content_type="application/sdp",
        headers={"Location": f"{request.host_url}api/v1/stream/{user.username}/tx"},
    )


@stream.websocket("/<string:username>/ws")
async def ws(username: str):
    user = users.find_by_username(username)
    if not user:
        return await websocket.close(code=4004)
    stream = user.stream
    queue: Queue[dict[str, str]] = Queue(maxsize=10)
    if stream:
        stream.client_ws_queues.append(queue)

    async def rx():
        while True:
            data = await websocket.receive_json()
            print(data)
            match data["type"]:
                case "candidate":
                    if stream:
                        await stream.connection.addIceCandidate(
                            RTCIceCandidate(**data["candidate"])
                        )
                case _:
                    pass

    async def tx():
        while True:
            message = await queue.get()
            print(message)
            await websocket.send_json(message)

    await gather(ensure_future(rx()), ensure_future(tx()))


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
    user = users.find_by_username(username)
    if not user:
        return abort(404)
    if not user.stream:
        return abort(404)
    stream = user.stream
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
            stream.clients.remove(client)

    @client.connection.on("datachannel")
    def _(channel: RTCDataChannel):
        print(f"datachannel", channel)
        client.chat = channel
        channel.send(
            json.dumps(
                {
                    "type": "emotes",
                    "emotes": [
                        {"name": name, "url": url} for name, url in emotes.items()
                    ],
                }
            )
        )

        @channel.on("message")
        def _(data: str):
            print("message", data)

            def combine(message: list[Fragment], part: str) -> list[Fragment]:
                emote = emotes.get(part)
                if emote:
                    fragment: EmoteFragment = {
                        "type": "emote",
                        "url": emote,
                        "name": part,
                    }
                    return message + [
                        fragment,
                    ]
                else:
                    return (
                        message[:-1]
                        + [
                            {
                                "type": "text",
                                "text": message[-1]["text"] + part + " ",
                            }
                        ]
                        if message[-1]["type"] == "text"
                        else message + [{"type": "text", "text": part + " "}]
                    )

            message = reduce(combine, data.split(" "), [])
            for client in stream.clients:
                if client.chat:
                    client.chat.send(
                        json.dumps(
                            {
                                "type": "message",
                                "time": datetime.now().strftime("%I:%M:%S"),
                                "message": message,
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
        track = stream.relay.subscribe(track)
        client.connection.addTrack(track)
    await client.connection.setRemoteDescription(
        RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
    )
    await client.connection.setLocalDescription(await client.connection.createAnswer())
    return quart.Response(
        client.connection.localDescription.sdp,
        status=CREATED,
        content_type="application/sdp",
    )
