from datetime import datetime, timezone
import os
from flask import Flask
from flask_limiter.errors import RateLimitExceeded
from flask_jwt_extended.exceptions import CSRFError, JWTExtendedException

from config import Config
from extensions import db, migrate, jwt, limiter
from common.responses import error_response
from common.exceptions import AppException
from common.utils import ensure_utc
from modules.users.models import User
from modules.auth.models import AuthOTP, AuthSession, PasswordResetToken
from modules.users.repository import UserRepository
from modules.auth.repository import AuthRepository

from modules.auth import auth_bp
from modules.users import users_bp
from routes import health_bp


def create_app(config_class=Config):
    # Configure Jinja to look into modules/email/templates as well as default templates
    base_dir = os.path.abspath(os.path.dirname(__file__))
    email_templates = os.path.join(base_dir, "modules", "email", "templates")
    default_templates = os.path.join(base_dir, "templates")

    app = Flask(
        __name__,
        template_folder=email_templates if os.path.exists(email_templates) else default_templates,
    )
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # JWT Callbacks
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_payload):
        sid = jwt_payload.get("sid")
        if not sid:
            return True
        session = AuthRepository.get_session(sid)
        if not session or session.revoked_at is not None:
            return True
        now = datetime.now(timezone.utc)
        if ensure_utc(session.expires_at) < now:
            return True
        user = UserRepository.get_by_id(jwt_payload["sub"])
        if not user or user.account_status != "ACTIVE":
            return True
        AuthRepository.update_session_activity(session)
        return False

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return UserRepository.get_by_id(identity)

    @jwt.unauthorized_loader
    def unauthorized_callback(msg):
        return error_response("Authentication is required.", status_code=401)

    @jwt.invalid_token_loader
    def invalid_token_callback(msg):
        return error_response("Invalid authentication token.", status_code=401)

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        return error_response("Your session is invalid or has expired. Please log in again.", status_code=401)

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        return error_response("Your session is invalid or has expired. Please log in again.", status_code=401)

    # Global Error Handlers
    @app.errorhandler(AppException)
    def handle_app_exception(e):
        return error_response(e.message, errors=e.errors, status_code=e.status_code)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return error_response("CSRF token missing or invalid.", status_code=400)

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exception(e):
        return error_response(str(e), status_code=401)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(e):
        return error_response("Rate limit exceeded. Please try again later.", status_code=429)

    @app.errorhandler(404)
    def handle_not_found(e):
        return error_response("Resource not found.", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return error_response("Method not allowed.", status_code=405)

    @app.errorhandler(500)
    def handle_server_error(e):
        return error_response("An unexpected server error occurred.", status_code=500)

    # Register Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(health_bp, name="health_root")

    # CLI command to create DB tables
    @app.cli.command("init-db")
    def init_db():
        """Create database tables."""
        db.create_all()
        print("Database tables created successfully.")

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
