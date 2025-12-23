from http.client import UNAUTHORIZED
import quart

from inter.models.user import User


user_self = quart.Blueprint("self", __name__, url_prefix="/self")


@user_self.route("/followers", methods=["GET"])
async def self_followers():
    user = User.from_session()
    if not user:
        return quart.Response(status=UNAUTHORIZED)
    return quart.jsonify(
        [
            {"username": user.username, "displayName": user.display_name}
            for user in user.followers()
        ]
    )


@user_self.route("/following", methods=["GET"])
async def self_following():
    user = User.from_session()
    if not user:
        return quart.Response(status=UNAUTHORIZED)
    return quart.jsonify(
        [
            {"username": user.username, "displayName": user.display_name}
            for user in user.following()
        ]
    )
