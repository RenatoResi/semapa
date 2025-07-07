from marshmallow import Schema, fields

class OrdemServicoSchema(Schema):
    id = fields.Int(dump_only=True)
    numero = fields.Str(required=True)
    data_emissao = fields.DateTime(dump_only=True)
    data_execucao = fields.DateTime(allow_none=True)
    responsavel = fields.Str(required=True)
    status = fields.Str()
    observacao = fields.Str()
    requerimento_id = fields.Int(required=True)
