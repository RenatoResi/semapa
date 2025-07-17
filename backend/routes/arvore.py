from flask import Blueprint, request, jsonify, send_file, current_app
from services import ArvoreService
from simplekml import Kml
import os
from flask_login import login_required

arvore_bp = Blueprint('arvore', __name__)

@arvore_bp.route('/arvores', methods=['POST'])
@login_required
def cadastrar_arvore():
    data = request.json
    try:
        nova = ArvoreService.criar(data)
        return jsonify({"message": "Árvore cadastrada!", "id": nova.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@arvore_bp.route('/arvores', methods=['GET'])
@login_required
def listar_arvores():
    try:
        arvores = ArvoreService.listar(com_especie=True)
        lista = []
        for a in arvores:
            especie_nome = getattr(a.especie, "nome_popular", a.especie) if getattr(a, "especie", None) else getattr(a, "especie", None)
            lista.append({
                "id": a.id,
                "especie": especie_nome,
                "endereco": a.endereco,
                "bairro": a.bairro,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "data_plantio": a.data_plantio.isoformat() if a.data_plantio else None,
                "foto": a.foto,
                "observacao": a.observacao
            })
        return jsonify(lista), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@arvore_bp.route('/gerar_kml')
@login_required
def gerar_kml():
    try:
        arvores = ArvoreService.listar(com_especie=True)
        kml = Kml(name="Árvores SEMAPA", open=1)
        for a in arvores:
            especie_nome = getattr(a.especie, "nome_popular", a.especie) if getattr(a, "especie", None) else getattr(a, "especie", None)
            ponto = kml.newpoint(
                name=especie_nome,
                coords=[(float(a.longitude), float(a.latitude))]
            )
            ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
            ponto.description = f"""
                <![CDATA[
                    <h3>Detalhes da Árvore</h3>
                    <p>ID: {a.id}</p>
                    <p>Espécie: {especie_nome}</p>
                ]]>
            """
        temp_dir = os.path.join(current_app.root_path, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        caminho_kml = os.path.join(temp_dir, 'arvores.kml')
        kml.save(caminho_kml)
        return send_file(caminho_kml, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@arvore_bp.route('/gerar_kml/<int:arvore_id>')
@login_required
def gerar_kml_arvore(arvore_id):
    try:
        arvore = ArvoreService.buscar_por_id(arvore_id, com_especie=True)
        if not arvore:
            return jsonify({"error": "Árvore não encontrada"}), 404
        especie_nome = getattr(arvore.especie, "nome_popular", arvore.especie) if getattr(arvore, "especie", None) else getattr(arvore, "especie", None)
        kml = Kml(name=f"Árvore {especie_nome}", open=1)
        ponto = kml.newpoint(
            name=especie_nome,
            coords=[(float(arvore.longitude), float(arvore.latitude))]
        )
        ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
        ponto.description = f"""
            <![CDATA[
                <h3>Detalhes da Árvore</h3>
                <p>ID: {arvore.id}</p>
                <p>Espécie: {especie_nome}</p>
                <p>Endereço: {arvore.endereco}</p>
            ]]>
        """
        temp_dir = os.path.join(current_app.root_path, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        caminho_kml = os.path.join(temp_dir, f'arvore_{arvore_id}.kml')
        kml.save(caminho_kml)
        return send_file(caminho_kml, as_attachment=True, download_name=f'arvore_{arvore_id}.kml')
    except Exception as e:
        return jsonify({"error": str(e)}), 400
