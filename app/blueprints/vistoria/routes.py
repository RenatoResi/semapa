from flask import Blueprint, request, render_template, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from datetime import datetime
from config import SessionLocal
from app.models import Vistoria, VistoriaFoto, Requerimento, Especies
from werkzeug.utils import secure_filename
from app import app
import sqlalchemy as sa
import io

bp = Blueprint('vistoria', __name__)

@bp.route('/vistorias', methods=['GET'])
@login_required
def listar_vistorias():
    session = SessionLocal()
    try:
        vistorias = session.query(Vistoria).options(
            joinedload(Vistoria.requerimento),
            joinedload(Vistoria.user)
        ).all()
        return render_template('vistoria_listar.html', vistorias=vistorias)
    finally:
        session.close()

# Rota para exibir formulário de nova vistoria
@bp.route('/vistorias/nova', methods=['GET'])
@login_required
def nova_vistoria():
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

# Rota para processar criação de nova vistoria
@bp.route('/vistorias', methods=['POST'])
@login_required
def criar_vistoria():
    data = request.form
    files = request.files.getlist('fotos')
    session = SessionLocal()
    
    try:
        # --- Lógica para Espécie ---
        especie_id = None
        nova_especie_popular = data.get('nova_especie_popular')

        if nova_especie_popular:
            # Usuário digitou uma nova espécie
            especie_existente = session.query(Especies).filter(sa.func.lower(Especies.nome_popular) == sa.func.lower(nova_especie_popular)).first()
            if especie_existente:
                especie_id = especie_existente.id
            else:
                # Cria a nova espécie no banco
                nova_especie = Especies(
                    nome_popular=nova_especie_popular,
                    nome_cientifico=data.get('nova_especie_cientifico') or 'Não informado',
                    porte='não informado' # Campo obrigatório, usando valor padrão
                )
                session.add(nova_especie)
                session.flush()  # Para obter o ID antes do commit final
                especie_id = nova_especie.id
        else:
            # Usuário selecionou uma espécie existente
            especie_id_str = data.get('especie_id')
            if especie_id_str:
                especie_id = int(especie_id_str)
        # --- Fim da Lógica para Espécie ---

        vistoria_data = datetime.strptime(data['vistoria_data'], '%Y-%m-%dT%H:%M')
        nova_vistoria = Vistoria(
            requerimento_id=int(data['requerimento_id']),
            vistoria_data=vistoria_data,
            user_id=current_user.id,
            status="Pendente", # ou outro status inicial
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
        
        for file in files:
            if file.filename != '':
                foto = VistoriaFoto(
                    vistoria_id=nova_vistoria.id,
                    arquivo_nome=secure_filename(file.filename),
                    arquivo=file.read()
                )
                session.add(foto)
        
        session.commit()
        flash("Vistoria cadastrada com sucesso!", "success")
        return redirect(url_for('listar_vistorias'))
    except Exception as e:
        session.rollback()
        flash(f"Erro ao cadastrar vistoria: {str(e)}", "error")
        # Redireciona de volta para o formulário, mantendo o requerimento_id se houver
        requerimento_id = data.get('requerimento_id')
        return redirect(url_for('nova_vistoria', requerimento_id=requerimento_id))
    finally:
        session.close()

# Rota para exibir formulário de edição
@bp.route('/vistorias/<int:id>/editar', methods=['GET'])
@login_required
def editar_vistoria(id):
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).options(
            joinedload(Vistoria.fotos)
        ).get(id)
        if not vistoria:
            flash("Vistoria não encontrada", "error")
            return redirect(url_for('listar_vistorias'))
        
        requerimentos = session.query(Requerimento).all()
        especies = session.query(Especies).all()
        return render_template(
            'vistoria_form.html',
            vistoria=vistoria,
            requerimentos=requerimentos,
            especies=especies
        )
    finally:
        session.close()

# Rota para processar atualização de vistoria
@bp.route('/vistorias/<int:id>', methods=['POST'])
@login_required
def atualizar_vistoria(id):
    data = request.form
    files = request.files.getlist('fotos')
    session = SessionLocal()
    
    try:
        vistoria = session.query(Vistoria).get(id)
        if not vistoria:
            flash("Vistoria não encontrada", "error")
            return redirect(url_for('listar_vistorias'))
        
        # --- Lógica para Espécie ---
        especie_id = None
        nova_especie_popular = data.get('nova_especie_popular')

        if nova_especie_popular:
            # Usuário digitou uma nova espécie
            especie_existente = session.query(Especies).filter(sa.func.lower(Especies.nome_popular) == sa.func.lower(nova_especie_popular)).first()
            if especie_existente:
                especie_id = especie_existente.id
            else:
                # Cria a nova espécie no banco
                nova_especie = Especies(
                    nome_popular=nova_especie_popular,
                    nome_cientifico=data.get('nova_especie_cientifico') or 'Não informado',
                    porte='não informado' # Campo obrigatório, usando valor padrão
                )
                session.add(nova_especie)
                session.flush()
                especie_id = nova_especie.id
        else:
            # Usuário selecionou uma espécie existente
            especie_id_str = data.get('especie_id')
            if especie_id_str:
                especie_id = int(especie_id_str)
        # --- Fim da Lógica para Espécie ---

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
        
        # Adicionar novas fotos, se houver
        for file in files:
            if file.filename != '':
                foto = VistoriaFoto(
                    vistoria_id=vistoria.id,
                    arquivo_nome=secure_filename(file.filename),
                    arquivo=file.read()
                )
                session.add(foto)
        
        session.commit()
        flash("Vistoria atualizada com sucesso!", "success")
        return redirect(url_for('editar_vistoria', id=id))
    except Exception as e:
        session.rollback()
        flash(f"Erro ao atualizar vistoria: {str(e)}", "error")
        return redirect(url_for('editar_vistoria', id=id))
    finally:
        session.close()

@bp.route('/vistoria_foto/<int:foto_id>', methods=['GET'])
@login_required
def vistoria_foto(foto_id):
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
        
@bp.route('/vistoria_foto/<int:foto_id>', methods=['DELETE'])
@login_required
def remover_vistoria_foto(foto_id):
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