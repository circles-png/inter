from asyncio import Event, get_event_loop, set_event_loop
from concurrent.futures import ThreadPoolExecutor
from http.client import CREATED, OK
import time
from aiortc import (
    MediaStreamTrack,
    RTCConfiguration,
    RTCIceCandidate,
    RTCIceServer,
    RTCPeerConnection,
    RTCSessionDescription,
)
import quart
from quart import request
from quart_cors import cors


def ntp_now():
    NTP_DELTA = 2208988800
    return int(time.time() + NTP_DELTA)


class Stream:
    def __init__(self, connection: RTCPeerConnection) -> None:
        self.connection = connection
        self.tracks: list[MediaStreamTrack] = []
        self.clients: list[Client] = []


class Client:
    def __init__(self, connection: RTCPeerConnection) -> None:
        self.connection = connection


def create_app():
    ADDRESS = "127.0.0.1"

    get_event_loop().set_default_executor(ThreadPoolExecutor(8))
    app = quart.Quart(__name__)
    cors(app, allow_origin="*")
    streams: list[Stream] = []
    api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")

    @app.route("/<int:stream_id>")
    async def index(stream_id: int):
        print(stream_id)
        return await quart.render_template("index.html", stream_id=stream_id)

    @api.route("/stream", methods=["POST", "DELETE"])
    async def stream():
        stream = Stream(
            RTCPeerConnection(
                RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
            )
        )
        streams.append(stream)

        @stream.connection.on("connectionstatechange")
        def on_connectionstatechange():
            print(f"tx connectionstatechange", stream.connection.connectionState)

        @stream.connection.on("datachannel")
        def on_datachannel():
            print(f"tx datachannel")

        @stream.connection.on("icecandidate")
        def on_icecandidate(candidate: RTCIceCandidate):
            print(f"tx icecandidate", candidate)

        @stream.connection.on("icecandidateerror")
        def on_icecandidateerror():
            print(f"tx icecandidateerror")

        @stream.connection.on("iceconnectionstatechange")
        def on_iceconnectionstatechange():
            print(f"tx iceconnectionstatechange", stream.connection.iceConnectionState)

        @stream.connection.on("negotiationneeded")
        def on_negotiationneeded():
            print(f"tx negotiationneeded")

        @stream.connection.on("signalingstatechange")
        def on_signalingstatechange():
            print(f"tx signalingstatechange", stream.connection.signalingState)

        @stream.connection.on("track")
        def on_track(t: MediaStreamTrack):
            print(f"tx track")
            stream.tracks.append(t)

        await stream.connection.setRemoteDescription(
            RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
        )
        await stream.connection.setLocalDescription(
            await stream.connection.createAnswer()
        )
        if stream.connection.iceGatheringState != "complete":
            completed = Event()

            @stream.connection.on("icegatheringstatechange")
            def check():
                if stream.connection.iceGatheringState == "complete":
                    completed.set()

            await completed.wait()
        return quart.Response(
            stream.connection.localDescription.sdp,
            status=CREATED,
            content_type="application/sdp",
            headers={
                "Location": f"http://{ADDRESS}:5001/api/v1/stream/{len(streams) - 1}/tx"
            },
        )

    @api.route("/stream/<int:stream_id>/tx", methods=["POST", "PATCH"])
    async def stream_tx(stream_id: int):
        print("TX endpoint called:", stream_id)
        return quart.Response(status=OK)

    @api.route("/stream/<int:stream_id>/tx", methods=["DELETE"])
    async def stream_tx_delete(stream_id: int):
        print("TX endpoint deleted at stream id:", stream_id)
        return quart.Response(status=OK)

    @api.route("/stream/<int:stream_id>/rx", methods=["POST", "PATCH"])
    async def stream_rx(stream_id: int):
        client = Client(
            RTCPeerConnection(
                RTCConfiguration([RTCIceServer(urls=["stun:stun.l.google.com:19302"])])
            )
        )

        @client.connection.on("connectionstatechange")
        def on_connectionstatechange():
            print(f"connectionstatechange", client.connection.connectionState)

        @client.connection.on("datachannel")
        def on_datachannel():
            print(f"datachannel")

        @client.connection.on("icecandidate")
        def on_icecandidate(candidate: RTCIceCandidate):
            print(f"icecandidate", candidate)

        @client.connection.on("icecandidateerror")
        def on_icecandidateerror():
            print(f"icecandidateerror")

        @client.connection.on("iceconnectionstatechange")
        def on_iceconnectionstatechange():
            print(f"iceconnectionstatechange", client.connection.iceConnectionState)

        @client.connection.on("negotiationneeded")
        def on_negotiationneeded():
            print(f"negotiationneeded")

        @client.connection.on("signalingstatechange")
        def on_signalingstatechange():
            print(f"signalingstatechange", client.connection.signalingState)

        @client.connection.on("track")
        def on_track(track: MediaStreamTrack):
            print(f"track")

        streams[stream_id].clients.append(client)
        for track in streams[stream_id].tracks:
            client.connection.addTrack(track)
        await client.connection.setRemoteDescription(
            RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
        )
        await client.connection.setLocalDescription(
            await client.connection.createAnswer()
        )
        if client.connection.iceGatheringState != "complete":
            completed = Event()

            @client.connection.on("icegatheringstatechange")
            def check():
                if client.connection.iceGatheringState == "complete":
                    completed.set()

            await completed.wait()
        return quart.Response(
            client.connection.localDescription.sdp,
            status=CREATED,
            content_type="application/sdp",
        )

    app.register_blueprint(api)
    return app
