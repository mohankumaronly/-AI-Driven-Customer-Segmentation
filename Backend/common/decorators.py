from functools import wraps
from flask import g
from flask_jwt_extended import get_jwt, current_user
from common.exceptions import AuthenticationError, ForbiddenError


def session_required(fn):
    """
    Decorator to ensure the session and user are active,
    setting g.current_user and g.current_session_id.
    Can be used alongside or inside routes with @jwt_required().
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user:
            raise AuthenticationError("Authentication is required.")
        if current_user.account_status != "ACTIVE":
            raise ForbiddenError("Account is not active.")
        jwt_claims = get_jwt()
        g.current_user = current_user
        g.current_session_id = jwt_claims.get("sid")
        return fn(*args, **kwargs)
    return wrapper
