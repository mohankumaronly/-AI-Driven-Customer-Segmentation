from datetime import datetime, timezone
from extensions import db
from modules.auth.models import AuthOTP, AuthSession, PasswordResetToken


class AuthRepository:
    # --- OTP Operations ---
    @staticmethod
    def create_otp(user_id: str | None, email: str, purpose: str, otp_hash: str, expires_at: datetime) -> AuthOTP:
        record = AuthOTP(
            user_id=user_id,
            email=email.lower().strip(),
            purpose=purpose,
            otp_hash=otp_hash,
            expires_at=expires_at,
            attempt_count=0,
        )
        db.session.add(record)
        db.session.commit()
        return record

    @staticmethod
    def get_latest_active_otp(email: str, purpose: str) -> AuthOTP | None:
        return (
            AuthOTP.query.filter_by(
                email=email.lower().strip(),
                purpose=purpose,
                consumed_at=None,
            )
            .order_by(AuthOTP.created_at.desc())
            .first()
        )

    @staticmethod
    def get_last_created_otp(email: str, purpose: str) -> AuthOTP | None:
        return (
            AuthOTP.query.filter_by(
                email=email.lower().strip(),
                purpose=purpose,
            )
            .order_by(AuthOTP.created_at.desc())
            .first()
        )

    @staticmethod
    def increment_otp_attempt(record: AuthOTP) -> None:
        record.attempt_count += 1
        db.session.commit()

    @staticmethod
    def consume_otp(record: AuthOTP) -> None:
        record.consumed_at = datetime.now(timezone.utc)
        db.session.commit()

    @staticmethod
    def invalidate_all_otps(email: str, purpose: str) -> None:
        records = AuthOTP.query.filter_by(
            email=email.lower().strip(),
            purpose=purpose,
            consumed_at=None,
        ).all()
        now = datetime.now(timezone.utc)
        for r in records:
            r.consumed_at = now
        db.session.commit()

    # --- Session Operations ---
    @staticmethod
    def create_session(user_id: str, expires_at: datetime, client_label: str | None = None, ip_address: str | None = None) -> AuthSession:
        session = AuthSession(
            user_id=str(user_id),
            expires_at=expires_at,
            client_label=client_label,
            ip_address=ip_address,
        )
        db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def get_session(session_id: str) -> AuthSession | None:
        return db.session.get(AuthSession, str(session_id))

    @staticmethod
    def update_session_activity(session: AuthSession) -> None:
        session.last_used_at = datetime.now(timezone.utc)
        db.session.commit()

    @staticmethod
    def revoke_session(session_id: str) -> None:
        session = db.session.get(AuthSession, str(session_id))
        if session and session.revoked_at is None:
            session.revoked_at = datetime.now(timezone.utc)
            db.session.commit()

    @staticmethod
    def revoke_all_user_sessions(user_id: str) -> None:
        now = datetime.now(timezone.utc)
        sessions = AuthSession.query.filter(
            AuthSession.user_id == str(user_id),
            AuthSession.revoked_at.is_(None),
        ).all()
        for s in sessions:
            s.revoked_at = now
        db.session.commit()

    # --- Password Reset Token Operations ---
    @staticmethod
    def create_reset_token(user_id: str, token_hash: str, expires_at: datetime) -> PasswordResetToken:
        token_record = PasswordResetToken(
            user_id=str(user_id),
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.session.add(token_record)
        db.session.commit()
        return token_record

    @staticmethod
    def get_reset_token(token_hash: str) -> PasswordResetToken | None:
        return PasswordResetToken.query.filter_by(
            token_hash=token_hash,
            consumed_at=None,
        ).first()

    @staticmethod
    def consume_reset_token(record: PasswordResetToken) -> None:
        record.consumed_at = datetime.now(timezone.utc)
        db.session.commit()
