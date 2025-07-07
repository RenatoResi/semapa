from flask import Blueprint, request, jsonify
from services import RequerenteService

requerente_bp = Blueprint('requerente', __name__)

@requerente_bp.route('/requerente', methods=['POST'])
def cadastrar_requerente():
    data = request.json
    try:
        novo = RequerenteService.criar(data)
        return jsonify({"message": "Requerente cadastrado!", "id": novo.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@requerente_bp.route('/requerentes', methods=['GET'])
def listar_requerentes():
    try:
        requerentes = RequerenteService.listar()
        return jsonify([{
            "id": r.id,
            "nome": r.nome,
            "telefone": r.telefone,
            "observacao": r.observacao
        } for r in requerentes]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
