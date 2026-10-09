from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models import StoreModel
from schemas import StoreSchema


blp = Blueprint(
    "stores",
    __name__,
    description="Operations on stores",
)


@blp.route("/store/<int:store_id>")
class Store(MethodView):

    @blp.response(200, StoreSchema)
    def get(self, store_id):
        return db.get_or_404(StoreModel, store_id)

    @jwt_required(fresh=True)
    def delete(self, store_id):
        store = db.get_or_404(StoreModel, store_id)

        try:
            db.session.delete(store)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while deleting the store.",
            )

        return {"message": "Store deleted."}


@blp.route("/store")
class StoreList(MethodView):

    @blp.response(200, StoreSchema(many=True))
    def get(self):
        return StoreModel.query.all()

    @jwt_required(fresh=True)
    @blp.arguments(StoreSchema)
    @blp.response(201, StoreSchema)
    def post(self, store_data):
        store = StoreModel(**store_data)

        try:
            db.session.add(store)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                409,
                message="A store with that name already exists.",
            )
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while inserting the store.",
            )

        return store