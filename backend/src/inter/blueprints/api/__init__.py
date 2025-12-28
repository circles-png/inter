import quart

from inter.blueprints.api.v1.auth import auth
from inter.blueprints.api.v1.stream import stream
from inter.blueprints.api.v1.user import user
from inter.blueprints.api.v1.user_self import user_self
from inter.common import users, emotes

api = quart.Blueprint("api", __name__, url_prefix="/api/v1/")


@api.route("/random", methods=["GET"])
async def random():
    return users.choice().username


@api.route("/emotes", methods=["GET"])
async def _():
    return quart.jsonify({name: url for name, url in emotes.items()})

api.register_blueprint(stream)
api.register_blueprint(auth)
api.register_blueprint(user)
api.register_blueprint(user_self)
