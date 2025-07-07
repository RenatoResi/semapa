from flask import Blueprint, request, jsonify
from services import OrdemServicoService

ordem_servico_bp = Blueprint('ordem_servico', __name__)

@ordem_servico_bp.route('/ordens_servico', methods=['POST'])
def cadastrar_ordem_servico():
    data = request.json
    try:
        nova = OrdemServicoService.criar(data)
        return jsonify({"message": "Ordem de serviço cadastrada!", "id": nova.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@ordem_servico_bp.route('/ordens_servico', methods=['GET'])
def listar_ordens_servico():
    try:
        ordens = OrdemServicoService.listar()
        return jsonify([{
            "id": o.id,
            "numero": o.numero,
            "data_emissao": o.data_emissao.isoformat(),
            "data_execucao": o.data_execucao.isoformat() if o.data_execucao else None,
            "responsavel": o.responsavel,
            "status": o.status,
            "observacao": o.observacao,
            "requerimento_id": o.requerimento_id
        } for o in ordens]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
