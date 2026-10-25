import secrets
from flask import Blueprint, request
from flask_jwt_extended import (
    jwt_required,
    current_user,
    get_jwt,
    set_access_cookies,
    unset_jwt_cookies,
    decode_token,
)
from extensions import limiter
from common.responses import success_response
from modules.auth.schemas import (
    validate_register_input,
    validate_verify_email_input,
    validate_resend_otp_input,
    validate_login_input,
    validate_forgot_password_input,
    validate_verify_reset_otp_input,
    validate_reset_password_input,
    validate_change_password_input,
)
from modules.auth.service import AuthService

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per minute; 50 per hour")
def register():
    data = request.get_json(silent=True) or {}
    username, email, password = validate_register_input(data)
    result = AuthService.register(username, email, password)
    return success_response(
        message="Registration successful. Verify your email to continue.",
        data=result,
        status_code=201,
    )


@auth_bp.route("/verify-email", methods=["POST"])
@limiter.limit("15 per minute; 60 per hour")
def verify_email():
    data = request.get_json(silent=True) or {}
    email, otp = validate_verify_email_input(data)
    result = AuthService.verify_email(email, otp)
    return success_response(
        message="Email verified successfully.",
        data=result,
        status_code=200,
    )


@auth_bp.route("/resend-verification-otp", methods=["POST"])
@limiter.limit("5 per minute; 20 per hour")
def resend_verification_otp():
    data = request.get_json(silent=True) or {}
    email = validate_resend_otp_input(data)
    AuthService.resend_verification_otp(email)
    return success_response(
        message="If the account requires verification, an email will be sent.",
        status_code=200,
    )


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute; 60 per hour")
def login():
    data = request.get_json(silent=True) or {}
    identifier, password = validate_login_input(data)
    client_label = request.headers.get("User-Agent")
    ip_address = request.remote_addr

    user_dict, access_token, expires_in_seconds = AuthService.login(
        identifier=identifier,
        password=password,
        client_label=client_label,
        ip_address=ip_address,
    )

    # Decode access token to retrieve CSRF token
    decoded = decode_token(access_token)
    csrf_token = decoded.get("csrf")

    response = success_response(
        message="Login successful.",
        data={
            "user": user_dict,
            "expires_in_seconds": expires_in_seconds,
            "csrf_token": csrf_token,
        },
        status_code=200,
    )

    # Set HttpOnly access token cookie and CSRF cookie
    set_access_cookies(response, access_token)
    return response


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(optional=True)
def logout():
    try:
        claims = get_jwt()
        session_id = claims.get("sid") if claims else None
        if session_id:
            AuthService.logout(session_id)
    except Exception:
        pass

    response = success_response(message="Logout successful.")
    unset_jwt_cookies(response)
    return response


@auth_bp.route("/forgot-password", methods=["POST"])
@limiter.limit("5 per minute; 20 per hour")
def forgot_password():
    data = request.get_json(silent=True) or {}
    email = validate_forgot_password_input(data)
    AuthService.forgot_password(email)
    return success_response(
        message="If an eligible account exists, password-reset instructions will be sent.",
        status_code=200,
    )


@auth_bp.route("/verify-reset-otp", methods=["POST"])
@limiter.limit("15 per minute; 60 per hour")
def verify_reset_otp():
    data = request.get_json(silent=True) or {}
    email, otp = validate_verify_reset_otp_input(data)
    result = AuthService.verify_reset_otp(email, otp)
    return success_response(
        message="OTP verified successfully.",
        data=result,
        status_code=200,
    )


@auth_bp.route("/reset-password", methods=["POST"])
@limiter.limit("10 per minute")
def reset_password():
    data = request.get_json(silent=True) or {}
    reset_token, new_password = validate_reset_password_input(data)
    AuthService.reset_password(reset_token, new_password)
    response = success_response(
        message="Password reset successfully. Please log in again.",
        status_code=200,
    )
    unset_jwt_cookies(response)
    return response


@auth_bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    data = request.get_json(silent=True) or {}
    current_password, new_password = validate_change_password_input(data)
    AuthService.change_password(current_user, current_password, new_password)
    response = success_response(
        message="Password changed successfully. Please log in again.",
        status_code=200,
    )
    unset_jwt_cookies(response)
    return response


@auth_bp.route("/csrf", methods=["GET"])
def get_csrf_token():
    # Attempt to extract CSRF token from access cookie or CSRF cookie
    csrf_token = request.cookies.get("csrf_access_token")
    if not csrf_token:
        access_cookie = request.cookies.get("access_token_cookie")
        if access_cookie:
            try:
                decoded = decode_token(access_cookie)
                csrf_token = decoded.get("csrf")
            except Exception:
                pass

    if not csrf_token:
        # Generate placeholder or session CSRF token if unauthenticated
        csrf_token = secrets.token_hex(16)

    return success_response(
        message="CSRF token retrieved successfully.",
        data={"csrf_token": csrf_token},
        status_code=200,
    )


@auth_bp.route("/status", methods=["GET"])
@jwt_required(optional=True)
def auth_status():
    if current_user and getattr(current_user, "account_status", None) == "ACTIVE":
        return success_response(
            message="Authenticated.",
            data={
                "authenticated": True,
                "user": {
                    "id": str(current_user.id),
                    "username": current_user.username,
                    "email": current_user.email,
                },
            },
            status_code=200,
        )
    return success_response(
        message="Not authenticated.",
        data={"authenticated": False},
        status_code=200,
    )
