from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import os
from datetime import datetime
from config import SessionLocal
from app.models import Arvore, Especies, Requerente
import sqlalchemy as sa
from simplekml import Kml
from app import app

bp = Blueprint('cadastro', __name__)

# -------------------- Rotas Auxiliares --------------------

@bp.route('/api/especies_autocomplete')
@login_required
def especies_autocomplete():
    termo = request.args.get('q', '').strip()
    session = SessionLocal()
    try:
        query = session.query(Especies)
        if termo:
            termo_like = f"%{termo.lower()}%"
            query = query.filter(
                or_(
                    sa.func.lower(Especies.nome_popular).like(termo_like),
                    sa.func.lower(Especies.nome_cientifico).like(termo_like)
                )
            )
        especies = query.order_by(Especies.nome_popular).limit(20).all()
        return jsonify([
            {
                "id": e.id,
                "nome_popular": e.nome_popular,
                "nome_cientifico": e.nome_cientifico
            }
            for e in especies
        ])
    finally:
        session.close()

@bp.route('/gerar_kml')
@login_required
def gerar_kml():
    session = SessionLocal()
    try:
        arvores = session.execute(
            sa.select(Arvore.id, Arvore.especie, Arvore.latitude, Arvore.longitude)
        ).all()

        kml = Kml(name="Árvores SEMAPA", open=1)

        for id, especie, lat, lon in arvores:
            ponto = kml.newpoint(
                name=especie,
                coords=[(float(lon), float(lat))]
            )
            ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
            ponto.description = f"""
                <![CDATA[
                    <h3>Detalhes da Árvore</h3>
                    <p>ID: {id}</p>
                    <p>Espécie: {especie}</p>
                ]]>
            """
        os.makedirs(os.path.join(app.root_path, 'temp'), exist_ok=True)
        caminho_kml = os.path.join(app.root_path, 'temp', 'arvores.kml')
        kml.save(caminho_kml)

        return send_file(caminho_kml, as_attachment=True)
    finally:
        session.close()

@bp.route('/gerar_kml/<int:arvore_id>')
@login_required
def gerar_kml_arvore(arvore_id):
    session = SessionLocal()
    try:
        arvore = session.query(Arvore).options(
            joinedload(Arvore.especie)
        ).get(arvore_id)
        
        if not arvore:
            return jsonify({"error": "Árvore não encontrada"}), 404

        kml = Kml(name=f"Árvore {arvore.especie}", open=1)
        
        ponto = kml.newpoint(
            name=arvore.especie.nome_popular if arvore.especie else "Não identificada",
            coords=[(float(arvore.longitude), float(arvore.latitude))]
        )
        ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
        ponto.description = f"""
            <![CDATA[
                <h3>Detalhes da Árvore</h3>
                <p>ID: {arvore.id}</p>
                <p>Espécie: {arvore.especie.nome_popular if arvore.especie else "Não identificada"}</p>
                <p>Endereço: {arvore.endereco}</p>
            ]]>
        """
        
        os.makedirs(os.path.join(app.root_path, 'temp'), exist_ok=True)
        caminho_kml = os.path.join(app.root_path, 'temp', f'arvore_{arvore_id}.kml')
        kml.save(caminho_kml)
        return send_file(caminho_kml, as_attachment=True, download_name=f'arvore_{arvore_id}.kml')
    finally:
        session.close()

# -------------------- REQUERENTES --------------------

