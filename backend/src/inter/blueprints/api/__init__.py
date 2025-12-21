import filetype # type: ignore
import quart

from inter.blueprints.api.v1.auth import auth
from inter.blueprints.api.v1.stream import stream
from inter.common import users

api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")


@api.route("/random", methods=["GET"])
async def random():
    return users.choice().username


@api.route("/avatar/<string:username>", methods=["GET"])
async def avatar(username: str):
    user = users.find_by_username(username)
    if not user:
        return quart.Response(status=404)
    avatar = users.avatar(user)
    if not avatar:
        return quart.Response(status=404)
    return quart.Response(avatar, mimetype=filetype.guess_mime(avatar)) # type: ignore


api.register_blueprint(stream)
api.register_blueprint(auth)
