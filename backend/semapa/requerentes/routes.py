from flask import Blueprint, request, jsonify, current_app, render_template
from flask_login import login_required, current_user
from semapa.models import SessionLocal, Requerente
from datetime import datetime
import sqlalchemy as sa

requerentes_bp = Blueprint('requerentes', __name__)

@requerentes_bp.route('/requerente', methods=['POST'])
@login_required
def cadastrar_requerente():
    data = request.json
    session = SessionLocal()
    try:
        novo = Requerente(
            nome=data['nome'],
            telefone=data.get('telefone', ''),
            observacao=data.get('observacao', ''),
            criado_por=current_user.id,
            data_criacao=datetime.now()
        )
        session.add(novo)
        session.commit()
        return jsonify({"message": "Requerente cadastrado!", "id": novo.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@requerentes_bp.route('/requerentes/<int:id>', methods=['PUT'])
@login_required
def atualizar_requerente(id):
    data = request.json
    session = SessionLocal()
    try:
        req = session.query(Requerente).get(id)
        if not req:
            return jsonify({"error": "Não encontrado"}), 404
        req.nome = data.get('nome', req.nome)
        req.telefone = data.get('telefone', req.telefone)
        req.observacao = data.get('observacao', req.observacao)
        req.data_atualizacao = datetime.now()
        req.atualizado_por = current_user.id
        session.commit()
        return jsonify({"message": "Atualizado!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@requerentes_bp.route('/requerentes', methods=['GET'])
@login_required
def listar_requerentes():
    session = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        query = session.query(Requerente).order_by(Requerente.id.desc())
        total = query.count()
        requerentes = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "requerentes": [ {
                "id": r.id,
                "nome": r.nome,
                "telefone": r.telefone,
                "observacao": r.observacao,
                "data_criacao": r.data_criacao.isoformat() if r.data_criacao else None,
                "criado_por": r.criado_por,
                "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
                "atualizado_por": r.atualizado_por
            } for r in requerentes ],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@requerentes_bp.route('/requerentes/todos', methods=['GET'])
@login_required
def listar_todos_requerentes():
    session = SessionLocal()
    try:
        requerentes = session.query(Requerente).order_by(Requerente.id.desc()).all()
        return jsonify([{
            "id": r.id,
            "nome": r.nome,
            "telefone": r.telefone,
            "observacao": r.observacao,
            "data_criacao": r.data_criacao.isoformat() if r.data_criacao else None,
            "criado_por": r.criado_por,
            "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
            "atualizado_por": r.atualizado_por
        } for r in requerentes]), 200
    finally:
        session.close()

@requerentes_bp.route('/api/requerente/existe', methods=['GET'])
@login_required
def requerente_existe():
    nome = request.args.get('nome')
    with SessionLocal() as session:
        requerente = session.query(Requerente).filter_by(nome=nome).first()
        if requerente:
            return jsonify({"exists": True, "id": requerente.id})
        else:
            return jsonify({"exists": False})
