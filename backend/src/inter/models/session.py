from datetime import datetime
from hashlib import sha256
from math import floor
from os import environ
import secrets
import sqlite3
from inter.utils import generate_secure_random_string


class Session:
    def __init__(self, user_id: int) -> None:
        self.id = generate_secure_random_string()
        secret = generate_secure_random_string()
        self.secret_hash = sha256(secret.encode()).digest()
        self.created_at = datetime.now()
        self.token = f"{self.id}.{secret}"
        self.user = user_id
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "insert into sessions (id, secret_hash, created_at, user) values (?, ?, ?, ?)",
                (
                    self.id,
                    self.secret_hash,
                    floor(self.created_at.timestamp()),
                    self.user,
                ),
            )

    @staticmethod
    def validate_token(token: str) -> "Session | None":
        parts = token.split(".")
        if len(parts) != 2:
            return None
        session_id, secret = parts
        session = Session.get(session_id)
        if not session:
            return None
        secret_hash = sha256(secret.encode()).digest()
        if not secrets.compare_digest(secret_hash, session.secret_hash):
            return None
        return session

    @staticmethod
    def get(session_id: str) -> "Session | None":
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            cursor = db.cursor()
            cursor.execute(
                "select id, secret_hash, created_at, user from sessions where id = ?",
                (session_id,),
            )
            session_id, secret_hash, created_at, user = cursor.fetchone()
        created_at = datetime.fromtimestamp(created_at)
        if (datetime.now() - created_at).total_seconds() > 60 * 60 * 24:
            Session.delete(session_id)
            return None
        session = Session.__new__(Session)
        session.id = session_id
        session.secret_hash = secret_hash
        session.created_at = created_at
        session.user = user
        return session

    @staticmethod
    def delete(session_id: str) -> None:
        with sqlite3.connect(environ["DATABASE_PATH"]) as db:
            db.cursor().execute(
                "delete from sessions where id = ?",
                (session_id,),
            )
