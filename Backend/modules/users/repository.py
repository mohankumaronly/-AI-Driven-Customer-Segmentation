from datetime import datetime, timezone
from sqlalchemy import or_
from extensions import db
from modules.users.models import User


class UserRepository:
    @staticmethod
    def get_by_id(user_id: str) -> User | None:
        return db.session.get(User, str(user_id))

    @staticmethod
    def get_by_normalized_username(username: str) -> User | None:
        return User.query.filter_by(normalized_username=username.lower().strip()).first()

    @staticmethod
    def get_by_normalized_email(email: str) -> User | None:
        return User.query.filter_by(normalized_email=email.lower().strip()).first()

    @staticmethod
    def get_by_identifier(identifier: str) -> User | None:
        norm = identifier.lower().strip()
        return User.query.filter(
            or_(User.normalized_username == norm, User.normalized_email == norm)
        ).first()

    @staticmethod
    def create(username: str, email: str, password_hash: str) -> User:
        user = User(
            username=username.strip(),
            normalized_username=username.lower().strip(),
            email=email.strip(),
            normalized_email=email.lower().strip(),
            password_hash=password_hash,
            email_verified=False,
            account_status="PENDING_VERIFICATION",
        )
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def update_password(user: User, password_hash: str) -> None:
        user.password_hash = password_hash
        user.password_changed_at = datetime.now(timezone.utc)
        db.session.commit()

    @staticmethod
    def activate_user(user: User) -> None:
        user.email_verified = True
        user.account_status = "ACTIVE"
        db.session.commit()

    @staticmethod
    def update_username(user: User, new_username: str) -> None:
        user.username = new_username.strip()
        user.normalized_username = new_username.lower().strip()
        db.session.commit()

    @staticmethod
    def mark_for_deletion(user: User) -> None:
        user.account_status = "PENDING_DELETION"
        db.session.commit()
