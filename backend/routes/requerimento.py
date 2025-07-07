from flask import Blueprint, request, jsonify
from services import RequerimentoService

requerimento_bp = Blueprint('requerimento', __name__)

@requerimento_bp.route('/requerimento', methods=['POST'])
def cadastrar_requerimento():
    data = request.json
    try:
        novo = RequerimentoService.criar(data)
        return jsonify({"message": "Requerimento cadastrado!", "id": novo.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@requerimento_bp.route('/requerimentos', methods=['GET'])
def listar_requerimentos():
    try:
        requerimentos = RequerimentoService.listar()
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
