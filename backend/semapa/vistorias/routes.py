from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from semapa.models import SessionLocal, Vistoria, VistoriaFoto, Requerimento, Especies
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename
from datetime import datetime
import io
import sqlalchemy as sa

vistorias_bp = Blueprint('vistorias', __name__)

@vistorias_bp.route('/vistorias', methods=['GET'])
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

@vistorias_bp.route('/vistorias/nova', methods=['GET'])
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

@vistorias_bp.route('/vistorias', methods=['POST'])
@login_required
def criar_vistoria():
    data = request.form
    files = request.files.getlist('fotos')
    session = SessionLocal()
    try:
        especie_id = None
        nova_especie_popular = data.get('nova_especie_popular')
        if nova_especie_popular:
            especie_existente = session.query(Especies).filter(sa.func.lower(Especies.nome_popular) == sa.func.lower(nova_especie_popular)).first()
            if especie_existente:
                especie_id = especie_existente.id
            else:
                nova_especie = Especies(
                    nome_popular=nova_especie_popular,
                    nome_cientifico=data.get('nova_especie_cientifico') or 'Não informado',
                    porte='não informado'
                )
                session.add(nova_especie)
                session.flush()
                especie_id = nova_especie.id
        else:
            especie_id_str = data.get('especie_id')
            if especie_id_str:
                especie_id = int(especie_id_str)
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
        return redirect(url_for('vistorias.listar_vistorias'))
    except Exception as e:
        session.rollback()
        flash(f"Erro ao cadastrar vistoria: {str(e)}", "error")
        requerimento_id = data.get('requerimento_id')
        return redirect(url_for('vistorias.nova_vistoria', requerimento_id=requerimento_id))
    finally:
        session.close()

@vistorias_bp.route('/vistorias/<int:id>/editar', methods=['GET'])
@login_required
def editar_vistoria(id):
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).options(
            joinedload(Vistoria.fotos)
        ).get(id)
        if not vistoria:
            flash("Vistoria não encontrada", "error")
            return redirect(url_for('vistorias.listar_vistorias'))
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

@vistorias_bp.route('/vistorias/<int:id>', methods=['POST'])
@login_required
def atualizar_vistoria(id):
    data = request.form
    files = request.files.getlist('fotos')
    session = SessionLocal()
    try:
        vistoria = session.query(Vistoria).get(id)
        if not vistoria:
            flash("Vistoria não encontrada", "error")
            return redirect(url_for('vistorias.listar_vistorias'))
        especie_id = None
        nova_especie_popular = data.get('nova_especie_popular')
        if nova_especie_popular:
            especie_existente = session.query(Especies).filter(sa.func.lower(Especies.nome_popular) == sa.func.lower(nova_especie_popular)).first()
            if especie_existente:
                especie_id = especie_existente.id
            else:
                nova_especie = Especies(
                    nome_popular=nova_especie_popular,
                    nome_cientifico=data.get('nova_especie_cientifico') or 'Não informado',
                    porte='não informado'
                )
                session.add(nova_especie)
                session.flush()
                especie_id = nova_especie.id
        else:
            especie_id_str = data.get('especie_id')
            if especie_id_str:
                especie_id = int(especie_id_str)
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
        return redirect(url_for('vistorias.editar_vistoria', id=id))
    except Exception as e:
        session.rollback()
        flash(f"Erro ao atualizar vistoria: {str(e)}", "error")
        return redirect(url_for('vistorias.editar_vistoria', id=id))
    finally:
        session.close()

@vistorias_bp.route('/vistoria_foto/<int:foto_id>', methods=['GET'])
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

@vistorias_bp.route('/vistoria_foto/<int:foto_id>', methods=['DELETE'])
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
