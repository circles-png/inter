from flask import abort
import quart

from inter.blueprints.api.v1.auth import auth
from inter.blueprints.api.v1.stream import stream
from inter.common import users
from inter.utils import generate_secure_random_string

api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")


@api.route("/random", methods=["GET"])
async def random():
    return users.choice().username


@api.route("/avatar/<string:username>", methods=["GET"])
async def avatar(username: str):
    user = users.find_by_username(username)
    if not user:
        return abort(404)
    return quart.Response(users.avatar(user))


@api.route("stream-token", methods=["GET"])
async def get_stream_token():
    return generate_secure_random_string()


api.register_blueprint(stream)
api.register_blueprint(auth)
