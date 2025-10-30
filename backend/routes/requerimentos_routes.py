from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from database import SessionLocal, Requerimento, Arvore
from sqlalchemy.orm import joinedload
from sqlalchemy import func as sa_func
from datetime import datetime
from app import cache

# -------------------- BLUEPRINT --------------------   

requerimentos_bp = Blueprint('requerimentos', __name__)

# -------------------- FUNÇÕES AUXILIARES --------------------

def serializar_requerimento_basico(r):
    """Serializa requerimento com dados básicos para listagem paginada"""
    return {
        "id": r.id,
        "numero": r.numero,
        "tipo": r.tipo,
        "motivo": r.motivo,
        "prioridade": r.prioridade,
        "status": r.status,
        "data_abertura": r.data_abertura.isoformat() if r.data_abertura else None,
        "requerente_nome": r.requerente.nome if r.requerente else "",
        "arvore_endereco": r.arvore.endereco if r.arvore else "",
        "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
        "atualizado_por": r.atualizado_por
    }

def serializar_requerimento_completo(r):
    """Serializa requerimento com todos os dados incluindo árvore e localização"""
    arvore = r.arvore
    return {
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

def atualizar_status_ordens_servico(requerimento, session):
    """Atualiza status das ordens de serviço associadas quando requerimento é concluído"""
    ordens_servico = requerimento.ordens_servico
    
    for os in ordens_servico:
        # Verificar se todos requerimentos desta OS estão concluídos
        todos_concluidos = all(
            req.status == "Concluído" 
            for req in os.requerimentos
            if req.id != requerimento.id
        )
        
        # Atualizar status da OS
        os.status = "Concluída" if todos_concluidos else "Em Andamento"
        os.data_atualizacao = datetime.now()
        os.atualizado_por = current_user.id

def obter_campos_ordenacao():
    """Retorna dicionário de campos válidos para ordenação"""
    return {
        'id': Requerimento.id,
        'numero': Requerimento.numero,
        'tipo': Requerimento.tipo,
        'motivo': Requerimento.motivo,
        'prioridade': Requerimento.prioridade,
        'status': Requerimento.status,
        'data_abertura': Requerimento.data_abertura,
        'data_atualizacao': Requerimento.data_atualizacao
    }

# -------------------- ROTAS --------------------

@requerimentos_bp.route('/requerimento', methods=['POST'])
@login_required
def cadastrar_requerimento():
    """Cadastra novo requerimento"""
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


@requerimentos_bp.route('/requerimentos', methods=['GET'])
@login_required
@cache.cached(timeout=300)
def listar_requerimentos():
    """Lista requerimentos com paginação e ordenação"""
    session = SessionLocal()
    try:
        # Parâmetros de paginação e ordenação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        order_by = request.args.get('order_by', 'id')
        direction = request.args.get('direction', 'desc').lower()
        
        # Obter campo de ordenação
        campos_validos = obter_campos_ordenacao()
        campo_ordenacao = campos_validos.get(order_by, Requerimento.id)
        ordenacao = campo_ordenacao.asc() if direction == 'asc' else campo_ordenacao.desc()
        
        # Query com ordenação
        query = session.query(Requerimento).order_by(ordenacao)
        total = query.count()
        
        # Paginação
        requerimentos = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        
        return jsonify({
            "requerimentos": [serializar_requerimento_basico(r) for r in requerimentos],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/requerimentos/<int:id>', methods=['PUT'])
@login_required
def atualizar_requerimento(id):
    """Atualiza dados de um requerimento"""
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

        # Atualizar ordens de serviço se status mudou para Concluído
        if status_anterior != "Concluído" and requerimento.status == "Concluído":
            atualizar_status_ordens_servico(requerimento, session)
        
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


@requerimentos_bp.route('/requerimentos/todos', methods=['GET'])
@login_required
@cache.cached(timeout=300)
def listar_todos_requerimentos():
    """Lista todos os requerimentos não concluídos com dados completos"""
    session = SessionLocal()
    try:
        requerimentos = (
            session.query(Requerimento)
            .options(joinedload(Requerimento.arvore))
            .filter(sa_func.lower(Requerimento.status) != 'concluído')
            .order_by(Requerimento.data_abertura.desc())
            .all()
        )
        
        requerimentos_json = [serializar_requerimento_completo(r) for r in requerimentos]
        return jsonify(requerimentos_json), 200
    except Exception as e:
        print(f"Erro no backend: {str(e)}")
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()


@requerimentos_bp.route('/requerimentos/concluidos', methods=['GET'])
@login_required
@cache.cached(timeout=300)
def listar_requerimentos_concluidos():
    """Lista todos os requerimentos concluídos com dados completos"""
    session = SessionLocal()
    try:
        order_by = request.args.get('order_by', 'data_atualizacao')
        direction = request.args.get('direction', 'desc').lower()
        
        # Obter campo de ordenação
        campos_validos = obter_campos_ordenacao()
        campo_ordenacao = campos_validos.get(order_by, Requerimento.data_atualizacao)
        ordenacao = campo_ordenacao.asc() if direction == 'asc' else campo_ordenacao.desc()
        
        requerimentos = (
            session.query(Requerimento)
            .options(joinedload(Requerimento.arvore))
            .filter(sa_func.lower(Requerimento.status) == 'concluído')
            .order_by(ordenacao)
            .all()
        )
        
        requerimentos_json = []
        for r in requerimentos:
            data = serializar_requerimento_completo(r)
            # Adicionar data de conclusão
            data['data_conclusao'] = r.data_atualizacao.isoformat() if r.data_atualizacao else None
            requerimentos_json.append(data)
        
        return jsonify(requerimentos_json), 200
    except Exception as e:
        print(f"Erro no backend: {str(e)}")
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()
