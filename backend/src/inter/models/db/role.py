from inter.common import db
from sqlalchemy import ForeignKey
from sqlalchemy.orm import mapped_column, Mapped


class UsersRoles(db.Model):
    __tablename__ = "users_roles"
    user: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True
    )


class Role(db.Model):
    __tablename__ = "roles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    icon: Mapped[bytes] = mapped_column(nullable=False)
