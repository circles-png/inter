# pyright: reportUnusedFunction=none
from asyncio import Queue, ensure_future, gather
from datetime import datetime
from functools import reduce
from hashlib import sha256
from http.client import BAD_REQUEST, CONFLICT, CREATED, OK
import json
from math import floor
from os import environ
from os.path import exists, join
from random import choice
import secrets
import sqlite3
from typing import Callable, Literal, TypedDict
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
from dotenv import load_dotenv
import quart
from quart import abort, request, websocket
from quart_cors import cors  # type: ignore
import requests


class Stream:
    def __init__(self, connection: RTCPeerConnection) -> None:
        self.connection = connection
        self.tracks: list[MediaStreamTrack] = []
        self.clients: list[Client] = []
        self.relay = aiortc.contrib.media.MediaRelay()
        self.client_ws_queues: list[Queue[dict[str, str]]] = []


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
        self.reload()

    def find_by_token(self, token: str) -> User | None:
        return self.find(lambda user: user.stream_token == token)

    def find_by_username(self, username: str) -> User | None:
        return self.find(lambda user: user.username == username)

    def find(self, condition: Callable[[User], bool]) -> User | None:
        return next((user for user in self.users if condition(user)), None)

    def choice(self) -> User:
        return choice(self.users)

    def available(self, username: str) -> bool:
        return self.find_by_username(username) is None

    def reload(self) -> None:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute("select username, stream_token from users")
            self.users = [
                User(username, stream_token)
                for username, stream_token in cursor.fetchall()
            ]

    def add(self, username: str, password: str) -> None:
        salt = generate_secure_random_string()
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "insert into users (username, stream_token, password_hash, salt, colour) values (?, ?, ?, ?, ?)",
                (
                    username,
                    generate_secure_random_string(),
                    sha256((password + salt).encode()).digest(),
                    salt,
                    1,
                ),
            )
        self.reload()


def create_app():
    load_dotenv()

    app = quart.Quart(__name__, static_folder="../../../frontend/build")
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

    @app.route("/<string:username>/js/index")
    async def index_js(username: str):
        return await quart.render_template("js/index.js", username=username)

    @app.route("/")
    async def root():
        return quart.redirect(f"/{users.choice().username}")

    @app.route("/<path:path>")
    async def static_files(path: str):
        if not app.static_folder:
            return abort(500)
        if exists(join(app.static_folder, path)):
            return await quart.send_from_directory(app.static_folder, path)  # type: ignore
        return await quart.send_file(join(app.static_folder, "index.html"))  # type: ignore

    @api.route("/random", methods=["GET"])
    async def random():
        return users.choice().username

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
        await stream.connection.setLocalDescription(
            await stream.connection.createAnswer()
        )
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
        await client.connection.setLocalDescription(
            await client.connection.createAnswer()
        )
        return quart.Response(
            client.connection.localDescription.sdp,
            status=CREATED,
            content_type="application/sdp",
        )

    @api.route("/auth/available/<string:username>", methods=["GET"])
    async def available(username: str):
        if users.available(username):
            return quart.Response(status=OK)
        else:
            return quart.Response(status=CONFLICT)

    @api.route("/auth/signup", methods=["POST"])
    async def signup():
        data = await request.get_json()
        username: str = data.get("username")
        password: str = data.get("password")
        reenter: str = data.get("reenter")
        if not username or not password or not reenter:
            return quart.Response("Enter a username and password.", status=BAD_REQUEST)
        if password != reenter:
            return quart.Response("Ensure passwords match.", status=BAD_REQUEST)
        if not users.available(username):
            return quart.Response(f"'{username}' is not available.", status=CONFLICT)
        users.add(username, password)
        session = Session()
        response = quart.Response(status=CREATED)
        response.set_cookie("session_token", session.token, max_age=86400, secure=True, samesite="Lax")
        return response

    api.register_blueprint(stream)
    app.register_blueprint(api)
    return app


class Session:
    def __init__(self) -> None:
        self.id = generate_secure_random_string()
        secret = generate_secure_random_string()
        self.secret_hash = sha256(secret.encode()).digest()
        self.created_at = datetime.now()
        self.token = f"{self.id}.{secret}"
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "insert into sessions (id, secret_hash, created_at) values (?, ?, ?)",
                (self.id, self.secret_hash, floor(self.created_at.timestamp())),
            )

    @staticmethod
    def validate_token(token: str) -> "Session | None":
        parts = token.split(".")
        if len(parts) != 2:
            return None
        session_id, secret = parts
        session = Session.get(session_id)
        if not session:
            return None
        secret_hash = sha256(secret.encode()).digest()
        if not secrets.compare_digest(secret_hash, session.secret_hash):
            return None
        return session

    @staticmethod
    def get(session_id: str) -> "Session | None":
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select id, secret_hash, created_at from sessions where id = ?",
                (session_id,),
            )
            session_id, secret_hash, created_at = cursor.fetchone()
        created_at = datetime.fromtimestamp(created_at)
        if (datetime.now() - created_at).total_seconds() > 60 * 60 * 24:
            Session.delete(session_id)
            return None
        session = Session.__new__(Session)
        session.id = session_id
        session.secret_hash = secret_hash
        session.created_at = created_at
        return session

    @staticmethod
    def delete(session_id: str) -> None:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "delete from sessions where id = ?",
                (session_id,),
            )


def generate_secure_random_string() -> str:
    return secrets.token_urlsafe(32)


class TextFragment(TypedDict):
    type: Literal["text"]
    text: str


class EmoteFragment(TypedDict):
    type: Literal["emote"]
    url: str
    name: str


class Message(TypedDict):
    time: str
    message: list["Fragment"]
    user: "User"


type Fragment = TextFragment | EmoteFragment
