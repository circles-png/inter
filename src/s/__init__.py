from datetime import datetime
from http.client import CREATED, OK
import json
from os import environ
from random import choice
from sqlite3 import connect
from typing import Callable
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
import aiortc.contrib
import aiortc.contrib.media
import quart
from quart import abort, request, websocket
from quart_cors import cors
import requests


class Stream:
    def __init__(self, connection: RTCPeerConnection) -> None:
        self.connection = connection
        self.tracks: list[MediaStreamTrack] = []
        self.clients: list[Client] = []
        self.relay = aiortc.contrib.media.MediaRelay()


class Client:
    def __init__(self, connection: RTCPeerConnection) -> None:
        self.connection = connection
        self.chat: RTCDataChannel | None = None


class User:
    def __init__(
        self,
        username: str,
        stream_token: str | None,
    ) -> None:
        self.username = username
        self.stream_token = stream_token
        self.stream: Stream | None = None


class Users:
    def __init__(self) -> None:
        with connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute("select username, stream_token from users")
            self.users: list[User] = [
                User(username, stream_token)
                for username, stream_token in cursor.fetchall()
            ]

    def find_by_token(self, token: str) -> User | None:
        return self.find(lambda user: user.stream_token == token)

    def find_by_username(self, username: str) -> User | None:
        return self.find(lambda user: user.username == username)

    def find(self, condition: Callable[[User], bool]) -> User | None:
        return next((user for user in self.users if condition(user)), None)

    def choice(self) -> User:
        return choice(self.users)


def create_app():
    app = quart.Quart(__name__)
    cors(app, allow_origin="*")
    users = Users()

    emotes: dict[str, str] = {
        emote[
            "name"
        ]: f"http:{emote['data']['host']['url']}/{emote['data']['host']['files'][1]['name']}"
        for emote in [
            *requests.get(
                f"https://7tv.io/v3/emote-sets/{environ["EMOTE_SET"]}"
            ).json()["emotes"],
            *requests.get(f"https://7tv.io/v3/emote-sets/global").json()["emotes"],
        ]
    }

    api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")

    @app.route("/")
    async def home():
        return quart.redirect(f"/{users.choice().username}")

    @app.route("/<string:username>/js/index")
    async def index_js(username: str):
        return await quart.render_template("js/index.js", username=username)

    @app.route("/<string:username>")
    async def watch(username: str):
        return await quart.render_template("index.html", username=username)

    @api.route("/stream", methods=["POST", "DELETE"])
    async def stream():
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
        async def on_connectionstatechange():
            print(f"tx connectionstatechange", stream.connection.connectionState)
            if stream.connection.connectionState == "closed":
                await stream.connection.close()
                for client in stream.clients:
                    await client.connection.close()

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
        return quart.Response(
            stream.connection.localDescription.sdp,
            status=CREATED,
            content_type="application/sdp",
            headers={"Location": f"{request.host_url}api/v1/stream/{user.username}/tx"},
        )

    @api.websocket("/stream/<string:username>/ws")
    async def ws(username: str):
        data = await websocket.receive_json()
        match data["type"]:
            case "candidate":
                user = users.find_by_username(username)
                if not user:
                    return await websocket.close(code=4004)
                stream = user.stream
                if stream:
                    await stream.connection.addIceCandidate(
                        RTCIceCandidate(**data["candidate"])
                    )
            case _:
                pass

    @api.route("/stream/<string:username>/tx", methods=["POST", "PATCH"])
    async def stream_tx(username: str):
        print("TX endpoint called:", username)
        return quart.Response(status=OK)

    @api.route("/stream/<string:username>/tx", methods=["DELETE"])
    async def stream_tx_delete(username: str):
        print("TX endpoint deleted at username:", username)
        return quart.Response(status=OK)

    @api.route("/stream/<string:username>/rx", methods=["POST", "PATCH"])
    async def stream_rx(username: str):
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
        async def on_connectionstatechange():
            print(f"connectionstatechange", client.connection.connectionState)
            if client.connection.connectionState == "closed":
                await client.connection.close()
                if client.chat:
                    client.chat.close()
                stream.clients.remove(client)

        @client.connection.on("datachannel")
        def on_datachannel(channel: RTCDataChannel):
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
            def on_message(data: str):
                print("message", data)
                for client in stream.clients:
                    if client.chat:
                        message = [
                            (
                                {"type": "emote", "url": emotes.get(part), "name": part}
                                if emotes.get(part)
                                else {"type": "text", "text": part + " "}
                            )
                            for part in data.split(" ")
                        ]
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

        stream.clients.append(client)
        for track in stream.tracks:
            client.connection.addTrack(stream.relay.subscribe(track))
        await client.connection.setRemoteDescription(
            RTCSessionDescription(sdp=(await request.data).decode(), type="offer")
        )
        await client.connection.setLocalDescription(
            await client.connection.createAnswer()
        )
        return quart.Response(
            client.connection.localDescription.sdp,
            status=CREATED,
            content_type="application/sdp",
        )

    app.register_blueprint(api)
    return app
