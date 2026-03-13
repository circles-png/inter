from inter.common import db
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, UniqueConstraint, CheckConstraint


class Moderation(db.Model):
    """
    Association table for moderation relationships between users. A viewer may receive a timeout
    from a streamer, which prevents them from chatting in the streamer's chat for a certain amount
    (maybe indefinite) of time.
    """

    __tablename__ = "moderation"

    subject: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )
    target: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )
    duration: Mapped[int] = mapped_column()
    start: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint("subject", "target"),
        CheckConstraint("subject != target"),
        CheckConstraint("duration > 0"),
    )
