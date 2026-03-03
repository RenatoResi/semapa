"""
Schemas de validação usando Marshmallow.
Centraliza validação de entrada de dados em todas as rotas.
"""

from marshmallow import Schema, fields, validate, ValidationError, pre_load
import re


class RequerenteSchema(Schema):
    """Schema para validação de Requerente"""
    id = fields.Integer(dump_only=True)
    nome = fields.String(
        required=True,
        validate=validate.Length(min=3, max=100),
        error_messages={"required": "Nome é obrigatório"}
    )
    telefone = fields.String(
        required=False,
        validate=validate.Length(max=20)
    )
    observacao = fields.String(required=False)
    data_criacao = fields.DateTime(dump_only=True)
    criado_por = fields.Integer(dump_only=True)

    class Meta:
        fields = ("id", "nome", "telefone", "observacao", "data_criacao", "criado_por")


class RequerimentoSchema(Schema):
    """Schema para validação de Requerimento"""
    id = fields.Integer(dump_only=True)
    numero = fields.String(
        required=True,
        validate=validate.Length(min=1, max=20),
        error_messages={"required": "Número do requerimento é obrigatório"}
    )
    tipo = fields.String(
        required=True,
        validate=validate.Length(min=1),
        error_messages={"required": "Tipo do requerimento é obrigatório"}
    )
    motivo = fields.String(required=False)
    prioridade = fields.String(
        required=False,
        validate=validate.OneOf(
            ['Baixa', 'Normal', 'Alta'],
            error="Prioridade deve ser: Baixa, Normal ou Alta"
        )
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(
            ['Aberto', 'Em Andamento', 'Concluído', 'Cancelado', 'Pendente'],
            error="Status inválido"
        )
    )
    requerente_id = fields.Integer(required=True)
    arvore_id = fields.Integer(required=False)
    observacao = fields.String(required=False)
    data_criacao = fields.DateTime(dump_only=True)
    criado_por = fields.Integer(dump_only=True)

    class Meta:
        fields = (
            "id", "numero", "tipo", "motivo", "prioridade", "status",
            "requerente_id", "arvore_id", "observacao", "data_criacao", "criado_por"
        )


class TarefaSchema(Schema):
    """Schema para validação de Tarefa/Agenda"""
    id = fields.Integer(dump_only=True)
    descricao = fields.String(
        required=True,
        validate=validate.Length(min=3, max=500),
        error_messages={"required": "Descrição é obrigatória"}
    )
    data_prevista = fields.Date(
        required=True,
        error_messages={"required": "Data prevista é obrigatória"}
    )
    periodo = fields.String(
        required=False,
        validate=validate.OneOf(
            ['manha', 'tarde', 'dia_todo'],
            error="Período deve ser: manha, tarde ou dia_todo"
        )
    )
    prioridade = fields.String(
        required=False,
        validate=validate.OneOf(['baixa', 'normal', 'alta'])
    )
    status = fields.String(
        required=False,
        validate=validate.OneOf(['planejada', 'em_execucao', 'concluida', 'cancelada'])
    )
    complexidade = fields.String(required=False)
    requerimento_id = fields.Integer(required=False)
    chefe_equipe_id = fields.Integer(required=False)
    observacoes = fields.String(required=False)
    criada_por = fields.Integer(dump_only=True)
    criada_em = fields.DateTime(dump_only=True)

    class Meta:
        fields = (
            "id", "descricao", "data_prevista", "periodo", "prioridade",
            "status", "complexidade", "requerimento_id", "chefe_equipe_id",
            "observacoes", "criada_por", "criada_em"
        )


class VistoriaSchema(Schema):
    """Schema para validação de Vistoria"""
    id = fields.Integer(dump_only=True)
    requerimento_id = fields.Integer(required=True)
    vistoria_data = fields.DateTime(required=True)
    status = fields.String(
        required=False,
        validate=validate.OneOf(['Pendente', 'Realizada', 'Concluída'])
    )
    diagnostico = fields.String(required=False)
    acao_recomendada = fields.String(required=False)
    risco_queda = fields.String(required=False)
    observacoes = fields.String(required=False)
    observacoes_tecnicas = fields.String(required=False)
    user_id = fields.Integer(dump_only=True)

    class Meta:
        fields = (
            "id", "requerimento_id", "vistoria_data", "status",
            "diagnostico", "acao_recomendada", "risco_queda",
            "observacoes", "observacoes_tecnicas", "user_id"
        )


class UserSchema(Schema):
    """Schema para validação de User (simplificado para segurança)"""
    id = fields.Integer(dump_only=True)
    email = fields.Email(required=True)
    nome = fields.String(required=False, validate=validate.Length(max=100))
    telefone = fields.String(required=False, validate=validate.Length(max=20))
    nivel = fields.Integer(required=False, validate=validate.Range(min=1, max=5))
    ativo = fields.Boolean(required=False)
    # Password nunca é incluído em schemas de response
    password = fields.String(load_only=True, required=False)

    class Meta:
        fields = ("id", "email", "nome", "telefone", "nivel", "ativo")


class ArvoreSchema(Schema):
    """Schema para validação de Árvore"""
    id = fields.Integer(dump_only=True)
    endereco = fields.String(required=False, validate=validate.Length(max=200))
    bairro = fields.String(required=False, validate=validate.Length(max=100))
    latitude = fields.String(required=False, validate=validate.Length(max=20))
    longitude = fields.String(required=False, validate=validate.Length(max=20))
    especie_id = fields.Integer(required=False)
    data_plantio = fields.DateTime(required=False)
    observacao = fields.String(required=False)
    foto = fields.String(required=False)
    data_criacao = fields.DateTime(dump_only=True)
    criado_por = fields.Integer(dump_only=True)

    class Meta:
        fields = (
            "id", "endereco", "bairro", "latitude", "longitude",
            "especie_id", "data_plantio", "observacao", "foto",
            "data_criacao", "criado_por"
        )


class EspeciaSchema(Schema):
    """Schema para validação de Espécie"""
    id = fields.Integer(dump_only=True)
    nome_popular = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100)
    )
    nome_cientifico = fields.String(
        required=False,
        validate=validate.Length(max=150)
    )
    porte = fields.String(required=False, validate=validate.Length(max=20))
    altura_min = fields.Float(required=False)
    altura_max = fields.Float(required=False)
    observacoes = fields.String(required=False)

    class Meta:
        fields = (
            "id", "nome_popular", "nome_cientifico", "porte",
            "altura_min", "altura_max", "observacoes"
        )


def validate_request_json(schema_class):
    """
    Decorator para validar requisição JSON contra um schema.
    
    Uso:
        @requerentes_bp.route('/requerente', methods=['POST'])
        @validate_request_json(RequerenteSchema)
        def cadastrar_requerente(validated_data):
            # validated_data já está validado
            pass
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            from flask import request, jsonify
            
            schema = schema_class()
            try:
                # Validar JSON recebido
                if not request.is_json:
                    return jsonify({"error": "Content-Type deve ser application/json"}), 400
                
                data = request.json
                validated_data = schema.load(data)
                
                # Passar dados validados como argumento nomeado
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except ValidationError as e:
                # Retornar erros de validação
                return jsonify({
                    "error": "Erro de validação",
                    "details": e.messages
                }), 400
            except Exception as e:
                return jsonify({"error": str(e)}), 400
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator
