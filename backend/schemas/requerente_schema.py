from marshmallow import Schema, fields

class RequerenteSchema(Schema):
    id = fields.Int(dump_only=True)
    nome = fields.Str(required=True)
    telefone = fields.Str()
    observacao = fields.Str()
