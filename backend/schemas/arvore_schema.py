from marshmallow import Schema, fields

class ArvoreSchema(Schema):
    id = fields.Int(dump_only=True)
    especie = fields.Str(required=True)
    endereco = fields.Str()
    bairro = fields.Str()
    latitude = fields.Str(required=True)
    longitude = fields.Str(required=True)
    data_plantio = fields.DateTime(allow_none=True)
    foto = fields.Str()
    observacao = fields.Str()
