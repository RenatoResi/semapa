from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from database import SessionLocal, Vistoria, VistoriaFoto, Requerimento, Especies
from sqlalchemy.orm import joinedload
from sqlalchemy import func as sa_func
from datetime import datetime
from werkzeug.utils import secure_filename
from functools import wraps
import io
from routes.decorators import nivel_requerido
from app import cache

vistorias_bp = Blueprint('vistorias', __name__, url_prefix='/vistorias')


# -------------------- FUNÇÕES AUXILIARES --------------------

def processar_especie(data, session):
    """
    Processa a espécie informada no formulário.
    Retorna o especie_id correspondente.
    """
    especie_id = None
    nova_especie_popular = data.get('nova_especie_popular')

    if nova_especie_popular:
        # Usuário digitou uma nova espécie
        especie_existente = session.query(Especies).filter(
            sa_func.lower(Especies.nome_popular) == sa_func.lower(nova_especie_popular)
        ).first()
        
        if especie_existente:
            especie_id = especie_existente.id
        else:
            # Cria a nova espécie no banco
            nova_especie = Especies(
                nome_popular=nova_especie_popular,
                nome_cientifico=data.get('nova_especie_cientifico') or 'Não informado',
                porte='não informado'  # Campo obrigatório, usando valor padrão
            )
            session.add(nova_especie)
            session.flush()  # Para obter o ID antes do commit final
            especie_id = nova_especie.id
    else:
        # Usuário selecionou uma espécie existente
        especie_id_str = data.get('especie_id')
        if especie_id_str:
            especie_id = int(especie_id_str)
    
    return especie_id

def processar_fotos(files, vistoria_id, session):
    """Processa e salva as fotos da vistoria"""
    for file in files:
        if file.filename != '':
            foto = VistoriaFoto(
                vistoria_id=vistoria_id,
                arquivo_nome=secure_filename(file.filename),
                arquivo=file.read()
            )
            session.add(foto)

# -------------------- ROTAS --------------------

@vistorias_bp.route('/', methods=['GET'])
@login_required
@nivel_requerido(1, 2)
@cache.cached(timeout=300)
def listar_vistorias():
    """Lista todas as vistorias cadastradas"""
    session = SessionLocal()
    try:
        vistorias = session.query(Vistoria).options(
            joinedload(Vistoria.requerimento),
            joinedload(Vistoria.user)
        ).all()
        return render_template('vistoria_listar.html', vistorias=vistorias)
    finally:
        session.close()


@vistorias_bp.route('/nova', methods=['GET'])
@login_required
def nova_vistoria():
    """Exibe formulário para nova vistoria"""
    session = SessionLocal()
    try:
        requerimentos = session.query(Requerimento).all()
        especies = session.query(Especies).all()
        requerimento_id = request.args.get('requerimento_id', type=int)
        return render_template(
            'vistoria_form.html',
            requerimentos=requerimentos,
            especies=especies,
            requerimento_id=requerimento_id
        )
    finally:
        session.close()


@vistorias_bp.route('/', methods=['POST'])
@login_required
def criar_vistoria():
    """Processa criação de nova vistoria"""
    data = request.form
    files = request.files.getlist('fotos')
    session = SessionLocal()
    
    try:
        # Processar espécie
        especie_id = processar_especie(data, session)

        # Criar vistoria
        vistoria_data = datetime.strptime(data['vistoria_data'], '%Y-%m-%dT%H:%M')
        nova_vistoria = Vistoria(
            requerimento_id=int(data['requerimento_id']),
            vistoria_data=vistoria_data,
            user_id=current_user.id,
            status="Pendente",
            especie_id=especie_id,
            condicoes=','.join(data.getlist('condicoes[]')),
            conflitos=','.join(data.getlist('conflitos[]')),
            risco_queda=data.get('risco_queda'),
            diagnostico=data.get('diagnostico'),
            acao_recomendada=data.get('acao_recomendada'),
            tipo_poda=','.join(data.getlist('tipo_poda[]')) if data.get('acao_recomendada') == 'poda' else '',
            galhos_cortar=data.get('galhos_cortar'),
            medidas_seguranca=data.get('medidas_seguranca'),
            observacoes_tecnicas=data.get('observacoes_tecnicas')
        )
        session.add(nova_vistoria)
        session.flush()
        
        # Processar fotos
        processar_fotos(files, nova_vistoria.id, session)
        
        session.commit()
        flash("Vistoria cadastrada com sucesso!", "success")
        return redirect(url_for('vistorias.listar_vistorias'))
    except Exception as e:
        session.rollback()
        flash(f"Erro ao cadastrar vistoria: {str(e)}", "error")
        requerimento_id = data.get('requerimento_id')
        return redirect(url_for('vistorias.nova_vistoria', requerimento_id=requerimento_id))
    finally:
        session.close()


