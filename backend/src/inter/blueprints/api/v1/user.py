from http.client import BAD_REQUEST, NO_CONTENT, NOT_FOUND, OK
from io import BytesIO
import PIL
import PIL.Image
from av import Packet, VideoFrame
import quart
from inter.common import users
from inter.models.user import User
import filetype  # type: ignore
from quart.datastructures import FileStorage

user = quart.Blueprint("user", __name__, url_prefix="/user/<string:username>")


@user.route("/avatar", methods=["GET"])
async def avatar(username: str):
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=404)
    avatar = users.avatar(user)
    if not avatar:
        return quart.Response(status=NO_CONTENT)
    return quart.Response(avatar, mimetype=filetype.guess_mime(avatar))  # type: ignore


@user.route("/", methods=["GET"])
async def get_user(username: str):
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=404)

    return quart.jsonify(
        {
            "displayName": user.display_name,
            "colour": user.colour,
            "following": user.following_count(),
            "followers": user.followers_count(),
        }
    )


@user.route("/follow", methods=["POST"])
async def follow(username: str):
    follower = User.from_session()
    followee = users.find_by_username(username)
    if not followee:
        return quart.Response(status=NOT_FOUND)
    follower.follow(followee)
    return quart.Response(status=OK)


@user.route("/unfollow", methods=["POST"])
async def unfollow(username: str):
    follower = User.from_session()
    followee = users.find_by_username(username)
    if not followee:
        return quart.Response(status=NOT_FOUND)
    follower.unfollow(followee)
    return quart.Response(status=OK)


@user.route("/followers", methods=["GET"])
async def followers(username: str):
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=NOT_FOUND)
    return quart.jsonify(user.followers_count())


@user.route("/following", methods=["GET"])
async def following(username: str):
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=NOT_FOUND)
    return quart.jsonify(user.following_count())


@user.post("/notify")
async def notify(username: str):
    user = User.from_session()
    followee = users.find_by_username(username)
    if not followee:
        return quart.Response(status=NOT_FOUND)
    form = await quart.request.form  # type: ignore
    if not len(form):  # type: ignore
        user.set_notify(followee)
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
    user.set_notify(followee, endpoint, p256dh, auth)
    return quart.Response(status=OK)


@user.get("/notify")
async def get_notify(username: str):
    user = User.from_session()
    followee = users.find_by_username(username)
    if not followee:
        return quart.Response(status=NOT_FOUND)
    setting = user.get_notify(followee)
    return quart.Response("all" if setting else "none")


@user.route("/stream", methods=["GET"])
async def stream(username: str):
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=NOT_FOUND)
    stream = user.stream

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
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=NOT_FOUND)
    stream = user.stream
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
