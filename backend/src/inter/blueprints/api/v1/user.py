"""
Endpoints for managing and querying users.
"""

from http.client import (
    BAD_REQUEST,
    CONFLICT,
    FORBIDDEN,
    NO_CONTENT,
    NOT_FOUND,
    OK,
)
from io import BytesIO
import json
import PIL
import PIL.Image
from av import Packet, VideoFrame
import quart
from sqlalchemy import delete, select
from inter.models.db.role import UsersRoles
from inter.models.db.user import User
import filetype  # type: ignore
from quart.datastructures import FileStorage
from inter.common import MODERATOR_ROLE_ID, get_session
from inter.blueprints.api.v1.stream import streams

user = quart.Blueprint("user", __name__, url_prefix="/user/<string:username>")


@user.route("/avatar", methods=["GET"])
async def avatar(username: str):
    """
    Get the avatar for the user with the given username. Return Not Found if the user does not exist
    or No Content if the user does not have an avatar.
    """
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        avatar = user.avatar
        if not avatar:
            return quart.Response(status=NO_CONTENT)
        return quart.Response(avatar, mimetype=filetype.guess_mime(avatar))  # type: ignore


@user.route("/", methods=["GET"])
async def get_user(username: str):
    """
    Get information about the user with the given username.
    """
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)

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
    """
    Follow the user with the given username.
    """
    async with get_session() as session, session.begin():
        followee = await User.find_by_username(session, username)
        if not followee:
            return quart.Response(status=NOT_FOUND)
        follower = await User.from_session(session)
        await follower.follow(followee, session)
        return quart.Response(status=OK)


@user.route("/unfollow", methods=["POST"])
async def unfollow(username: str):
    """
    Unfollow the user with the given username.
    """
    async with get_session() as session, session.begin():
        follower = await User.from_session(session)
        followee = await User.find_by_username(session, username)
        if not followee:
            return quart.Response(status=NOT_FOUND)
        await follower.unfollow(followee, session)
        return quart.Response(status=OK)


@user.route("/followers", methods=["GET"])
async def followers(username: str):
    """
    Get the number of followers for the user with the given username.
    """
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        return quart.jsonify(await user.followers_count(session))


@user.route("/following", methods=["GET"])
async def following(username: str):
    """
    Get the number of users that the user with the given username is following.
    """
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        return quart.jsonify(await user.following_count(session))


@user.post("/notify")
async def notify(username: str):
    """
    Set the currently authenticated user's notification settings for the user with the given
    username. Uses Web Push and VAPID to send notifications and authenticate the client.
    """
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
    """
    Get the currently authenticated user's notification settings for the user with the given
    username.
    """
    async with get_session() as session, session.begin():
        user = await User.from_session(session)
        followee = await User.find_by_username(session, username)
        if not followee:
            return quart.Response(status=NOT_FOUND)
        setting = await user.get_notify(followee, session)
        return quart.Response("all" if setting else "none")


@user.route("/stream", methods=["GET"])
async def stream(username: str):
    """
    Get the stream information for the user with the given username.
    """
    async with get_session() as session, session.begin():
        user = await User.find_by_username(session, username)
        if not user:
            return quart.Response(status=NOT_FOUND)
        stream = streams[user.id]
        return quart.jsonify(
            {
                "title": user.stream_title,
                "game": user.stream_game,
                "start": stream.start,
                "viewers": len(stream.clients) if stream.connection else None,
            }
        )


@user.route("/stream/preview", methods=["GET"])
async def stream_preview(username: str):
    """
    Get an image preview of the stream for the user with the given username.
    """
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
                (frame for frame in frame.decode() if isinstance(frame, VideoFrame)),
                None,
            )
            if not frame:
                return quart.Response(status=NOT_FOUND)
            return await send_video_frame(frame)
        return quart.Response(status=NOT_FOUND)


@user.route("/moderate", methods=["POST"])
async def moderate(username: str):
    """
    Moderate the user with the given username.
    """
    async with get_session() as session, session.begin():
        subject = await User.from_session(session)
        target = await User.find_by_username(session, username)
        if not target:
            return quart.Response(status=NOT_FOUND)
        if subject.id == target.id:
            return quart.Response(
                "Ensure you are not moderating yourself.", status=CONFLICT
            )
        data = await quart.request.get_json()
        client = next(
            (
                client
                for client in streams[subject.id].clients
                if client.viewer == target.id
            ),
            None,
        )
        if "duration" not in data:
            await subject.unmoderate(target, session)
            if client and client.chat:
                client.chat.send(
                    json.dumps(
                        {
                            "type": "system",
                            "message": "You have been pardoned.",
                        }
                    )
                )
            return quart.Response(status=OK)
        await subject.moderate(target, data["duration"], session)
        if client and client.chat:
            client.chat.send(
                json.dumps(
                    {
                        "type": "system",
                        "message": (
                            "You have been banned."
                            if data["duration"] is None
                            else f"You have been timed out for {data['duration']} seconds."
                        ),
                    }
                )
            )
        return quart.Response(status=OK)


@user.route("/roles/<string:subject>", methods=["GET"])
async def get_roles(username: str, subject: str):
    """
    Get the roles that the target with the given username has, with respect to the given subject.
    """
    async with get_session() as session, session.begin():
        target = await User.find_by_username(session, username)
        if not target:
            return quart.Response(status=NOT_FOUND)
        subject_user = await User.find_by_username(session, subject)
        if not subject_user:
            return quart.Response(status=NOT_FOUND)
        return quart.jsonify(
            [
                *await session.scalars(
                    select(UsersRoles.role).where(
                        UsersRoles.target == target.id,
                        UsersRoles.subject == subject_user.id,
                    )
                )
            ]
        )


@user.route("/roles/<string:subject>", methods=["POST"])
async def set_roles(username: str, subject: str):
    """
    Set the roles that the target with the given username has, with respect to the given subject.
    """
    async with get_session() as session, session.begin():
        actor = await User.from_session(session)
        subject_user = await User.find_by_username(session, subject)

        if not subject_user:
            return quart.Response(status=NOT_FOUND)
        if (
            actor.id != subject_user.id
            and not (
                await session.execute(
                    select(UsersRoles).where(
                        UsersRoles.subject == actor.id,
                        UsersRoles.target == subject_user.id,
                        UsersRoles.role == MODERATOR_ROLE_ID,
                    )
                )
            ).one_or_none()
        ):
            return quart.Response(status=FORBIDDEN)
        target = await User.find_by_username(session, username)
        if not target:
            return quart.Response(status=NOT_FOUND)
        data = await quart.request.get_json()
        if not isinstance(data, list) or not all(
            isinstance(role, int) for role in data  # type: ignore
        ):
            return quart.Response(status=BAD_REQUEST)
        await session.execute(
            delete(UsersRoles).where(
                UsersRoles.target == target.id, UsersRoles.subject == subject_user.id
            )
        )
        session.add_all(
            UsersRoles(subject=subject_user.id, target=target.id, role=role) for role in data  # type: ignore
        )
        for client in streams[subject_user.id].clients:
            await client.tx_queue.put({"type": "roles"})
    return quart.Response(status=OK)
