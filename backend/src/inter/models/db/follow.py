from inter.common import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint


class Follow(db.Model):
    """
    Association table for followers and followees, with optional columns for push notification
    settings. `p256dh` and `auth` are used for Web Push authentication.
    """
    __tablename__ = "follow"

    follower: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )
    followee: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )
    endpoint: Mapped[str | None] = mapped_column()
    p256dh: Mapped[bytes | None] = mapped_column()
    auth: Mapped[bytes | None] = mapped_column()

    __table_args__ = (
        UniqueConstraint("follower", "followee"),
        CheckConstraint("follower != followee"),
    )
