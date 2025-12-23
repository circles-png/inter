from http.client import NOT_FOUND, OK, UNAUTHORIZED
import quart
from inter.common import users
from inter.models.user import User
import filetype  # type: ignore

user = quart.Blueprint("user", __name__, url_prefix="/user/<string:username>")


@user.route("/avatar", methods=["GET"])
async def avatar(username: str):
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=404)
    avatar = users.avatar(user)
    if not avatar:
        return quart.Response(status=404)
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
        }
    )


@user.route("/follow", methods=["POST"])
async def follow(username: str):
    follower = User.from_session()
    if not follower:
        return quart.Response(status=UNAUTHORIZED)
    followee = users.find_by_username(username)
    if not followee:
        return quart.Response(status=NOT_FOUND)
    follower.follow(followee)
    return quart.Response(status=OK)


@user.route("/unfollow", methods=["POST"])
async def unfollow(username: str):
    follower = User.from_session()
    if not follower:
        return quart.Response(status=UNAUTHORIZED)
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
