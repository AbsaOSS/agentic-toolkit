"""User service — business logic layer for user management."""
from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate
from src.core.security import hash_password, verify_password
from src.core.exceptions import UserNotFoundError, DuplicateEmailError


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_PASSWORD_MIN_LEN = 8


def validate_email(email: str) -> bool:
    """Return True if *email* is a syntactically valid e-mail address.

    Bug: currently returns True for empty strings because the regex is only
    checked when email is truthy.  Fix: add an explicit empty-string guard.
    """
    # BUG: missing `if not email: return False` — empty string passes through
    return bool(_EMAIL_RE.match(email))


def validate_password(password: str) -> bool:
    """Return True if password meets minimum length and complexity rules."""
    if not password or len(password) < _PASSWORD_MIN_LEN:
        return False
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    return has_upper and has_digit


# ---------------------------------------------------------------------------
# UserService
# ---------------------------------------------------------------------------

class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_user(self, user_id: str) -> User:
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise UserNotFoundError(user_id)
        return user

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_users(self, skip: int = 0, limit: int = 50) -> List[User]:
        return (
            self.db.query(User)
            .filter(User.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def search_users(self, query: str, limit: int = 20) -> List[User]:
        pattern = f"%{query}%"
        return (
            self.db.query(User)
            .filter(
                (User.email.ilike(pattern)) | (User.display_name.ilike(pattern))
            )
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def register(self, payload: UserCreate) -> User:
        if not validate_email(payload.email):
            raise ValueError(f"Invalid email address: {payload.email!r}")
        if not validate_password(payload.password):
            raise ValueError("Password does not meet complexity requirements.")
        if self.get_user_by_email(payload.email):
            raise DuplicateEmailError(payload.email)

        user = User(
            id=str(uuid.uuid4()),
            email=payload.email.lower().strip(),
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
            created_at=datetime.utcnow(),
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(self, user_id: str, payload: UserUpdate) -> User:
        user = self.get_user(user_id)
        if payload.display_name is not None:
            user.display_name = payload.display_name
        if payload.email is not None:
            if not validate_email(payload.email):
                raise ValueError(f"Invalid email address: {payload.email!r}")
            existing = self.get_user_by_email(payload.email)
            if existing and existing.id != user_id:
                raise DuplicateEmailError(payload.email)
            user.email = payload.email.lower().strip()
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(
        self, user_id: str, old_password: str, new_password: str
    ) -> None:
        user = self.get_user(user_id)
        if not verify_password(old_password, user.password_hash):
            raise ValueError("Current password is incorrect.")
        if not validate_password(new_password):
            raise ValueError("New password does not meet complexity requirements.")
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()

    def deactivate_user(self, user_id: str) -> None:
        user = self.get_user(user_id)
        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        self.db.commit()

    def reactivate_user(self, user_id: str) -> None:
        user = self.get_user(user_id)
        user.is_active = True
        user.deactivated_at = None
        user.updated_at = datetime.utcnow()
        self.db.commit()

    # ------------------------------------------------------------------
    # Auth helpers
    # ------------------------------------------------------------------

    def generate_password_reset_token(self, email: str) -> Optional[str]:
        user = self.get_user_by_email(email)
        if not user or not user.is_active:
            return None
        token = hashlib.sha256(
            f"{user.id}{user.password_hash}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()
        user.reset_token = token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        self.db.commit()
        return token

    def consume_password_reset_token(self, token: str, new_password: str) -> bool:
        user = (
            self.db.query(User)
            .filter(User.reset_token == token)
            .first()
        )
        if not user:
            return False
        if user.reset_token_expires < datetime.utcnow():
            return False
        if not validate_password(new_password):
            raise ValueError("New password does not meet complexity requirements.")
        user.password_hash = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
