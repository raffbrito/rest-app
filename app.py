import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_smorest import Api

from db import db
from models import BlockListModel

from resources.item import blp as ItemBluePrint
from resources.store import blp as StoreBluePrint
from resources.tag import blp as TagBluePrint
from resources.user import blp as UserBluePrint


def create_app(db_url=None, test_config=None):
    load_dotenv()

    app = Flask(__name__)

    app.config.update(
        PROPAGATE_EXCEPTIONS=True,
        API_TITLE="Stores REST API",
        API_VERSION="V1",
        OPENAPI_VERSION="3.0.3",
        OPENAPI_URL_PREFIX="/",
        OPENAPI_SWAGGER_UI_PATH="/swagger-ui",
        OPENAPI_SWAGGER_UI_URL=(
            "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"
        ),
        SQLALCHEMY_DATABASE_URI=(
            db_url
            or os.getenv("DATABASE_URL")
            or "sqlite:///data.db"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY"),
    )

    if test_config:
        app.config.update(test_config)

    if not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError(
            "JWT_SECRET_KEY is not configured. "
            "Set it in the environment or a local .env file."
        )

    db.init_app(app)
    Migrate(app, db)

    api = Api(app)
    jwt = JWTManager(app)

    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    @jwt.token_in_blocklist_loader
    def check_if_token_in_blocklist(jwt_header, jwt_payload):
        jti = jwt_payload["jti"]

        token = BlockListModel.query.filter_by(token=jti).first()

        return token is not None

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "message": "The token has been revoked.",
                    "error": "token_revoked",
                }
            ),
            401,
        )

    @jwt.needs_fresh_token_loader
    def fresh_token_required_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "message": "Fresh token required.",
                    "error": "fresh_token_required",
                }
            ),
            401,
        )

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return (
            jsonify(
                {
                    "message": "The token has expired.",
                    "error": "token_expired",
                }
            ),
            401,
        )

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return (
            jsonify(
                {
                    "message": "Signature verification failed.",
                    "error": "invalid_token",
                }
            ),
            401,
        )

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return (
            jsonify(
                {
                    "description": (
                        "Request does not contain an access token."
                    ),
                    "error": "authorization_required",
                }
            ),
            401,
        )

    api.register_blueprint(ItemBluePrint)
    api.register_blueprint(StoreBluePrint)
    api.register_blueprint(TagBluePrint)
    api.register_blueprint(UserBluePrint)

    return app