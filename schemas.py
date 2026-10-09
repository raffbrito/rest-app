from marshmallow import Schema, fields, validate


class PlainItemSchema(Schema):
    id = fields.Int(dump_only=True)

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=80),
    )

    description = fields.Str(
        allow_none=True,
    )

    price = fields.Float(
        required=True,
        validate=validate.Range(min=0),
    )


class PlainStoreSchema(Schema):
    id = fields.Int(dump_only=True)

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=80),
    )


class PlainTagSchema(Schema):
    id = fields.Int(dump_only=True)

    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=80),
    )


class ItemUpdateSchema(Schema):
    name = fields.Str(
        validate=validate.Length(min=1, max=80),
    )

    description = fields.Str(
        allow_none=True,
    )

    price = fields.Float(
        validate=validate.Range(min=0),
    )

    store_id = fields.Int()


class ItemSchema(PlainItemSchema):
    store_id = fields.Int(
        required=True,
        load_only=True,
    )

    store = fields.Nested(
        PlainStoreSchema(),
        dump_only=True,
    )

    tags = fields.List(
        fields.Nested(PlainTagSchema()),
        dump_only=True,
    )


class StoreSchema(PlainStoreSchema):
    items = fields.List(
        fields.Nested(PlainItemSchema()),
        dump_only=True,
    )

    tags = fields.List(
        fields.Nested(PlainTagSchema()),
        dump_only=True,
    )


class TagCreateSchema(Schema):
    name = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=80),
    )


class TagSchema(PlainTagSchema):
    store_id = fields.Int(dump_only=True)

    store = fields.Nested(
        PlainStoreSchema(),
        dump_only=True,
    )

    items = fields.List(
        fields.Nested(PlainItemSchema()),
        dump_only=True,
    )


class TagAndItemSchema(Schema):
    message = fields.Str()
    tag = fields.Nested(TagSchema)
    item = fields.Nested(PlainItemSchema)


class UserSchema(Schema):
    id = fields.Int(dump_only=True)

    username = fields.Str(
        required=True,
    )

    password = fields.Str(
        required=True,
        load_only=True,
    )