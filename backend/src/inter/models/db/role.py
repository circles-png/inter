from inter.common import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped


class UsersRoles(db.Model):
    """
    Association table for roles of viewers (target) with respect to streamers (subject).
    """

    __tablename__ = "users_roles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    subject: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    target: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="CASCADE"))


class Roles(db.Model):
    """
    Model of a role that a viewer can have with respect to a streamer. For example, "moderator",
    "VIP", etc.
    """

    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    icon: Mapped[bytes] = mapped_column(nullable=False)
    vip: Mapped[bool] = mapped_column(nullable=False, default=False)
    moderator: Mapped[bool] = mapped_column(nullable=False, default=False)
