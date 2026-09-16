from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models import ItemModel, StoreModel
from schemas import ItemSchema, ItemUpdateSchema


blp = Blueprint(
    "items",
    __name__,
    description="Operations on items",
)


@blp.route("/item/<int:item_id>")
class Item(MethodView):

    @jwt_required()
    @blp.response(200, ItemSchema)
    def get(self, item_id):
        return ItemModel.query.get_or_404(item_id)

    @jwt_required()
    def delete(self, item_id):
        item = ItemModel.query.get_or_404(item_id)

        try:
            db.session.delete(item)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while deleting the item.",
            )

        return {"message": "Item deleted."}

    @jwt_required()
    @blp.arguments(ItemUpdateSchema)
    @blp.response(200, ItemSchema)
    def put(self, item_data, item_id):
        item = ItemModel.query.get_or_404(item_id)

        if "store_id" in item_data:
            StoreModel.query.get_or_404(item_data["store_id"])

        for key, value in item_data.items():
            setattr(item, key, value)

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                409,
                message=(
                    "The item could not be updated because "
                    "it conflicts with existing data."
                ),
            )
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while updating the item.",
            )

        return item


@blp.route("/item")
class ItemList(MethodView):

    @jwt_required()
    @blp.response(200, ItemSchema(many=True))
    def get(self):
        return ItemModel.query.all()

    @jwt_required(fresh=True)
    @blp.arguments(ItemSchema)
    @blp.response(201, ItemSchema)
    def post(self, item_data):
        StoreModel.query.get_or_404(item_data["store_id"])

        item = ItemModel(**item_data)

        try:
            db.session.add(item)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                409,
                message=(
                    "The item could not be created because "
                    "it conflicts with existing data."
                ),
            )
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while inserting the item.",
            )

        return item