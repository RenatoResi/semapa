from flask import Blueprint, request, jsonify, render_template, abort, send_file
import mimetypes
import io
from flask_login import login_required, current_user
from database import SessionLocal, Requerimento, Vistoria, VistoriaFoto, Tarefa, Arvore, Requerente, Especies
from sqlalchemy.orm import joinedload
from sqlalchemy import func as sa_func
from datetime import datetime

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
        "data_conclusao": r.data_conclusao.isoformat() if r.data_conclusao else None,
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
        "data_conclusao": r.data_conclusao.isoformat() if r.data_conclusao else None,
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
        
        # Obter IDs dos requerimentos que têm vistoria e mapear para o id da vistoria (mais eficiente)
        requerimentos_serializados = []
        if requerimentos:
            req_ids = [r.id for r in requerimentos]
            rows = session.query(Vistoria.requerimento_id, Vistoria.id).filter(Vistoria.requerimento_id.in_(req_ids)).all()
            requerimento_ids_com_vistoria = {req_id for req_id, _ in rows}
            vistoria_map = {req_id: vist_id for req_id, vist_id in rows}
        else:
            requerimento_ids_com_vistoria = set()
            vistoria_map = {}

        # Serializar com informação de vistoria (inclui campo 'vistoria_id' quando disponível)
        for r in requerimentos:
            requerimento_data = serializar_requerimento_basico(r)
            requerimento_data['tem_vistoria'] = r.id in requerimento_ids_com_vistoria
            requerimento_data['vistoria_id'] = vistoria_map.get(r.id)
            requerimentos_serializados.append(requerimento_data)
        
        return jsonify({
            "requerimentos": requerimentos_serializados,
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
        if 'numero' in data:
            requerimento.numero = data['numero']
        if 'tipo' in data:
            requerimento.tipo = data['tipo']
        if 'motivo' in data:
            requerimento.motivo = data['motivo']
        if 'prioridade' in data:
            requerimento.prioridade = data['prioridade']
        if 'observacao' in data:
            requerimento.observacao = data['observacao']
        if 'data_abertura' in data and data['data_abertura']:
            try:
                requerimento.data_abertura = datetime.strptime(data['data_abertura'], '%Y-%m-%d')
            except:
                pass
        if 'data_conclusao' in data and data['data_conclusao']:
            try:
                requerimento.data_conclusao = datetime.strptime(data['data_conclusao'], '%Y-%m-%dT%H:%M')
            except:
                pass
        elif 'data_conclusao' in data and not data['data_conclusao']:
            requerimento.data_conclusao = None
        
        # Campos obrigatórios de auditoria
        requerimento.data_atualizacao = datetime.now()
        requerimento.atualizado_por = current_user.id

        # # Atualizar ordens de serviço se status mudou para Concluído
        # if status_anterior != "Concluído" and requerimento.status == "Concluído":
        #     requerimento.data_conclusao = datetime.now()
        #     atualizar_status_ordens_servico(requerimento, session)
        
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
        
        # obter ids e mapear para id da vistoria (se houver)
        requerimentos_json = []
        ids = [r.id for r in requerimentos]
        if ids:
            rows = session.query(Vistoria.requerimento_id, Vistoria.id).filter(Vistoria.requerimento_id.in_(ids)).all()
            requerimento_ids_com_vistoria = {req_id for req_id, _ in rows}
            vistoria_map = {req_id: vist_id for req_id, vist_id in rows}
        else:
            requerimento_ids_com_vistoria = set()
            vistoria_map = {}

        for r in requerimentos:
            obj = serializar_requerimento_completo(r)
            obj['tem_vistoria'] = r.id in requerimento_ids_com_vistoria
            obj['vistoria_id'] = vistoria_map.get(r.id)
            requerimentos_json.append(obj)
        return jsonify(requerimentos_json), 200
    except Exception as e:
        print(f"Erro no backend: {str(e)}")
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()


@requerimentos_bp.route('/requerimentos/concluidos', methods=['GET'])
@login_required
def listar_requerimentos_concluidos():
    """Lista todos os requerimentos concluídos com dados completos"""
    session = SessionLocal()
    try:
        order_by = request.args.get('order_by', 'data_conclusao')
        direction = request.args.get('direction', 'desc').lower()
        
        # Obter campo de ordenação
        campos_validos = obter_campos_ordenacao()
        campo_ordenacao = campos_validos.get(order_by, Requerimento.data_conclusao)
        ordenacao = campo_ordenacao.asc() if direction == 'asc' else campo_ordenacao.desc()
        
        requerimentos = (
            session.query(Requerimento)
            .options(joinedload(Requerimento.arvore))
            .filter(sa_func.lower(Requerimento.status) == 'concluído')
            .order_by(ordenacao)
            .all()
        )

        # obter ids e mapear para id da vistoria (se houver)
        requerimentos_json = []
        ids = [r.id for r in requerimentos]
        if ids:
            rows = session.query(Vistoria.requerimento_id, Vistoria.id).filter(Vistoria.requerimento_id.in_(ids)).all()
            requerimento_ids_com_vistoria = {req_id for req_id, _ in rows}
            vistoria_map = {req_id: vist_id for req_id, vist_id in rows}
        else:
            requerimento_ids_com_vistoria = set()
            vistoria_map = {}

        for r in requerimentos:
            data = serializar_requerimento_completo(r)
            data['tem_vistoria'] = r.id in requerimento_ids_com_vistoria
            data['vistoria_id'] = vistoria_map.get(r.id)
            requerimentos_json.append(data)
        
        return jsonify(requerimentos_json), 200
    except Exception as e:
        print(f"Erro no backend: {str(e)}")
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()

@requerimentos_bp.route('/requerimentos/<int:id>/vistoria', methods=['POST'])
@login_required
def cadastrar_vistoria(id):
    """Cadastra uma nova vistoria para um requerimento"""
    data = request.json
    session = SessionLocal()
    try:
        requerimento = session.query(Requerimento).get(id)
        if not requerimento:
            return jsonify({"error": "Requerimento não encontrado"}), 404
        
        nova_vistoria = Vistoria(
            requerimento_id=requerimento.id,
            data_vistoria=datetime.strptime(data['data_vistoria'], '%Y-%m-%d'),
            responsavel_id=current_user.id,
            observacao=data.get('observacao', ''),
            criado_por=current_user.id,
            data_criacao=datetime.now()
        )
        session.add(nova_vistoria)
        session.commit()
        
        return jsonify({"message": "Vistoria cadastrada!", "id": nova_vistoria.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/vistoria/<int:id>', methods=['GET'])
@login_required
def obter_vistoria(id):
    """Obtém os detalhes de uma vistoria específica"""
    session = SessionLocal()
    try:
        vistoria = (
            session.query(Vistoria)
            .options(joinedload(Vistoria.requerimento))
            .filter(Vistoria.id == id)
            .first()
        )
        if not vistoria:
            return jsonify({"error": "Vistoria não encontrada"}), 404
        
        # Serializar dados da vistoria
        vistoria_data = {
            "id": vistoria.id,
            "requerimento_id": vistoria.requerimento_id,
            "data_vistoria": vistoria.data_vistoria.isoformat() if vistoria.data_vistoria else None,
            "responsavel_id": vistoria.responsavel_id,
            "observacao": vistoria.observacao,
            "criado_por": vistoria.criado_por,
            "data_criacao": vistoria.data_criacao.isoformat() if vistoria.data_criacao else None
        }
        
        return jsonify(vistoria_data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/vistoria/<int:id>/fotos', methods=['POST'])
@login_required
def cadastrar_foto_vistoria(id):
    """Cadastra uma nova foto para uma vistoria"""
    files = request.files.getlist('fotos')
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).get(id)
        if not vistoria:
            return jsonify({"error": "Vistoria não encontrada"}), 404
        
        # Verificar se a vistoria já possui fotos cadastradas
        if vistoria.fotos:
            return jsonify({"error": "Vistoria já possui fotos cadastradas"}), 400
        
        # Salvar cada foto enviada
        for file in files:
            # Criar objeto de foto
            nova_foto = VistoriaFoto(
                vistoria_id=vistoria.id,
                nome_arquivo=file.filename,
                tipo_conteudo=file.content_type,
                tamanho=file.content_length,
                criado_por=current_user.id,
                data_criacao=datetime.now()
            )
            # Ler conteúdo da foto e atribuir a coluna 'conteudo'
            nova_foto.conteudo = file.read()
            session.add(nova_foto)
        
        session.commit()
        return jsonify({"message": "Fotos cadastradas com sucesso!"}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/vistoria/<int:id>/fotos', methods=['GET'])
@login_required
def listar_fotos_vistoria(id):
    """Lista as fotos de uma vistoria"""
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).get(id)
        if not vistoria:
            return jsonify({"error": "Vistoria não encontrada"}), 404
        
        # Obter fotos da vistoria
        fotos = (
            session.query(VistoriaFoto)
            .filter(VistoriaFoto.vistoria_id == vistoria.id)
            .all()
        )
        
        # Serializar dados das fotos
        fotos_serializadas = [
            {
                "id": foto.id,
                "nome_arquivo": foto.nome_arquivo,
                "tipo_conteudo": foto.tipo_conteudo,
                "tamanho": foto.tamanho,
                "data_criacao": foto.data_criacao.isoformat() if foto.data_criacao else None
            }
            for foto in fotos
        ]
        
        return jsonify(fotos_serializadas), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/foto/<int:id>', methods=['GET'])
@login_required
def obter_foto(id):
    """Retorna o conteúdo binário da foto da vistoria (coluna 'arquivo' na tabela)."""
    session = SessionLocal()
    try:
        foto = session.query(VistoriaFoto).get(id)
        if not foto:
            return ("Foto não encontrada", 404)

        # Suporta tanto nomes antigos quanto os atuais (fallback)
        arquivo_bytes = getattr(foto, 'arquivo', None) or getattr(foto, 'conteudo', None)
        if not arquivo_bytes:
            return ("Arquivo da foto vazio", 404)

        filename = getattr(foto, 'arquivo_nome', None) or getattr(foto, 'nome_arquivo', None) or f'foto_{id}.jpg'

        # Tenta usar tipo salvo em DB, senão deduz pelo nome do arquivo, senão fallback para jpeg
        tipo = getattr(foto, 'tipo_conteudo', None)
        if not tipo:
            tipo, _ = mimetypes.guess_type(filename)
        if not tipo:
            tipo = 'image/jpeg'

        # Serve inline (não como attachment) para facilitar exibição no browser
        return send_file(
            io.BytesIO(arquivo_bytes),
            mimetype=tipo,
            as_attachment=False,
            download_name=filename
        )
    except Exception as e:
        session.rollback()
        return (f"Erro ao obter foto: {str(e)}", 500)
    finally:
        session.close()


@requerimentos_bp.route('/vistoria/<int:id>', methods=['PUT'])
@login_required
def atualizar_vistoria(id):
    """Atualiza dados de uma vistoria"""
    data = request.json
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).get(id)
        if not vistoria:
            return jsonify({"error": "Vistoria não encontrada"}), 404
        
        # Atualiza apenas campos fornecidos
        if 'data_vistoria' in data:
            vistoria.data_vistoria = datetime.strptime(data['data_vistoria'], '%Y-%m-%d')
        if 'observacao' in data:
            vistoria.observacao = data['observacao']
        
        # Campos obrigatórios de auditoria
        vistoria.data_atualizacao = datetime.now()
        vistoria.atualizado_por = current_user.id

        session.commit()
        return jsonify({
            "message": "Vistoria atualizada com sucesso!",
            "atualizado_por": current_user.nome,
            "data_atualizacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/vistoria/<int:id>/foto/<int:foto_id>', methods=['DELETE'])
@login_required
def remover_foto_vistoria(id, foto_id):
    """Remove uma foto de uma vistoria"""
    session = SessionLocal()
    try:
        foto = session.query(VistoriaFoto).filter(VistoriaFoto.id == foto_id, VistoriaFoto.vistoria_id == id).first()
        if not foto:
            return jsonify({"error": "Foto não encontrada"}), 404
        
        # Remover foto
        session.delete(foto)
        session.commit()
        return jsonify({"message": "Foto removida com sucesso!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/vistoria/<int:id>', methods=['DELETE'])
@login_required
def remover_vistoria(id):
    """Remove uma vistoria e suas fotos associadas"""
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).get(id)
        if not vistoria:
            return jsonify({"error": "Vistoria não encontrada"}), 404
        
        # Remover fotos associadas
        for foto in vistoria.fotos:
            session.delete(foto)
        
        # Remover vistoria
        session.delete(vistoria)
        session.commit()
        return jsonify({"message": "Vistoria removida com sucesso!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/tarefas', methods=['POST'])
@login_required
def cadastrar_tarefa():
    """Cadastra uma nova tarefa"""
    data = request.json
    session = SessionLocal()
    try:
        nova_tarefa = Tarefa(
            requerimento_id=data['requerimento_id'],
            descricao=data['descricao'],
            responsavel_id=data.get('responsavel_id'),
            data_limite=datetime.strptime(data['data_limite'], '%Y-%m-%d'),
            status=data.get('status', 'Pendente'),
            criado_por=current_user.id,
            data_criacao=datetime.now()
        )
        session.add(nova_tarefa)
        session.commit()
        return jsonify({"message": "Tarefa cadastrada!", "id": nova_tarefa.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/tarefas/<int:id>', methods=['PUT'])
@login_required
def atualizar_tarefa(id):
    """Atualiza dados de uma tarefa"""
    data = request.json
    session = SessionLocal()
    try:
        tarefa = session.query(Tarefa).get(id)
        if not tarefa:
            return jsonify({"error": "Tarefa não encontrada"}), 404
        
        # Atualiza apenas campos fornecidos
        if 'status' in data:
            tarefa.status = data['status']
        if 'responsavel_id' in data:
            tarefa.responsavel_id = data['responsavel_id']
        
        # Campos obrigatórios de auditoria
        tarefa.data_atualizacao = datetime.now()
        tarefa.atualizado_por = current_user.id

        session.commit()
        return jsonify({
            "message": "Tarefa atualizada com sucesso!",
            "atualizado_por": current_user.nome,
            "data_atualizacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/tarefas/<int:id>', methods=['DELETE'])
@login_required
def remover_tarefa(id):
    """Remove uma tarefa"""
    session = SessionLocal()
    try:
        tarefa = session.query(Tarefa).get(id)
        if not tarefa:
            return jsonify({"error": "Tarefa não encontrada"}), 404
        
        # Remover tarefa
        session.delete(tarefa)
        session.commit()
        return jsonify({"message": "Tarefa removida com sucesso!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()



@requerimentos_bp.route('/especies', methods=['POST'])
@login_required
def cadastrar_especie():
    """Cadastra uma nova espécie"""
    data = request.json
    session = SessionLocal()
    try:
        nova_especie = Especies(
            nome_cientifico=data['nome_cientifico'],
            nome_popular=data.get('nome_popular', ''),
            familia=data.get('familia', ''),
            genero=data.get('genero', ''),
            ordem=data.get('ordem', ''),
            classe=data.get('classe', ''),
            reino=data.get('reino', ''),
            dados_adicionais=data.get('dados_adicionais', ''),
            status=data.get('status', 'Ativa'),
            criado_por=current_user.id,
            data_criacao=datetime.now()
        )
        session.add(nova_especie)
        session.commit()
        return jsonify({"message": "Espécie cadastrada!", "id": nova_especie.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/especies/<int:id>', methods=['PUT'])
@login_required
def atualizar_especie(id):
    """Atualiza dados de uma espécie"""
    data = request.json
    session = SessionLocal()
    try:
        especie = session.query(Especies).get(id)
        if not especie:
            return jsonify({"error": "Espécie não encontrada"}), 404
        
        # Atualiza apenas campos fornecidos
        if 'status' in data:
            especie.status = data['status']
        
        # Campos obrigatórios de auditoria
        especie.data_atualizacao = datetime.now()
        especie.atualizado_por = current_user.id

        session.commit()
        return jsonify({
            "message": "Espécie atualizada com sucesso!",
            "atualizado_por": current_user.nome,
            "data_atualizacao": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@requerimentos_bp.route('/especies/<int:id>', methods=['DELETE'])
@login_required
def remover_especie(id):
    """Remove uma espécie"""
    session = SessionLocal()
    try:
        especie = session.query(Especies).get(id)
        if not especie:
            return jsonify({"error": "Espécie não encontrada"}), 404
        
        # Remover espécie
        session.delete(especie)
        session.commit()
        return jsonify({"message": "Espécie removida com sucesso!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
