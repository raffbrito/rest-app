import pytest

from app import create_app
from db import db


@pytest.fixture
def app():
    app = create_app(
        "sqlite://",
        {
            "TESTING": True,
            "JWT_SECRET_KEY": "76096766e5d750474e66a20d8ed7cd64df722b3f8eda6dbc7fb29448e5c9d25f",
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
