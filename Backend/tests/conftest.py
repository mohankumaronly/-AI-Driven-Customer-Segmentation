import pytest
from app import create_app
from config import TestConfig
from extensions import db
from modules.users.models import User
from modules.auth.models import AuthOTP, AuthSession, PasswordResetToken
from werkzeug.security import generate_password_hash


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def active_user(app):
    user = User(
        username="active_user",
        normalized_username="active_user",
        email="active@example.com",
        normalized_email="active@example.com",
        password_hash=generate_password_hash("ValidPass123!"),
        email_verified=True,
        account_status="ACTIVE",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def pending_user(app):
    user = User(
        username="pending_user",
        normalized_username="pending_user",
        email="pending@example.com",
        normalized_email="pending@example.com",
        password_hash=generate_password_hash("ValidPass123!"),
        email_verified=False,
        account_status="PENDING_VERIFICATION",
    )
    db.session.add(user)
    db.session.commit()
    return user
