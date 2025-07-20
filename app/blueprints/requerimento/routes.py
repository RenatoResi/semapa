
from app.models import Arvore, Especies, Requerimento, Requerente, OrdemServico
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime
from config import SessionLocal
from sqlalchemy import or_
from app import app
from sqlalchemy import func as sa_func
import sqlalchemy as sa

bp = Blueprint('requerimento', __name__)

@bp.route('/requerimento', methods=['POST'])
@login_required
def cadastrar_requerimento():
    data = request.json
    session = SessionLocal()
    try:
        novo = Requerimento(
            numero=data['numero'],
            data_abertura=datetime.strptime(data['data_abertura'], '%Y-%m-%d'),
            status=data.get('status', 'Pendente'),
            tipo=data['tipo'],
            motivo=data['motivo'],
            prioridade=data.get('prioridade', 'Normal'),
            requerente_id=data['requerente_id'],
            arvore_id=data.get('arvore_id'),
            observacao=data.get('observacao', ''),
            criado_por=current_user.id,
            data_criacao=datetime.now()
        )
        session.add(novo)
        session.commit()
        return jsonify({"message": "Requerimento cadastrado!", "id": novo.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/requerimentos', methods=['GET'])
@login_required
def listar_requerimentos():
    session = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        order_by = request.args.get('order_by', 'id')
        direction = request.args.get('direction', 'desc').lower()
        campos_validos = {
            'id': Requerimento.id,
            'numero': Requerimento.numero,
            'tipo': Requerimento.tipo,
            'motivo': Requerimento.motivo,
            'prioridade': Requerimento.prioridade,
            'status': Requerimento.status,
            'data_abertura': Requerimento.data_abertura
        }
        campo_ordenacao = campos_validos.get(order_by, Requerimento.id)
        if direction == 'asc':
            ordenacao = campo_ordenacao.asc()
        else:
            ordenacao = campo_ordenacao.desc()
        query = session.query(Requerimento).order_by(ordenacao)
        total = query.count()
        requerimentos = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "requerimentos": [ {
                "id": r.id,
                "numero": r.numero,
                "tipo": r.tipo,
                "motivo": r.motivo,
                "prioridade": r.prioridade,
                "status": r.status,  # CAMPO ESSENCIAL ADICIONADO
                "data_abertura": r.data_abertura.isoformat() if r.data_abertura else None,
                "requerente_nome": r.requerente.nome if r.requerente else "",
                "arvore_endereco": r.arvore.endereco if r.arvore else "",
                # Adicione outros campos necessários para a interface
                "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
                "atualizado_por": r.atualizado_por
            } for r in requerimentos ],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/requerimentos/<int:id>', methods=['PUT'])
@login_required
def atualizar_requerimento(id):
    data = request.json
    session = SessionLocal()
    try:
        requerimento = session.query(Requerimento).get(id)
        if not requerimento:
            return jsonify({"error": "Requerimento não encontrado"}), 404
        
        status_anterior = requerimento.status
        
        # Atualiza apenas campos fornecidos
        if 'status' in data:
            requerimento.status = data['status']
        
        # Campos obrigatórios de auditoria
        requerimento.data_atualizacao = datetime.now()
        requerimento.atualizado_por = current_user.id

        if status_anterior != "Concluído" and requerimento.status == "Concluído":
            # Obter todas as OS associadas a este requerimento
            ordens_servico = requerimento.ordens_servico
            
            # Verificar cada OS associada
            for os in ordens_servico:
                # Verificar se todos requerimentos desta OS estão concluídos
                todos_concluidos = all(
                    req.status == "Concluído" 
                    for req in os.requerimentos
                    if req.id != requerimento.id  # Excluir o próprio requerimento
                )
                
                # Atualizar status da OS
                if todos_concluidos:
                    os.status = "Concluída"
                else:
                    os.status = "Em Andamento"
                
                # Atualizar dados de auditoria da OS
                os.data_atualizacao = datetime.now()
                os.atualizado_por = current_user.id
        
        session.commit()
        return jsonify({
            "message": "Requerimento atualizado com sucesso!",
            "atualizado_por": current_user.nome,
            "data_atualizacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/requerimentos/todos', methods=['GET'])
@login_required
def listar_todos_requerimentos():
    session = SessionLocal()
    try:
        requerimentos = (
            session.query(Requerimento)
            .options(joinedload(Requerimento.arvore))
            .filter(sa.func.lower(Requerimento.status) != 'concluído')
            .order_by(Requerimento.data_abertura.desc())
            .all()
        )
        requerimentos_json = []
        for r in requerimentos:
            arvore = r.arvore
            requerimento_data = {
                "id": r.id,
                "numero": r.numero,
                "tipo": r.tipo,
                "motivo": r.motivo,
                "prioridade": r.prioridade,
                "data_abertura": r.data_abertura.isoformat() if r.data_abertura else None,
                "requerente_nome": r.requerente.nome if r.requerente else "",
                "requerente_telefone": r.requerente.telefone if r.requerente else "",
                "observacao": r.observacao,
                "status": r.status,
                "arvore_id": arvore.id if arvore else None,
                "arvore_latitude": arvore.latitude if arvore else None,
                "arvore_longitude": arvore.longitude if arvore else None,
                "arvore_especie": arvore.especie.nome_popular if arvore and arvore.especie else "",
                "arvore_endereco": arvore.endereco if arvore else "",
                "arvore_bairro": arvore.bairro if arvore else ""
            }
            requerimentos_json.append(requerimento_data)
        return jsonify(requerimentos_json), 200
    except Exception as e:
        print(f"Erro no backend: {str(e)}")
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()