from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import get_session, Requerente
from schemas import RequerenteSchema, validate_request_json
from datetime import datetime
from marshmallow import ValidationError

requerentes_bp = Blueprint('requerentes', __name__)

# -------------------- FUNÇÕES AUXILIARES --------------------

def serializar_requerente(r):
    """Serializa requerente com todos os dados"""
    return {
        "id": r.id,
        "nome": r.nome,
        "telefone": r.telefone,
        "observacao": r.observacao,
        "data_criacao": r.data_criacao.isoformat() if r.data_criacao else None,
        "criado_por": r.criado_por,
        "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
        "atualizado_por": r.atualizado_por
    }

# -------------------- ROTAS --------------------

@requerentes_bp.route('/requerente', methods=['POST'])
@login_required
def cadastrar_requerente():
    """Cadastra novo requerente com validação usando Marshmallow"""
    schema = RequerenteSchema()
    try:
        # Validar dados de entrada
        if not request.is_json:
            return jsonify({"error": "Content-Type deve ser application/json"}), 400
        
        validated_data = schema.load(request.get_json())
        
        with get_session() as session:
            novo = Requerente(
                nome=validated_data['nome'],
                telefone=validated_data.get('telefone', ''),
                observacao=validated_data.get('observacao', ''),
                criado_por=current_user.id,
                data_criacao=datetime.now()
            )
            session.add(novo)
        
        return jsonify({
            "message": "Requerente cadastrado com sucesso!", 
            "id": novo.id
        }), 201
        
    except ValidationError as e:
        # Retornar erros de validação
        return jsonify({
            "error": "Erro de validação",
            "details": e.messages
        }), 400
    except Exception as e:
        return jsonify({"error": f"Erro ao cadastrar requerente: {str(e)}"}), 500


@requerentes_bp.route('/requerentes', methods=['GET'])
@login_required
def listar_requerentes():
    """Lista requerentes com paginação"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        
        with get_session() as session:
            query = session.query(Requerente).order_by(Requerente.id.desc())
            total = query.count()
            
            requerentes = (
                query
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )
        
        return jsonify({
            "requerentes": [serializar_requerente(r) for r in requerentes],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@requerentes_bp.route('/requerentes/todos', methods=['GET'])
@login_required
def listar_todos_requerentes():
    """Lista todos os requerentes cadastrados"""
    with get_session() as session:
        requerentes = session.query(Requerente).order_by(Requerente.id.desc()).all()
        return jsonify([serializar_requerente(r) for r in requerentes]), 200


@requerentes_bp.route('/requerentes/<int:id>', methods=['PUT'])
@login_required
def atualizar_requerente(id):
    """Atualiza dados de um requerente existente"""
    data = request.json
    try:
        with get_session() as session:
            req = session.query(Requerente).get(id)
            if not req:
                return jsonify({"error": "Requerente não encontrado"}), 404
            
            req.nome = data.get('nome', req.nome)
            req.telefone = data.get('telefone', req.telefone)
            req.observacao = data.get('observacao', req.observacao)
            req.data_atualizacao = datetime.now()
            req.atualizado_por = current_user.id
        
        return jsonify({"message": "Requerente atualizado com sucesso!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@requerentes_bp.route('/api/requerente/existe', methods=['GET'])
@login_required
def requerente_existe():
    """Verifica se um requerente já existe pelo nome"""
    nome = request.args.get('nome')
    with get_session() as session:
        requerente = session.query(Requerente).filter_by(nome=nome).first()
        if requerente:
            return jsonify({"exists": True, "id": requerente.id}), 200
        else:
            return jsonify({"exists": False}), 200
