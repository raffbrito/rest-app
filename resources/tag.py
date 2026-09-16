from flask.views import MethodView
from flask_jwt_extended import jwt_required
from flask_smorest import Blueprint, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from db import db
from models import ItemModel, StoreModel, TagModel
from schemas import TagAndItemSchema, TagCreateSchema, TagSchema


blp = Blueprint(
    "Tags",
    "tags",
    description="Operations on tags",
)


@blp.route("/store/<int:store_id>/tag")
class TagsInStore(MethodView):

    @blp.response(200, TagSchema(many=True))
    def get(self, store_id):
        store = StoreModel.query.get_or_404(store_id)

        return store.tags

    @jwt_required(fresh=True)
    @blp.arguments(TagCreateSchema)
    @blp.response(201, TagSchema)
    def post(self, tag_data, store_id):
        StoreModel.query.get_or_404(store_id)

        tag = TagModel(
            store_id=store_id,
            **tag_data,
        )

        try:
            db.session.add(tag)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            abort(
                409,
                message="A tag with that name already exists.",
            )
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while inserting the tag.",
            )

        return tag


@blp.route("/item/<int:item_id>/tag/<int:tag_id>")
class LinkTagToItem(MethodView):

    @jwt_required()
    @blp.response(200, TagSchema)
    def post(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        if item.store_id != tag.store_id:
            abort(
                400,
                message=(
                    "A tag can only be linked to an item "
                    "from the same store."
                ),
            )

        if tag in item.tags:
            abort(
                409,
                message="This tag is already linked to the item.",
            )

        item.tags.append(tag)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message=(
                    "An error occurred while linking "
                    "the tag to the item."
                ),
            )

        return tag

    @jwt_required()
    @blp.response(200, TagAndItemSchema)
    def delete(self, item_id, tag_id):
        item = ItemModel.query.get_or_404(item_id)
        tag = TagModel.query.get_or_404(tag_id)

        if tag not in item.tags:
            abort(
                404,
                message="The tag is not linked to this item.",
            )

        item.tags.remove(tag)

        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message=(
                    "An error occurred while removing "
                    "the tag from the item."
                ),
            )

        return {
            "message": "Tag removed from item",
            "item": item,
            "tag": tag,
        }


@blp.route("/tag/<int:tag_id>")
class TagById(MethodView):

    @blp.response(200, TagSchema)
    def get(self, tag_id):
        return TagModel.query.get_or_404(tag_id)

    @jwt_required(fresh=True)
    @blp.response(
        202,
        description=(
            "Deletes a tag if it is not associated "
            "with any items."
        ),
        example={"message": "Tag deleted"},
    )
    @blp.alt_response(
        404,
        description="Tag not found",
    )
    @blp.alt_response(
        400,
        description=(
            "Tag is associated with items and "
            "cannot be deleted"
        ),
    )
    def delete(self, tag_id):
        tag = TagModel.query.get_or_404(tag_id)

        if tag.items:
            abort(
                400,
                message=(
                    "Tag is associated with items "
                    "and cannot be deleted"
                ),
            )

        try:
            db.session.delete(tag)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            abort(
                500,
                message="An error occurred while deleting the tag.",
            )

        return {"message": "Tag deleted"}