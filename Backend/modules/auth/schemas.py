import re
from common.exceptions import ValidationError
from common.validators import validate_username, validate_email, validate_password


def validate_register_input(data: dict) -> tuple[str, str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    username = validate_username(data.get("username"))
    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))
    return username, email, password


def validate_verify_email_input(data: dict) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    email = validate_email(data.get("email"))
    otp = str(data.get("otp", "")).strip()
    if not otp or not re.match(r"^\d{6}$", otp):
        raise ValidationError(
            "Request validation failed.",
            errors=[{"field": "otp", "code": "INVALID_OTP", "message": "OTP must be a 6-digit number."}],
        )
    return email, otp


def validate_resend_otp_input(data: dict) -> str:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return validate_email(data.get("email"))


def validate_login_input(data: dict) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    identifier = str(data.get("identifier", "")).strip()
    if not identifier:
        raise ValidationError(
            "Request validation failed.",
            errors=[{"field": "identifier", "code": "REQUIRED", "message": "Username or email is required."}],
        )
    password = str(data.get("password", ""))
    if not password:
        raise ValidationError(
            "Request validation failed.",
            errors=[{"field": "password", "code": "REQUIRED", "message": "Password is required."}],
        )
    return identifier, password


def validate_forgot_password_input(data: dict) -> str:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return validate_email(data.get("email"))


def validate_verify_reset_otp_input(data: dict) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    email = validate_email(data.get("email"))
    otp = str(data.get("otp", "")).strip()
    if not otp or not re.match(r"^\d{6}$", otp):
        raise ValidationError(
            "Request validation failed.",
            errors=[{"field": "otp", "code": "INVALID_OTP", "message": "OTP must be a 6-digit number."}],
        )
    return email, otp


def validate_reset_password_input(data: dict) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    reset_token = str(data.get("reset_token", "")).strip()
    if not reset_token:
        raise ValidationError(
            "Request validation failed.",
            errors=[{"field": "reset_token", "code": "REQUIRED", "message": "Reset token is required."}],
        )
    new_password = validate_password(data.get("new_password"), field_name="new_password")
    return reset_token, new_password


def validate_change_password_input(data: dict) -> tuple[str, str]:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    current_password = str(data.get("current_password", ""))
    if not current_password:
        raise ValidationError(
            "Request validation failed.",
            errors=[{"field": "current_password", "code": "REQUIRED", "message": "Current password is required."}],
        )
    new_password = validate_password(data.get("new_password"), field_name="new_password")
    return current_password, new_password
