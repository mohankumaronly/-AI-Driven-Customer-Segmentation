from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

from common.utils import ensure_utc
from common.exceptions import (
    ValidationError,
    AuthenticationError,
    ForbiddenError,
    ConflictError,
    RateLimitExceededError,
)
from modules.users.repository import UserRepository
from modules.auth.repository import AuthRepository
from modules.auth.tokens import (
    generate_otp,
    hash_otp,
    verify_otp_hash,
    generate_reset_token,
    hash_reset_token,
    verify_reset_token_hash,
    create_user_access_token,
)
from modules.email.service import EmailService


class AuthService:
    @staticmethod
    def register(username: str, email: str, password: str) -> dict:
        # Check username uniqueness
        if UserRepository.get_by_normalized_username(username):
            raise ConflictError("Username is already taken.")

        # Check email uniqueness
        existing_user = UserRepository.get_by_normalized_email(email)
        if existing_user:
            if existing_user.email_verified:
                raise ConflictError("Email is already registered.")
            else:
                raise ConflictError("Email is already registered and pending verification.")

        # Hash password and create user
        pw_hash = generate_password_hash(password)
        user = UserRepository.create(username=username, email=email, password_hash=pw_hash)

        # Generate and save OTP
        otp = generate_otp()
        otp_hash_val = hash_otp(otp)
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=current_app.config.get("OTP_EXPIRE_SECONDS", 300)
        )

        AuthRepository.create_otp(
            user_id=user.id,
            email=user.email,
            purpose="EMAIL_VERIFICATION",
            otp_hash=otp_hash_val,
            expires_at=expires_at,
        )

        # Send OTP email
        EmailService.send_verification_otp(user.email, otp)

        return {
            "user": user.to_dict(),
            "verification_required": True,
            "otp_expires_in_seconds": current_app.config.get("OTP_EXPIRE_SECONDS", 300),
        }

    @staticmethod
    def verify_email(email: str, otp: str) -> dict:
        user = UserRepository.get_by_normalized_email(email)
        if not user:
            raise ValidationError("Account not found.")

        if user.email_verified and user.account_status == "ACTIVE":
            return {"email_verified": True, "account_status": "ACTIVE"}

        otp_record = AuthRepository.get_latest_active_otp(email, "EMAIL_VERIFICATION")
        if not otp_record:
            raise ValidationError("No pending verification code found or code has expired.")

        now = datetime.now(timezone.utc)
        if ensure_utc(otp_record.expires_at) < now:
            AuthRepository.consume_otp(otp_record)
            raise ValidationError("Verification code has expired. Please request a new code.")

        max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 5)
        if otp_record.attempt_count >= max_attempts:
            AuthRepository.consume_otp(otp_record)
            raise ValidationError("Maximum verification attempts exceeded. Please request a new code.")

        if not verify_otp_hash(otp, otp_record.otp_hash):
            AuthRepository.increment_otp_attempt(otp_record)
            raise ValidationError("Invalid verification code.")

        # Successfully verified
        AuthRepository.consume_otp(otp_record)
        UserRepository.activate_user(user)

        return {"email_verified": True, "account_status": "ACTIVE"}

    @staticmethod
    def resend_verification_otp(email: str) -> None:
        user = UserRepository.get_by_normalized_email(email)
        if not user or user.email_verified:
            # Do not reveal whether account exists or is verified
            return

        last_otp = AuthRepository.get_last_created_otp(email, "EMAIL_VERIFICATION")
        cooldown = current_app.config.get("OTP_RESEND_COOLDOWN_SECONDS", 60)
        now = datetime.now(timezone.utc)

        if last_otp and last_otp.created_at:
            elapsed = (now - ensure_utc(last_otp.created_at)).total_seconds()
            if elapsed < cooldown:
                remaining = int(cooldown - elapsed)
                raise RateLimitExceededError(
                    f"Please wait {remaining} seconds before requesting another verification code."
                )

        AuthRepository.invalidate_all_otps(email, "EMAIL_VERIFICATION")

        otp = generate_otp()
        otp_hash_val = hash_otp(otp)
        expires_at = now + timedelta(seconds=current_app.config.get("OTP_EXPIRE_SECONDS", 300))

        AuthRepository.create_otp(
            user_id=user.id,
            email=user.email,
            purpose="EMAIL_VERIFICATION",
            otp_hash=otp_hash_val,
            expires_at=expires_at,
        )

        EmailService.send_verification_otp(user.email, otp)

    @staticmethod
    def login(identifier: str, password: str, client_label: str | None = None, ip_address: str | None = None) -> tuple[dict, str, int]:
        user = UserRepository.get_by_identifier(identifier)
        if not user or not check_password_hash(user.password_hash, password):
            raise AuthenticationError("Invalid username/email or password.")

        if not user.email_verified or user.account_status == "PENDING_VERIFICATION":
            raise ForbiddenError("Please verify your email address before logging in.")

        if user.account_status != "ACTIVE":
            raise ForbiddenError(f"Account is {user.account_status.lower()}.")

        expires_seconds = int(current_app.config.get("ACCESS_TOKEN_EXPIRES_SECONDS", 604800))
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_seconds)

        # Create session record
        session = AuthRepository.create_session(
            user_id=user.id,
            expires_at=expires_at,
            client_label=client_label,
            ip_address=ip_address,
        )

        # Create JWT access token
        access_token = create_user_access_token(user_id=user.id, session_id=session.id)

        return user.to_dict(), access_token, expires_seconds

    @staticmethod
    def logout(session_id: str | None) -> None:
        if session_id:
            AuthRepository.revoke_session(session_id)

    @staticmethod
    def forgot_password(email: str) -> None:
        user = UserRepository.get_by_normalized_email(email)
        if not user or user.account_status != "ACTIVE":
            return

        now = datetime.now(timezone.utc)
        AuthRepository.invalidate_all_otps(email, "PASSWORD_RESET")

        otp = generate_otp()
        otp_hash_val = hash_otp(otp)
        expires_at = now + timedelta(seconds=current_app.config.get("OTP_EXPIRE_SECONDS", 300))

        AuthRepository.create_otp(
            user_id=user.id,
            email=user.email,
            purpose="PASSWORD_RESET",
            otp_hash=otp_hash_val,
            expires_at=expires_at,
        )

        EmailService.send_password_reset_otp(user.email, otp)

    @staticmethod
    def verify_reset_otp(email: str, otp: str) -> dict:
        user = UserRepository.get_by_normalized_email(email)
        if not user:
            raise ValidationError("Invalid reset code or email.")

        otp_record = AuthRepository.get_latest_active_otp(email, "PASSWORD_RESET")
        if not otp_record:
            raise ValidationError("Invalid or expired password reset code.")

        now = datetime.now(timezone.utc)
        if ensure_utc(otp_record.expires_at) < now:
            AuthRepository.consume_otp(otp_record)
            raise ValidationError("Password reset code has expired. Please request a new code.")

        max_attempts = current_app.config.get("OTP_MAX_ATTEMPTS", 5)
        if otp_record.attempt_count >= max_attempts:
            AuthRepository.consume_otp(otp_record)
            raise ValidationError("Maximum attempts exceeded. Please request a new code.")

        if not verify_otp_hash(otp, otp_record.otp_hash):
            AuthRepository.increment_otp_attempt(otp_record)
            raise ValidationError("Invalid password reset code.")

        # Consume OTP and create short-lived reset token
        AuthRepository.consume_otp(otp_record)

        reset_token = generate_reset_token()
        token_hash_val = hash_reset_token(reset_token)
        token_expires_at = now + timedelta(
            seconds=current_app.config.get("PASSWORD_RESET_TOKEN_EXPIRE_SECONDS", 300)
        )

        AuthRepository.create_reset_token(
            user_id=user.id,
            token_hash=token_hash_val,
            expires_at=token_expires_at,
        )

        return {
            "reset_token": reset_token,
            "expires_in_seconds": current_app.config.get("PASSWORD_RESET_TOKEN_EXPIRE_SECONDS", 300),
        }

    @staticmethod
    def reset_password(reset_token: str, new_password: str) -> None:
        token_hash_val = hash_reset_token(reset_token)
        token_record = AuthRepository.get_reset_token(token_hash_val)

        if not token_record or token_record.consumed_at is not None:
            raise ValidationError("Invalid or expired reset token.")

        now = datetime.now(timezone.utc)
        if ensure_utc(token_record.expires_at) < now:
            AuthRepository.consume_reset_token(token_record)
            raise ValidationError("Reset token has expired. Please request a new one.")

        user = UserRepository.get_by_id(token_record.user_id)
        if not user:
            raise ValidationError("User account not found.")

        # Update password
        new_pw_hash = generate_password_hash(new_password)
        UserRepository.update_password(user, new_pw_hash)

        # Consume reset token
        AuthRepository.consume_reset_token(token_record)

        # Revoke all active sessions
        AuthRepository.revoke_all_user_sessions(user.id)

        # Send notification email
        EmailService.send_password_changed_notification(user.email)

    @staticmethod
    def change_password(user, current_password: str, new_password: str) -> None:
        if not check_password_hash(user.password_hash, current_password):
            raise ValidationError(
                "Current password is incorrect.",
                errors=[{"field": "current_password", "code": "INCORRECT_PASSWORD", "message": "Current password is incorrect."}],
            )

        new_pw_hash = generate_password_hash(new_password)
        UserRepository.update_password(user, new_pw_hash)

        # Revoke all sessions for this user
        AuthRepository.revoke_all_user_sessions(user.id)

        # Send notification email
        EmailService.send_password_changed_notification(user.email)
