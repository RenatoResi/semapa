from flask import Blueprint, request, jsonify, send_file, current_app
from services import ArvoreService
from simplekml import Kml
import os

arvore_bp = Blueprint('arvore', __name__)

@arvore_bp.route('/arvores', methods=['POST'])
def cadastrar_arvore():
    data = request.json
    try:
        nova = ArvoreService.criar(data)
        return jsonify({"message": "Árvore cadastrada!", "id": nova.id}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@arvore_bp.route('/arvores', methods=['GET'])
def listar_arvores():
    try:
        arvores = ArvoreService.listar()
        return jsonify([{
            "id": a.id,
            "especie": a.especie,
            "endereco": a.endereco,
            "bairro": a.bairro,
            "latitude": a.latitude,
            "longitude": a.longitude,
            "data_plantio": a.data_plantio.isoformat() if a.data_plantio else None,
            "foto": a.foto,
            "observacao": a.observacao
        } for a in arvores]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@arvore_bp.route('/gerar_kml')
def gerar_kml():
    try:
        arvores = ArvoreService.listar()
        kml = Kml(name="Árvores SEMAPA", open=1)
        for a in arvores:
            ponto = kml.newpoint(
                name=a.especie,
                coords=[(float(a.longitude), float(a.latitude))]
            )
            ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
            ponto.description = f"""
                <![CDATA[
                    <h3>Detalhes da Árvore</h3>
                    <p>ID: {a.id}</p>
                    <p>Espécie: {a.especie}</p>
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
def gerar_kml_arvore(arvore_id):
    try:
        arvore = ArvoreService.buscar_por_id(arvore_id)
        if not arvore:
            return jsonify({"error": "Árvore não encontrada"}), 404
        kml = Kml(name=f"Árvore {arvore.especie}", open=1)
        ponto = kml.newpoint(
            name=arvore.especie,
            coords=[(float(arvore.longitude), float(arvore.latitude))]
        )
        ponto.style.iconstyle.icon.href = 'https://maps.google.com/mapfiles/kml/shapes/parks.png'
        ponto.description = f"""
            <![CDATA[
                <h3>Detalhes da Árvore</h3>
                <p>ID: {arvore.id}</p>
                <p>Espécie: {arvore.especie}</p>
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
