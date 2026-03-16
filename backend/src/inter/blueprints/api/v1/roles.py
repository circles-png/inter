"""
Endpoints for querying roles.
"""

from http.client import NOT_FOUND
import quart
from sqlalchemy import select

from inter.models.db.role import Roles
from inter.common import get_session


roles = quart.Blueprint("roles", __name__, url_prefix="/roles")


@roles.route("/", methods=["GET"])
async def all_roles():
    """
    Get the list of all roles.
    """
    async with get_session() as session, session.begin():
        roles = await session.scalars(select(Roles))
        return quart.jsonify([{"id": role.id, "name": role.name} for role in roles])

@roles.route("/<int:role_id>/icon", methods=["GET"])
async def get_icon(role_id: int):
    """
    Get the icon for a role.
    """
    async with get_session() as session, session.begin():
        role = await session.get(Roles, role_id)
        if role is None:
            return quart.Response(status=NOT_FOUND)
        return quart.Response(role.icon, mimetype="image/png")
