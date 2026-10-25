from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required

pages_bp = Blueprint("pages", __name__)


@pages_bp.route("/")
def landing():
    return render_template("index.html")


@pages_bp.route("/login")
def login_page():
    return render_template("login.html")


@pages_bp.route("/register")
def register_page():
    return render_template("register.html")


@pages_bp.route("/forgot-password")
def forgot_password_page():
    return render_template("forgot-password.html")


@pages_bp.route("/dashboard")
@jwt_required()
def dashboard_page():
    # Flask guarantees a valid session cookie before this line runs.
    # No cookie / expired / revoked → JWT error handler fires → 302 to /login.
    return render_template("dashboard.html")