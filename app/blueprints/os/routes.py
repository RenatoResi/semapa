
from app.models import Arvore, Especies, Requerimento, OrdemServico
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime
from config import SessionLocal
from app import app


bp = Blueprint('ordens_servico', __name__)


@bp.route('/ordens_servico', methods=['GET', 'POST'])
@login_required
def ordens_servico():
    if request.method == 'GET':
        return listar_ordens_servico()
    elif request.method == 'POST':
        return cadastrar_ordem_servico()

def listar_ordens_servico():
    session = SessionLocal()
    try:
        ordens = session.query(OrdemServico).all()
        ordens_json = []
        for os in ordens:
            # Carregar requerimentos com dados completos
            requerimentos = []
            for req in os.requerimentos:
                requerimentos.append({
                    "id": req.id,
                    "numero": req.numero,
                    "status": req.status,  # CAMPO ADICIONADO
                    "requerente_nome": req.requerente.nome if req.requerente else "",
                    "requerente_telefone": req.requerente.telefone if req.requerente else "",
                    "arvore_endereco": req.arvore.endereco if req.arvore else "",
                    "arvore_latitude": req.arvore.latitude if req.arvore else None,
                    "arvore_longitude": req.arvore.longitude if req.arvore else None
                })
            
            ordens_json.append({
                "id": os.id,
                "numero": os.numero,
                "responsavel": os.responsavel,
                "data_emissao": os.data_emissao.isoformat() if os.data_emissao else None,
                "data_execucao": os.data_execucao.isoformat() if os.data_execucao else None,
                "status": os.status,
                "observacao": os.observacao,
                "requerimentos": requerimentos
            })
        return jsonify(ordens_json), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

def cadastrar_ordem_servico():
    data = request.json
    session = SessionLocal()
    try:
        # Verificar se requerimento_ids existe e não está vazio
        requerimento_ids = data.get('requerimento_ids', [])
        if not requerimento_ids:
            return jsonify({"error": "Nenhum requerimento selecionado."}), 400
        
        # Verificar se todos os requerimentos existem
        requerimentos = session.query(Requerimento).filter(Requerimento.id.in_(requerimento_ids)).all()
        if len(requerimentos) != len(requerimento_ids):
            ids_encontrados = {r.id for r in requerimentos}
            ids_nao_encontrados = [rid for rid in requerimento_ids if rid not in ids_encontrados]
            return jsonify({"error": f"Requerimentos não encontrados: {ids_nao_encontrados}"}), 400
        
        nova = OrdemServico(
            numero=data['numero'],
            responsavel=data['responsavel'],
            observacao=data.get('observacao', ''),
            criado_por=current_user.id,
            data_emissao=datetime.now()
        )
        if 'data_execucao' in data:
            nova.data_execucao = data['data_execucao']
        nova.requerimentos = requerimentos
        session.add(nova)
        session.commit()
        return jsonify({"message": "Ordem de serviço cadastrada!", "id": nova.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/ordens_servico/<int:id>', methods=['PUT'])
@login_required
def atualizar_ordem_servico(id):
    data = request.json
    session = SessionLocal()
    try:
        ordem = session.query(OrdemServico).get(id)
        if not ordem:
            return jsonify({"error": "Ordem de serviço não encontrada"}), 404
        ordem.numero = data.get('numero', ordem.numero)
        ordem.responsavel = data.get('responsavel', ordem.responsavel)
        ordem.observacao = data.get('observacao', ordem.observacao)
        if 'data_execucao' in data:
            ordem.data_execucao = data['data_execucao']
        ordem.data_atualizacao = datetime.now()
        ordem.atualizado_por = current_user.id
        session.commit()
        return jsonify({"message": "Ordem de serviço atualizada!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/ordens_servico/<int:id>', methods=['GET'])
@login_required
def detalhes_ordem_servico(id):
    session = SessionLocal()
    try:
        os = session.query(OrdemServico).get(id)
        if not os:
            return jsonify({"error": "Ordem de serviço não encontrada"}), 404
        
        # Carregar requerimentos com dados completos
        requerimentos = []
        for req in os.requerimentos:
            requerimentos.append({
                "id": req.id,
                "numero": req.numero,
                "tipo": req.tipo,
                "motivo": req.motivo,
                "status": req.status,  # CAMPO ESSENCIAL ADICIONADO
                "requerente_nome": req.requerente.nome if req.requerente else "",
                "requerente_telefone": req.requerente.telefone if req.requerente else "",
                "arvore_endereco": req.arvore.endereco if req.arvore else "",
                "arvore_latitude": req.arvore.latitude if req.arvore else None,
                "arvore_longitude": req.arvore.longitude if req.arvore else None
            })
        
        return jsonify({
            "id": os.id,
            "numero": os.numero,
            "responsavel": os.responsavel,
            "data_emissao": os.data_emissao.isoformat() if os.data_emissao else None,
            "data_execucao": os.data_execucao.isoformat() if os.data_execucao else None,
            "status": os.status,
            "observacao": os.observacao,
            "requerimentos": requerimentos
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()