@bp.route('/requerente', methods=['POST'])
@login_required
def cadastrar_requerente():
    data = request.json
    session = SessionLocal()
    try:
        novo = Requerente(
            nome=data['nome'],
            telefone=data.get('telefone', ''),
            observacao=data.get('observacao', ''),
            criado_por=current_user.id,
            data_criacao=datetime.now()
        )
        session.add(novo)
        session.commit()
        return jsonify({"message": "Requerente cadastrado!", "id": novo.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/requerentes/<int:id>', methods=['PUT'])
@login_required
def atualizar_requerente(id):
    data = request.json
    session = SessionLocal()
    try:
        req = session.query(Requerente).get(id)
        if not req:
            return jsonify({"error": "Não encontrado"}), 404
        req.nome = data.get('nome', req.nome)
        req.telefone = data.get('telefone', req.telefone)
        req.observacao = data.get('observacao', req.observacao)
        req.data_atualizacao = datetime.now()
        req.atualizado_por = current_user.id
        session.commit()
        return jsonify({"message": "Atualizado!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/requerentes', methods=['GET'])
@login_required
def listar_requerentes():
    session = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        query = session.query(Requerente).order_by(Requerente.id.desc())
        total = query.count()
        requerentes = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "requerentes": [ {
                "id": r.id,
                "nome": r.nome,
                "telefone": r.telefone,
                "observacao": r.observacao,
                "data_criacao": r.data_criacao.isoformat() if r.data_criacao else None,
                "criado_por": r.criado_por,
                "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
                "atualizado_por": r.atualizado_por
            } for r in requerentes ],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/requerentes/todos', methods=['GET'])
@login_required
def listar_todos_requerentes():
    session = SessionLocal()
    try:
        requerentes = session.query(Requerente).order_by(Requerente.id.desc()).all()
        return jsonify([{
            "id": r.id,
            "nome": r.nome,
            "telefone": r.telefone,
            "observacao": r.observacao,
            "data_criacao": r.data_criacao.isoformat() if r.data_criacao else None,
            "criado_por": r.criado_por,
            "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
            "atualizado_por": r.atualizado_por
        } for r in requerentes]), 200
    finally:
        session.close()

@bp.route('/api/requerente/existe', methods=['GET'])
@login_required
def requerente_existe():
    nome = request.args.get('nome')
    with SessionLocal() as session:
        requerente = session.query(Requerente).filter_by(nome=nome).first()
        if requerente:
            return jsonify({"exists": True, "id": requerente.id})
        else:
            return jsonify({"exists": False})

# -------------------- ÁRVORES --------------------

@bp.route('/arvores/todos', methods=['GET'])
@login_required
def listar_todas_arvores():
    session = SessionLocal()
    try:
        arvores = session.query(Arvore).options(joinedload(Arvore.especie)).order_by(Arvore.id.desc()).all()
        return jsonify([{
            "id": a.id,
            "especie": a.especie.nome_popular if a.especie else "",
            "endereco": a.endereco,
            "bairro": a.bairro,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "data_plantio": a.data_plantio.isoformat() if a.data_plantio else None,
            "foto": a.foto,
            "observacao": a.observacao,
            "data_criacao": a.data_criacao.isoformat() if a.data_criacao else None,
            "criado_por": a.criado_por,
            "data_atualizacao": a.data_atualizacao.isoformat() if a.data_atualizacao else None,
            "atualizado_por": a.atualizado_por
        } for a in arvores]), 200
    finally:
        session.close()

@bp.route('/arvores', methods=['POST'])
@login_required
def cadastrar_arvore():
    data = request.json
    session = SessionLocal()
    try:
        # --- Lógica para Espécie ---
        especie_id = None
        nova_especie_popular = data.get('nova_especie_popular') # Supondo que o frontend envie isso

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
        elif data.get('especie_id'):
            especie_id = int(data.get('especie_id'))
        # --- Fim da Lógica para Espécie ---

        data_plantio = None
        if data.get('data_plantio'):
            data_plantio = datetime.strptime(data['data_plantio'], '%Y-%m-%d')
        nova = Arvore(
            especie_id=especie_id,
            endereco=data.get('endereco', ''),
            bairro=data.get('bairro', ''),
            latitude=data['latitude'] or None,
            longitude=data['longitude'] or None,
            data_plantio=data_plantio,
            foto=data.get('foto', ''),
            observacao=data.get('observacao', ''),
            criado_por=current_user.id,
            data_criacao=datetime.now()
        )
        session.add(nova)
        session.commit()
        return jsonify({"message": "Árvore cadastrada!", "id": nova.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/arvores/<int:id>', methods=['PUT'])
@login_required
def atualizar_arvore(id):
    data = request.json
    session = SessionLocal()
    try:
        arvore = session.query(Arvore).get(id)
        if not arvore:
            return jsonify({"error": "Árvore não encontrada"}), 404
        
        # --- Lógica para Espécie ---
        nova_especie_popular = data.get('nova_especie_popular')
        if nova_especie_popular:
            especie_existente = session.query(Especies).filter(sa.func.lower(Especies.nome_popular) == sa.func.lower(nova_especie_popular)).first()
            if especie_existente:
                arvore.especie_id = especie_existente.id
            else:
                nova_especie = Especies(
                    nome_popular=nova_especie_popular,
                    nome_cientifico=data.get('nova_especie_cientifico') or 'Não informado',
                    porte='não informado'
                )
                session.add(nova_especie)
                session.flush()
                arvore.especie_id = nova_especie.id
        elif data.get('especie_id'):
            arvore.especie_id = int(data.get('especie_id'))
        # --- Fim da Lógica para Espécie ---

        arvore.endereco = data.get('endereco', arvore.endereco)
        arvore.bairro = data.get('bairro', arvore.bairro)
        arvore.latitude = data.get('latitude', arvore.latitude)
        arvore.longitude = data.get('longitude', arvore.longitude)
        if data.get('data_plantio'):
            arvore.data_plantio = datetime.strptime(data['data_plantio'], '%Y-%m-%d')
        arvore.foto = data.get('foto', arvore.foto)
        arvore.observacao = data.get('observacao', arvore.observacao)
        arvore.data_atualizacao = datetime.now()
        arvore.atualizado_por = current_user.id
        session.commit()
        return jsonify({"message": "Árvore atualizada!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/api/sugestoes/bairros')
@login_required
def sugestoes_bairros():
    session = SessionLocal()
    try:
        query = request.args.get('query', '').lower()
        bairros = (
            session.query(Arvore.bairro)
            .filter(Arvore.bairro.ilike(f'%{query}%'))
            .distinct()
            .limit(10)
            .all()
        )
        sugestoes = [b[0] for b in bairros if b[0]]
        return jsonify(sugestoes)
    finally:
        session.close()

@bp.route('/api/sugestoes/enderecos')
@login_required
def sugestoes_enderecos():
    session = SessionLocal()
    try:
        query = request.args.get('query', '').lower()
        enderecos = (
            session.query(Arvore.endereco)
            .filter(Arvore.endereco.ilike(f'%{query}%'))
            .distinct()
            .limit(10)
            .all()
        )
        sugestoes = [e[0] for e in enderecos if e[0]]
        return jsonify(sugestoes)
    finally:
        session.close()

@bp.route('/arvores', methods=['GET'])
@login_required
def listar_arvores():
    session = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        query = session.query(Arvore).order_by(Arvore.id.desc())
        total = query.count()
        arvores = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "arvores": [ {
                "id": a.id,
                "especie": a.especie.nome_popular if a.especie else "",
                "endereco": a.endereco,
                "bairro": a.bairro,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "data_plantio": a.data_plantio.isoformat() if a.data_plantio else None,
                "foto": a.foto,
                "observacao": a.observacao,
                "data_criacao": a.data_criacao.isoformat() if a.data_criacao else None,
                "criado_por": a.criado_por,
                "data_atualizacao": a.data_atualizacao.isoformat() if a.data_atualizacao else None,
                "atualizado_por": a.atualizado_por
            } for a in arvores ],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
