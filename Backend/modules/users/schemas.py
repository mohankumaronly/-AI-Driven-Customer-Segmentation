from common.exceptions import ValidationError
from common.validators import validate_username


def validate_update_user_input(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    
    # Check for forbidden fields
    forbidden_fields = {"email", "email_verified", "account_status", "password_hash", "id", "created_at", "updated_at"}
    disallowed = set(data.keys()).intersection(forbidden_fields)
    if disallowed:
        raise ValidationError(
            f"Cannot update field(s): {', '.join(disallowed)}.",
            errors=[{"field": f, "code": "FORBIDDEN_FIELD", "message": f"Updating {f} is not permitted."} for f in disallowed],
        )

    validated = {}
    if "username" in data:
        validated["username"] = validate_username(data.get("username"))
    
    if not validated:
        raise ValidationError("No valid fields provided for update.")
    
    return validated
