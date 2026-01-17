from http.client import BAD_REQUEST, NO_CONTENT, NOT_FOUND, OK
from io import BytesIO
import PIL
import PIL.Image
from av import Packet, VideoFrame
import quart
from inter.models.db.user import User
import filetype  # type: ignore
from quart.datastructures import FileStorage
from inter.common import get_session
from inter.blueprints.api.v1.stream import streams

user = quart.Blueprint("user", __name__, url_prefix="/user/<string:username>")


@user.route("/avatar", methods=["GET"])
async def avatar(username: str):
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=404)
        avatar = user.avatar
        if not avatar:
            return quart.Response(status=NO_CONTENT)
        return quart.Response(avatar, mimetype=filetype.guess_mime(avatar))  # type: ignore


@user.route("/", methods=["GET"])
async def get_user(username: str):
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=404)

        return quart.jsonify(
            {
                "displayName": user.display_name,
                "colour": user.colour,
                "following": await user.following_count(session),
                "followers": await user.followers_count(session),
            }
        )


@user.route("/follow", methods=["POST"])
async def follow(username: str):
    async with get_session() as session, session.begin():
        followee = await User.find_by_username(session, username)
        if not followee:
            return quart.Response(status=NOT_FOUND)
        follower = await User.from_session(session)
        await follower.follow(followee, session)
        return quart.Response(status=OK)


@user.route("/unfollow", methods=["POST"])
async def unfollow(username: str):
    async with get_session() as session, session.begin():
        follower = await User.from_session(session)
        followee = await User.find_by_username(session, username)
        if not followee:
            return quart.Response(status=NOT_FOUND)
        await follower.unfollow(followee, session)
        return quart.Response(status=OK)


@user.route("/followers", methods=["GET"])
async def followers(username: str):
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        return quart.jsonify(await user.followers_count(session))


@user.route("/following", methods=["GET"])
async def following(username: str):
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        return quart.jsonify(await user.following_count(session))

@user.post("/notify")
async def notify(username: str):
    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        followee = await User.find_by_username(session, username)
        if not followee:
            return quart.Response(status=NOT_FOUND)
        form = await quart.request.form  # type: ignore
        if not len(form):  # type: ignore
            await user.set_notify(followee, session)
            return quart.Response(status=OK)
        endpoint = form.get("endpoint")  # type: ignore
        if not endpoint or not isinstance(endpoint, str):
            return quart.Response(status=BAD_REQUEST)
        files = await quart.request.files  # type: ignore
        p256dh = files.get("p256dh")  # type: ignore
        if not p256dh or not isinstance(p256dh, FileStorage):
            return quart.Response(status=BAD_REQUEST)
        auth = files.get("auth")  # type: ignore
        if not auth or not isinstance(auth, FileStorage):
            return quart.Response(status=BAD_REQUEST)
        p256dh = p256dh.stream.read()
        auth = auth.stream.read()
        await user.set_notify(followee, session, endpoint, p256dh, auth)
        return quart.Response(status=OK)


@user.get("/notify")
async def get_notify(username: str):
    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        followee = await User.find_by_username(session, username)
        if not followee:
            return quart.Response(status=NOT_FOUND)
        setting = await user.get_notify(followee, session)
        return quart.Response("all" if setting else "none")


@user.route("/stream", methods=["GET"])
async def stream(username: str):
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        stream = streams[user.id]

        return quart.jsonify(
            {
                "title": stream.title,
                "game": stream.game,
                "start": stream.start,
                "viewers": len(stream.clients) if stream.connection else None,
            }
        )


@user.route("/stream/preview", methods=["GET"])
async def stream_preview(username: str):
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        stream = streams[user.id]
        if not stream:
            return quart.Response(status=NOT_FOUND)
        track = stream.video
        if not track:
            return quart.Response(status=NOT_FOUND)
        new_track = stream.relay.subscribe(track)
        frame = await new_track.recv()
        new_track.stop()

        async def send_video_frame(frame: VideoFrame) -> quart.Response:
            image: PIL.Image.Image = frame.to_image()  # type: ignore
            io = BytesIO()
            image.save(io, "PNG")  # type: ignore
            io.seek(0)
            return await quart.send_file(io, mimetype="image/png")  # type: ignore

        if isinstance(frame, VideoFrame):
            return await send_video_frame(frame)
        if isinstance(frame, Packet):
            frame = next(
                (frame for frame in frame.decode() if isinstance(frame, VideoFrame)), None
            )
            if not frame:
                return quart.Response(status=NOT_FOUND)
            return await send_video_frame(frame)
        return quart.Response(status=NOT_FOUND)
