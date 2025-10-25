from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required, current_user
from database import SessionLocal, Arvore, Especies
from sqlalchemy.orm import joinedload
from sqlalchemy import func as sa_func
from datetime import datetime
from simplekml import Kml
import os
import sqlalchemy as sa

arvores_bp = Blueprint('arvores', __name__)

# -------------------- FUNÇÕES AUXILIARES --------------------

def serializar_arvore(a):
    """Serializa árvore com todos os dados"""
    return {
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
    }

def processar_especie_arvore(data, session):
    """
    Processa a espécie informada no formulário (nova ou existente).
    Retorna o especie_id correspondente.
    """
    especie_id = None
    nova_especie_popular = data.get('nova_especie_popular')

    if nova_especie_popular:
        # Buscar se espécie já existe (case-insensitive)
        especie_existente = session.query(Especies).filter(
            sa_func.lower(Especies.nome_popular) == sa_func.lower(nova_especie_popular)
        ).first()
        
        if especie_existente:
            especie_id = especie_existente.id
        else:
            # Criar nova espécie
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
    
    return especie_id

def parsear_data_plantio(data_str):
    """Converte string de data para datetime, retorna None se inválida"""
    if data_str:
        try:
            return datetime.strptime(data_str, '%Y-%m-%d')
        except Exception:
            return None
    return None

# -------------------- ROTAS --------------------

@arvores_bp.route('/arvores/todos', methods=['GET'])
@login_required
def listar_todas_arvores():
    """Lista todas as árvores cadastradas"""
    session = SessionLocal()
    try:
        arvores = session.query(Arvore).options(
            joinedload(Arvore.especie)
        ).order_by(Arvore.id.desc()).all()
        
        return jsonify([serializar_arvore(a) for a in arvores]), 200
    finally:
        session.close()


@arvores_bp.route('/arvores', methods=['GET'])
@login_required
def listar_arvores():
    """Lista árvores com paginação"""
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
            "arvores": [serializar_arvore(a) for a in arvores],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()


@arvores_bp.route('/arvores', methods=['POST'])
@login_required
def cadastrar_arvore():
    """Cadastra nova árvore"""
    data = request.json
    session = SessionLocal()
    try:
        # Processar espécie
        especie_id = processar_especie_arvore(data, session)

        # Parsear data de plantio
        data_plantio = parsear_data_plantio(data.get('data_plantio'))
        
        # Criar nova árvore
        nova = Arvore(
            especie_id=especie_id,
            endereco=data.get('endereco', ''),
            bairro=data.get('bairro', ''),
            latitude=data.get('latitude') or None,
            longitude=data.get('longitude') or None,
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


@arvores_bp.route('/arvores/<int:id>', methods=['PUT'])
@login_required
def atualizar_arvore(id):
    """Atualiza dados de uma árvore existente"""
    data = request.json
    session = SessionLocal()
    try:
        arvore = session.query(Arvore).get(id)
        if not arvore:
            return jsonify({"error": "Árvore não encontrada"}), 404
        
        # Processar espécie
        nova_especie_popular = data.get('nova_especie_popular')
        if nova_especie_popular:
            especie_existente = session.query(Especies).filter(
                sa_func.lower(Especies.nome_popular) == sa_func.lower(nova_especie_popular)
            ).first()
            
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
        
        # Atualizar campos
        arvore.endereco = data.get('endereco', arvore.endereco)
        arvore.bairro = data.get('bairro', arvore.bairro)
        arvore.latitude = data.get('latitude', arvore.latitude)
        arvore.longitude = data.get('longitude', arvore.longitude)
        
        # Parsear data de plantio
        if data.get('data_plantio'):
            arvore.data_plantio = parsear_data_plantio(data.get('data_plantio'))
        
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


@arvores_bp.route('/api/sugestoes/bairros', methods=['GET'])
@login_required
def sugestoes_bairros():
    """API para sugestões de bairros durante digitação"""
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


@arvores_bp.route('/api/sugestoes/enderecos', methods=['GET'])
@login_required
def sugestoes_enderecos():
    """API para sugestões de endereços durante digitação"""
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


@arvores_bp.route('/gerar_kml', methods=['GET'])
@login_required
def gerar_kml():
    """Gera arquivo KML com todas as árvores cadastradas"""
    session = SessionLocal()
    try:
        arvores = session.execute(
            sa.select(Arvore.id, Arvore.endereco, Arvore.latitude, Arvore.longitude)
            .join(Especies, Arvore.especie_id == Especies.id, isouter=True)
            .add_columns(Especies.nome_popular.label('especie'))
        ).all()

        kml = Kml(name="Árvores SEMAPA", open=1)

        for arvore in arvores:
            if arvore.latitude and arvore.longitude:
                ponto = kml.newpoint(
                    name=arvore.especie or "Não identificada",
                    coords=[(float(arvore.longitude), float(arvore.latitude))]
                )
                ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
                ponto.description = f"""
                    <![CDATA[
                        <h3>Detalhes da Árvore</h3>
                        <p>ID: {arvore.id}</p>
                        <p>Espécie: {arvore.especie or "Não identificada"}</p>
                        <p>Endereço: {arvore.endereco}</p>
                    ]]>
                """

        # Criar diretório temporário se não existir
        from flask import current_app
        os.makedirs(os.path.join(current_app.root_path, 'temp'), exist_ok=True)
        caminho_kml = os.path.join(current_app.root_path, 'temp', 'arvores.kml')
        kml.save(caminho_kml)

        return send_file(caminho_kml, as_attachment=True)
    finally:
        session.close()


@arvores_bp.route('/gerar_kml/<int:arvore_id>', methods=['GET'])
@login_required
def gerar_kml_arvore(arvore_id):
    """Gera arquivo KML para uma árvore específica"""
    session = SessionLocal()
    try:
        arvore = session.query(Arvore).options(
            joinedload(Arvore.especie)
        ).get(arvore_id)
        
        if not arvore:
            return jsonify({"error": "Árvore não encontrada"}), 404

        if not (arvore.latitude and arvore.longitude):
            return jsonify({"error": "Árvore sem coordenadas"}), 400

        kml = Kml(name=f"Árvore {arvore.especie.nome_popular if arvore.especie else 'Não identificada'}", open=1)
        
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
                <p>Bairro: {arvore.bairro}</p>
            ]]>
        """
        
        from flask import current_app
        os.makedirs(os.path.join(current_app.root_path, 'temp'), exist_ok=True)
        caminho_kml = os.path.join(current_app.root_path, 'temp', f'arvore_{arvore_id}.kml')
        kml.save(caminho_kml)
        
        return send_file(caminho_kml, as_attachment=True, download_name=f'arvore_{arvore_id}.kml')
    finally:
        session.close()
