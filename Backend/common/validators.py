import re
from email_validator import validate_email as ext_validate_email, EmailNotValidError
from common.exceptions import ValidationError

USERNAME_REGEX = re.compile(r"^[a-zA-Z0-9_]{3,30}$")
SPECIAL_CHAR_REGEX = re.compile(r"""[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?~`]""")


def validate_username(username: str | None) -> str:
    if not username or not isinstance(username, str):
        raise ValidationError(
            message="Request validation failed.",
            errors=[{"field": "username", "code": "REQUIRED", "message": "Username is required."}],
        )
    trimmed = username.strip()
    if len(trimmed) < 3 or len(trimmed) > 30:
        raise ValidationError(
            message="Request validation failed.",
            errors=[{
                "field": "username",
                "code": "INVALID_LENGTH",
                "message": "Username must be between 3 and 30 characters.",
            }],
        )
    if not USERNAME_REGEX.match(trimmed):
        raise ValidationError(
            message="Request validation failed.",
            errors=[{
                "field": "username",
                "code": "INVALID_CHARACTERS",
                "message": "Username can only contain letters, numbers, and underscores.",
            }],
        )
    return trimmed


def validate_email(email: str | None) -> str:
    if not email or not isinstance(email, str):
        raise ValidationError(
            message="Request validation failed.",
            errors=[{"field": "email", "code": "REQUIRED", "message": "Email is required."}],
        )
    trimmed = email.strip()
    try:
        valid = ext_validate_email(trimmed, check_deliverability=False)
        return valid.normalized.lower()
    except EmailNotValidError as e:
        raise ValidationError(
            message="Request validation failed.",
            errors=[{"field": "email", "code": "INVALID_EMAIL", "message": str(e)}],
        )


def validate_password(password: str | None, field_name: str = "password") -> str:
    if not password or not isinstance(password, str):
        raise ValidationError(
            message="Request validation failed.",
            errors=[{"field": field_name, "code": "REQUIRED", "message": f"{field_name.replace('_', ' ').capitalize()} is required."}],
        )
    
    errors = []
    if len(password) < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password):
        errors.append("at least one uppercase letter")
    if not re.search(r"[a-z]", password):
        errors.append("at least one lowercase letter")
    if not re.search(r"\d", password):
        errors.append("at least one digit")
    if not SPECIAL_CHAR_REGEX.search(password):
        errors.append("at least one special character")

    if errors:
        raise ValidationError(
            message="Request validation failed.",
            errors=[{
                "field": field_name,
                "code": "WEAK_PASSWORD",
                "message": f"Password must contain {', '.join(errors)}.",
            }],
        )
    return password
