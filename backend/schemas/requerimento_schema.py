from marshmallow import Schema, fields

class RequerimentoSchema(Schema):
    id = fields.Int(dump_only=True)
    numero = fields.Str(required=True)
    data_abertura = fields.DateTime(dump_only=True)
    tipo = fields.Str(required=True)
    motivo = fields.Str(required=True)
    status = fields.Str()
    prioridade = fields.Str()
    requerente_id = fields.Int(required=True)
    arvore_id = fields.Int(allow_none=True)
    observacao = fields.Str()
