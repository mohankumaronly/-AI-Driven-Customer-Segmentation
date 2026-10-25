import uuid
from datetime import datetime, timezone
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(30), nullable=False)
    normalized_username = db.Column(db.String(30), unique=True, nullable=False, index=True)
    email = db.Column(db.String(254), nullable=False)
    normalized_email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.Text, nullable=False)
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    account_status = db.Column(db.String(30), default="PENDING_VERIFICATION", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    password_changed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    # Relationships
    sessions = db.relationship("AuthSession", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    otps = db.relationship("AuthOTP", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    reset_tokens = db.relationship("PasswordResetToken", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self):
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "email_verified": self.email_verified,
            "account_status": self.account_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
