from flask import Blueprint, request, jsonify
from database import SessionLocal, Requerimento

requerimento_bp = Blueprint('requerimento', __name__)

@requerimento_bp.route('/requerimento', methods=['POST'])
def cadastrar_requerimento():
    data = request.json
    session = SessionLocal()
    try:
        novo = Requerimento(
            numero=data['numero'],
            tipo=data['tipo'],
            motivo=data['motivo'],
            prioridade=data.get('prioridade', 'Normal'),
            requerente_id=data['requerente_id'],
            arvore_id=data.get('arvore_id'),
            observacao=data.get('observacao', '')
        )
        session.add(novo)
        session.commit()
        return jsonify({"message": "Requerimento cadastrado!", "id": novo.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@requerimento_bp.route('/requerimentos', methods=['GET'])
def listar_requerimentos():
    session = SessionLocal()
    try:
        requerimentos = session.query(Requerimento).all()
        return jsonify([{
            "id": r.id,
            "numero": r.numero,
            "data_abertura": r.data_abertura.isoformat(),
            "tipo": r.tipo,
            "motivo": r.motivo,
            "status": r.status,
            "prioridade": r.prioridade,
            "requerente_id": r.requerente_id,
            "arvore_id": r.arvore_id,
            "observacao": r.observacao
        } for r in requerimentos]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
