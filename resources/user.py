from flask.views import MethodView
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)
from flask_smorest import Blueprint, abort
from passlib.hash import pbkdf2_sha256
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models import BlockListModel, UserModel
from schemas import UserSchema


blp = Blueprint(
    "Users",
    "users",
    description="Operations on users",
)


@blp.route("/register")
class UserRegister(MethodView):

    @blp.arguments(UserSchema)
    def post(self, user_data):
        existing_user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if existing_user:
            abort(
                409,
                message="A user with that username already exists.",
            )

        user = UserModel(
            username=user_data["username"],
            password=pbkdf2_sha256.hash(
                user_data["password"]
            ),
        )

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                409,
                message="A user with that username already exists.",
            )
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while creating the user.",
            )

        return {
            "message": "User created successfully."
        }, 201


@blp.route("/login")
class UserLogin(MethodView):

    @blp.arguments(UserSchema)
    def post(self, user_data):
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(
            user_data["password"],
            user.password,
        ):
            access_token = create_access_token(
                identity=str(user.id),
                fresh=True,
            )

            refresh_token = create_refresh_token(
                identity=str(user.id),
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
            }, 200

        abort(
            401,
            message="Invalid credentials.",
        )


@blp.route("/refresh")
class UserRefresh(MethodView):

    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        refresh_jti = get_jwt()["jti"]

        revoked_token = BlockListModel(
            token=refresh_jti
        )

        try:
            db.session.add(revoked_token)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                400,
                message="Token already revoked.",
            )
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message=(
                    "An error occurred while "
                    "revoking the refresh token."
                ),
            )

        new_token = create_access_token(
            identity=current_user,
            fresh=False,
        )

        return {
            "access_token": new_token
        }, 200


@blp.route("/logout")
class UserLogout(MethodView):

    @jwt_required()
    def post(self):
        jti = get_jwt()["jti"]

        revoked_token = BlockListModel(
            token=jti
        )

        try:
            db.session.add(revoked_token)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                400,
                message="Token already revoked.",
            )
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message=(
                    "An error occurred while "
                    "revoking the token."
                ),
            )

        return {
            "message": "Successfully logged out."
        }, 200


@blp.route("/user/<int:user_id>")
class User(MethodView):

    @jwt_required()
    @blp.response(200, UserSchema)
    def get(self, user_id):
        if get_jwt_identity() != str(user_id):
            abort(
                403,
                message=(
                    "You may only access your own user account."
                ),
            )

        return UserModel.query.get_or_404(user_id)

    @jwt_required(fresh=True)
    def delete(self, user_id):
        if get_jwt_identity() != str(user_id):
            abort(
                403,
                message=(
                    "You may only delete your own user account."
                ),
            )

        user = UserModel.query.get_or_404(user_id)

        try:
            db.session.delete(user)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while deleting the user.",
            )

        return {
            "message": "User deleted."
        }, 200