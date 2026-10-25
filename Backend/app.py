from datetime import datetime, timezone
import os
from flask import Flask, request, redirect, jsonify
from flask_limiter.errors import RateLimitExceeded
from flask_jwt_extended.exceptions import CSRFError, JWTExtendedException
from jinja2 import ChoiceLoader, FileSystemLoader

from config import Config
from extensions import db, migrate, jwt, limiter, cors
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
from routes.pages import pages_bp


def create_app(config_class=Config):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    email_templates = os.path.join(base_dir, "modules", "email", "templates")
    default_templates = os.path.join(base_dir, "templates")

    app = Flask(
        __name__,
        template_folder=default_templates,
        static_folder=os.path.join(base_dir, "static"),
        static_url_path="/static",
    )
    app.config.from_object(config_class)

    # Fix Jinja to look in BOTH templates/ and modules/email/templates/
    app.jinja_loader = ChoiceLoader([
        FileSystemLoader(default_templates),
        FileSystemLoader(email_templates)
    ])

    # ---- CORS ----
    cors.init_app(
        app,
        origins=app.config["CORS_ORIGINS"],
        supports_credentials=True,
        allow_headers=[
            "Content-Type",
            "Authorization",
            "X-CSRF-TOKEN",
            "X-Requested-With",
        ],
        expose_headers=["Content-Type"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        max_age=600,
    )

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)

    # ---- JWT blocklist / user lookup ----
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
        return UserRepository.get_by_id(jwt_data["sub"])

    # ---- JWT error handlers ----
    def _is_html_navigation():
        accept = request.headers.get("Accept", "")
        return "text/html" in accept and request.method == "GET"

    @jwt.unauthorized_loader
    def unauthorized_callback(msg):
        if _is_html_navigation():
            return redirect("/login?from=protected", code=302)
        return error_response("Authentication is required.", status_code=401)

    @jwt.invalid_token_loader
    def invalid_token_callback(msg):
        if _is_html_navigation():
            return redirect("/login?reason=invalid", code=302)
        return error_response("Invalid authentication token.", status_code=401)

    @jwt.expired_token_loader
    def expired_token_callback(_jwt_header, _jwt_payload):
        if _is_html_navigation():
            return redirect("/login?reason=expired", code=302)
        return error_response(
            "Your session is invalid or has expired. Please log in again.",
            status_code=401,
        )

    @jwt.revoked_token_loader
    def revoked_token_callback(_jwt_header, _jwt_payload):
        if _is_html_navigation():
            return redirect("/login?reason=revoked", code=302)
        return error_response(
            "Your session is invalid or has expired. Please log in again.",
            status_code=401,
        )

    # ---- Global error handlers ----
    @app.errorhandler(AppException)
    def handle_app_exception(e):
        print(f"\n🚨 [BACKEND VALIDATION ERROR] Path: {request.path}")
        print(f"Message: {e.message}")
        print(f"Errors: {e.errors}\n")
        return error_response(e.message, errors=e.errors, status_code=e.status_code)

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        print(f"[ERR] CSRFError for {request.path}")
        return error_response("CSRF token missing or invalid.", status_code=400)

    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exception(e):
        print(f"[ERR] JWTExtendedException for {request.path}: {type(e).__name__}: {e}")
        if _is_html_navigation():
            return redirect("/login?reason=invalid", code=302)
        return error_response(str(e), status_code=401)

    @app.errorhandler(RateLimitExceeded)
    def handle_rate_limit_exceeded(e):
        print(f"[ERR] RateLimitExceeded for {request.path}")
        return error_response("Rate limit exceeded. Please try again later.", status_code=429)

    @app.errorhandler(404)
    def handle_not_found(e):
        print(f"[404] NOT FOUND: {request.method} {request.path}")
        return error_response("Resource not found.", status_code=404)

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        print(f"[ERR] 405 for {request.method} {request.path}")
        return error_response("Method not allowed.", status_code=405)

    @app.errorhandler(500)
    def handle_server_error(e):
        print(f"[ERR] 500 for {request.path}: {e}")
        return error_response("An unexpected server error occurred.", status_code=500)

    # Print all error bodies to the terminal so we can see exact failures
    @app.after_request
    def _log_errors(response):
        if response.status_code >= 400:
            try:
                body = response.get_data(as_text=True)
                print(f"[ERR-BODY] {request.method} {request.path} → {response.status_code} → {body[:300]}")
            except Exception:
                pass
        return response

    # ---- Blueprints ----
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(users_bp, url_prefix="/api/v1/users")
    app.register_blueprint(health_bp, url_prefix="/api/v1")
    app.register_blueprint(health_bp, name="health_root")
    app.register_blueprint(pages_bp)

    # ---- DEBUG: print registered routes at startup ----
    print("\n" + "=" * 70)
    print("REGISTERED ROUTES AT STARTUP:")
    print("=" * 70)
    for r in sorted(app.url_map.iter_rules(), key=lambda x: str(x.rule)):
        print(f"  {r.rule:40s}  {sorted(r.methods)}")
    print("=" * 70)
    print(f"Template folder: {app.template_folder}")
    print(f"Email template folder: {email_templates}")
    print(f"Static folder:   {app.static_folder}")
    print(f"Blueprints:      {list(app.blueprints.keys())}")
    print("=" * 70 + "\n")

    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database tables created successfully.")

    return app


app = create_app()

if __name__ == "__main__":
    # Render assigns a dynamic PORT. If not found, use 5000 for local.
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)