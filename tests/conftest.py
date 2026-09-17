import pytest

from app import create_app
from db import db


@pytest.fixture
def app():
    app = create_app(
        "sqlite://",
        {
            "TESTING": True,
            "JWT_SECRET_KEY": "test-only-secret-key-at-least-32-bytes-long",
        },
    )

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()
