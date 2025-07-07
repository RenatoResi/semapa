from flask import Blueprint, request, jsonify
from database import SessionLocal, Requerente

requerente_bp = Blueprint('requerente', __name__)

@requerente_bp.route('/requerente', methods=['POST'])
def cadastrar_requerente():
    data = request.json
    session = SessionLocal()
    try:
        novo = Requerente(
            nome=data['nome'],
            telefone=data.get('telefone', ''),
            observacao=data.get('observacao', '')
        )
        session.add(novo)
        session.commit()
        return jsonify({"message": "Requerente cadastrado!", "id": novo.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@requerente_bp.route('/requerentes', methods=['GET'])
def listar_requerentes():
    session = SessionLocal()
    try:
        requerentes = session.query(Requerente).all()
        return jsonify([{
            "id": r.id,
            "nome": r.nome,
            "telefone": r.telefone,
            "observacao": r.observacao
        } for r in requerentes]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
