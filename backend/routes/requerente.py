from flask import Blueprint, request, jsonify
from services import RequerenteService
from flask_login import login_required

requerente_bp = Blueprint('requerente', __name__)

@requerente_bp.route('/requerente', methods=['POST'])
@login_required
def cadastrar_requerente():
    data = request.json
    try:
        novo = RequerenteService.criar(data)
        return jsonify({"message": "Requerente cadastrado!", "id": novo.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@requerente_bp.route('/requerentes', methods=['GET'])
@login_required
def listar_requerentes():
    try:
        requerentes = RequerenteService.listar()
        lista = [{
            "id": r.id,
            "nome": r.nome,
            "telefone": r.telefone,
            "observacao": r.observacao
        } for r in requerentes]
        return jsonify(lista), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