@vistorias_bp.route('/<int:id>/editar', methods=['GET'])
@login_required
@nivel_requerido(1, 2)
def editar_vistoria(id):
    """Exibe formulário de edição de vistoria"""
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).options(
            joinedload(Vistoria.fotos),
            joinedload(Vistoria.requerimento),
            joinedload(Vistoria.especie)
        ).get(id)
        
        if not vistoria:
            flash("Vistoria não encontrada", "error")
            return redirect(url_for('vistorias.listar_vistorias'))
        
        # Buscar todos os requerimentos e espécies para os selects
        requerimentos = session.query(Requerimento).all()
        especies = session.query(Especies).all()

        # Processar dados para o template
        vistoria_data = {
            'id': vistoria.id,
            'requerimento_id': vistoria.requerimento_id,
            'vistoria_data': vistoria.vistoria_data,
            'especie_id': vistoria.especie_id,
            'risco_queda': vistoria.risco_queda,
            'diagnostico': vistoria.diagnostico,
            'acao_recomendada': vistoria.acao_recomendada,
            'galhos_cortar': vistoria.galhos_cortar,
            'medidas_seguranca': vistoria.medidas_seguranca,
            'observacoes_tecnicas': vistoria.observacoes_tecnicas,
            'condicoes': vistoria.condicoes.split(',') if vistoria.condicoes else [],
            'conflitos': vistoria.conflitos.split(',') if vistoria.conflitos else [],
            'tipo_poda': vistoria.tipo_poda.split(',') if vistoria.tipo_poda else []
        }
        
        return render_template('vistoria_form.html', 
                             vistoria=vistoria_data,
                             requerimento=vistoria.requerimento,
                             requerimento_id=vistoria.requerimento_id,
                             requerimentos=requerimentos,
                             especies=especies,
                             is_edit=True)
    finally:
        session.close()


@vistorias_bp.route('/<int:id>', methods=['POST'])
@login_required
@nivel_requerido(1, 2)
def atualizar_vistoria(id):
    """Processa atualização de vistoria"""
    data = request.form
    files = request.files.getlist('fotos')
    session = SessionLocal()
    
    try:
        vistoria = session.query(Vistoria).get(id)
        if not vistoria:
            flash("Vistoria não encontrada", "error")
            return redirect(url_for('vistorias.listar_vistorias'))
        
        # Processar espécie
        especie_id = processar_especie(data, session)

        # Atualizar campos da vistoria
        vistoria.vistoria_data = datetime.strptime(data['vistoria_data'], '%Y-%m-%dT%H:%M')
        vistoria.requerimento_id = int(data['requerimento_id'])
        vistoria.especie_id = especie_id
        vistoria.condicoes = ','.join(data.getlist('condicoes[]'))
        vistoria.conflitos = ','.join(data.getlist('conflitos[]'))
        vistoria.risco_queda = data.get('risco_queda')
        vistoria.diagnostico = data.get('diagnostico')
        vistoria.acao_recomendada = data.get('acao_recomendada')
        vistoria.tipo_poda = ','.join(data.getlist('tipo_poda[]')) if data.get('acao_recomendada') == 'poda' else ''
        vistoria.galhos_cortar = data.get('galhos_cortar')
        vistoria.medidas_seguranca = data.get('medidas_seguranca')
        vistoria.observacoes_tecnicas = data.get('observacoes_tecnicas')
        
        # Processar novas fotos
        processar_fotos(files, vistoria.id, session)
        
        session.commit()
        flash("Vistoria atualizada com sucesso!", "success")
        return redirect(url_for('vistorias.editar_vistoria', id=id))
    except Exception as e:
        session.rollback()
        flash(f"Erro ao atualizar vistoria: {str(e)}", "error")
        return redirect(url_for('vistorias.editar_vistoria', id=id))
    finally:
        session.close()


@vistorias_bp.route('/foto/<int:foto_id>', methods=['GET'])
@login_required
@cache.cached(timeout=300)
def vistoria_foto(foto_id):
    """Exibe foto da vistoria"""
    session = SessionLocal()
    try:
        foto = session.query(VistoriaFoto).get(foto_id)
        if not foto:
            return jsonify({"error": "Foto não encontrada"}), 404
        
        return send_file(
            io.BytesIO(foto.arquivo),
            mimetype='image/jpeg',
            download_name=foto.arquivo_nome
        )
    finally:
        session.close()


@vistorias_bp.route('/foto/<int:foto_id>', methods=['DELETE'])
@login_required
def remover_vistoria_foto(foto_id):
    """Remove foto da vistoria"""
    session = SessionLocal()
    try:
        foto = session.query(VistoriaFoto).get(foto_id)
        if not foto:
            return jsonify({"success": False, "error": "Foto não encontrada"}), 404
        
        session.delete(foto)
        session.commit()
        return jsonify({"success": True})
    except Exception as e:
        session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        session.close()
