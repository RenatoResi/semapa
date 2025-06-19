from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from database import SessionLocal, criar_banco, Requerente, Arvore, Requerimento, OrdemServico, Especies
import os
from simplekml import Kml
from sqlalchemy.orm import Session
import sqlalchemy as sa
import sqlalchemy
from datetime import datetime
from sqlalchemy.orm import joinedload
from flask import render_template

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
criar_banco()

@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/requerimento')
def requerimento():
    return render_template('requerimento.html')

@app.route('/requerimento_listar')
def requerimento_listar():
    return render_template('requerimento_listar.html')

@app.route('/os_listar')
def os_listar():
    return render_template('os_listar.html')

@app.route('/lista_especies')
def lista_especies():
    return render_template('lista_especies.html')

@app.route('/gerar_kml')
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

@app.route('/gerar_kml/<int:arvore_id>')
def gerar_kml_arvore(arvore_id):
    session = SessionLocal()
    try:
        arvore = session.execute(
            sa.select(Arvore.id, Arvore.especie, Arvore.latitude, Arvore.longitude, Arvore.endereco)
            .where(Arvore.id == arvore_id)
        ).first()
        
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
        
        os.makedirs(os.path.join(app.root_path, 'temp'), exist_ok=True)
        caminho_kml = os.path.join(app.root_path, 'temp', f'arvore_{arvore_id}.kml')
        kml.save(caminho_kml)

        return send_file(caminho_kml, as_attachment=True, download_name=f'arvore_{arvore_id}.kml')
    finally:
        session.close()

@app.route('/requerente', methods=['POST'])
def cadastrar_requerente():
    data = request.json
    session = SessionLocal()
    try:
        novo = Requerente(
            nome=data['nome'],
            telefone=data.get('telefone', ''),
            observacao=data.get('observacao', '')
        )
        session.add(novo)
        session.commit()
        return jsonify({"message": "Requerente cadastrado!", "id": novo.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/requerentes', methods=['GET'])
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
            "requerentes": [{
                "id": r.id,
                "nome": r.nome,
                "telefone": r.telefone,
                "observacao": r.observacao
            } for r in requerentes],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

# Endpoint para todos requerentes (sem paginação)
@app.route('/requerentes/todos', methods=['GET'])
def listar_todos_requerentes():
    session = SessionLocal()
    try:
        requerentes = session.query(Requerente).order_by(Requerente.id.desc()).all()
        return jsonify([{
            "id": r.id,
            "nome": r.nome,
            "telefone": r.telefone,
            "observacao": r.observacao
        } for r in requerentes]), 200
    finally:
        session.close()

# Endpoint para todas árvores (sem paginação)
@app.route('/arvores/todos', methods=['GET'])
def listar_todas_arvores():
    session = SessionLocal()
    try:
        arvores = session.query(Arvore).order_by(Arvore.id.desc()).all()
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
    finally:
        session.close()

@app.route('/api/requerente/existe', methods=['GET'])
def requerente_existe():
    nome = request.args.get('nome')

    with SessionLocal() as session:
        requerente = session.query(Requerente).filter_by(nome=nome).first()
        if requerente:
            return jsonify({"exists": True, "id": requerente.id})
        else:
            return jsonify({"exists": False})

@app.route('/arvores', methods=['POST'])
def cadastrar_arvore():
    data = request.json
    session = SessionLocal()
    try:
        data_plantio = None
        if data.get('data_plantio'):
            # Converter de string 'YYYY-MM-DD' para datetime
            data_plantio = datetime.strptime(data['data_plantio'], '%Y-%m-%d')
        nova = Arvore(
            especie=data['especie'] or None,
            endereco=data.get('endereco', ''),
            bairro=data.get('bairro', ''),
            latitude=data['latitude'] or None,
            longitude=data['longitude'] or None,
            data_plantio=data_plantio,
            foto=data.get('foto', ''),
            observacao=data.get('observacao', '')
        )
        session.add(nova)
        session.commit()
        return jsonify({"message": "Árvore cadastrada!", "id": nova.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/api/sugestoes/bairros')
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
        
@app.route('/api/sugestoes/enderecos')
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

@app.route('/arvores', methods=['GET'])
def listar_arvores():
    session = SessionLocal()
    try:
        # Pegando os parâmetros de paginação da URL (com valores padrão)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        # Consulta paginada e ordenada pelo id decrescente
        query = session.query(Arvore).order_by(Arvore.id.desc())
        total = query.count()  # Total de registros (para paginação)
        arvores = (
            query
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )

        return jsonify({
            "arvores": [{
                "id": a.id,
                "especie": a.especie,
                "endereco": a.endereco,
                "bairro": a.bairro,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "data_plantio": a.data_plantio.isoformat() if a.data_plantio else None,
                "foto": a.foto,
                "observacao": a.observacao
            } for a in arvores],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/requerimento', methods=['POST'])
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
            observacao=data.get('observacao', '')
        )
        session.add(novo)
        session.commit()
        return jsonify({"message": "Requerimento cadastrado!", "id": novo.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/requerimentos', methods=['GET'])
def listar_requerimentos():
    session = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        order_by = request.args.get('order_by', 'id')
        direction = request.args.get('direction', 'desc').lower()

        # Mapeia os campos válidos para ordenação segura
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
                "status": r.status,
                "data_abertura": r.data_abertura.isoformat() if r.data_abertura else None,
                "requerente_nome": r.requerente.nome if r.requerente else "",
                "arvore_endereco": r.arvore.endereco if r.arvore else ""
            } for r in requerimentos ],
            "total": total,
            "page": page,
            "per_page": per_page
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/requerimentos/<int:id>', methods=['PUT'])
def atualizar_requerimento(id):
    data = request.json
    session = SessionLocal()
    try:
        requerimento = session.query(Requerimento).get(id)
        if not requerimento:
            return jsonify({"error": "Requerimento não encontrado"}), 404

        # Atualiza campos, se existirem no payload
        requerimento.numero = data.get('numero', requerimento.numero)
        requerimento.tipo = data.get('tipo', requerimento.tipo)
        requerimento.motivo = data.get('motivo', requerimento.motivo)
        requerimento.prioridade = data.get('prioridade', requerimento.prioridade)
        requerimento.status = data.get('status', requerimento.status)
        requerimento.data_abertura = datetime.strptime(data['data_abertura'], '%Y-%m-%d') if data.get('data_abertura') else requerimento.data_abertura
        requerimento.requerente_id = data.get('requerente_id', requerimento.requerente_id)
        requerimento.arvore_id = data.get('arvore_id', requerimento.arvore_id)
        requerimento.observacao = data.get('observacao', requerimento.observacao)

        session.commit()
        return jsonify({"message": "Requerimento atualizado com sucesso!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/requerimentos/todos', methods=['GET'])
def listar_todos_requerimentos():
    session = SessionLocal()
    try:
        requerimentos = (
            session.query(Requerimento)
            .options(joinedload(Requerimento.arvore))
            .filter(sa.func.lower(Requerimento.status) != 'concluído')  # <-- filtro aqui
            .order_by(Requerimento.id.desc())
            .all()
        )

        requerimentos_json = []
        for r in requerimentos:
            # Captura dados da árvore associada (se existir)
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
                "arvore_id": arvore.id if arvore else None,
                "arvore_latitude": arvore.latitude if arvore else None,
                "arvore_longitude": arvore.longitude if arvore else None,
                "arvore_especie": arvore.especie if arvore else "",
                "arvore_endereco": arvore.endereco if arvore else "",
                "arvore_bairro": arvore.bairro if arvore else ""
            }
            requerimentos_json.append(requerimento_data)

        return jsonify(requerimentos_json), 200
    except Exception as e:
        print(f"Erro no backend: {str(e)}")  # Log para debug
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()

@app.route('/ordens_servico', methods=['POST'])
def cadastrar_ordem_servico():
    data = request.json
    session = SessionLocal()
    try:
        nova = OrdemServico(
            numero=data['numero'],
            responsavel=data['responsavel'],
            requerimento_id=data['requerimento_id'],
            observacao=data.get('observacao', '')
        )
        if 'data_execucao' in data:
            nova.data_execucao = data['data_execucao']
        session.add(nova)
        session.commit()
        return jsonify({"message": "Ordem de serviço cadastrada!", "id": nova.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/ordens_servico', methods=['GET'])
def listar_ordens_servico():
    session = SessionLocal()
    try:
        ordens = session.query(OrdemServico).all()
        return jsonify([{
            "id": o.id,
            "numero": o.numero,
            "data_emissao": o.data_emissao.isoformat(),
            "data_execucao": o.data_execucao.isoformat() if o.data_execucao else None,
            "responsavel": o.responsavel,
            "status": o.status,
            "observacao": o.observacao,
            "requerimento_id": o.requerimento_id
        } for o in ordens]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/especies', methods=['GET'])
def listar_especies():
    session = SessionLocal()
    try:
        especies = session.query(Especies).all()
        return jsonify([
            {
                "id": e.id,
                "nome_popular": e.nome_popular,
                "nome_cientifico": e.nome_cientifico,
                "porte": e.porte,
                "altura_min": e.altura_min,
                "altura_max": e.altura_max,
                "longevidade_min": e.longevidade_min,
                "longevidade_max": e.longevidade_max,
                "deciduidade": e.deciduidade,
                "cor_flor": e.cor_flor,
                "epoca_floracao": e.epoca_floracao,
                "fruto_comestivel": e.fruto_comestivel,
                "epoca_frutificacao": e.epoca_frutificacao,
                "necessidade_rega": e.necessidade_rega,
                "atrai_fauna": e.atrai_fauna,
                "observacoes": e.observacoes,
                "link_foto": e.link_foto
            } for e in especies
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
        
@app.route('/especies', methods=['POST'])
def cadastrar_especie():
    data = request.json
    session = SessionLocal()
    try:
        nova = Especies(
            nome_popular=data['nome_popular'],
            nome_cientifico=data['nome_cientifico'],
            porte=data['porte'],
            altura_min=data.get('altura_min'),
            altura_max=data.get('altura_max'),
            longevidade_min=data.get('longevidade_min'),
            longevidade_max=data.get('longevidade_max'),
            deciduidade=data.get('deciduidade', ''),
            cor_flor=data.get('cor_flor', ''),
            epoca_floracao=data.get('epoca_floracao', ''),
            fruto_comestivel=data.get('fruto_comestivel', 'não'),
            epoca_frutificacao=data.get('epoca_frutificacao', ''),
            necessidade_rega=data.get('necessidade_rega', ''),
            atrai_fauna=data.get('atrai_fauna', 'não'),
            observacoes=data.get('observacoes', ''),
            link_foto=data.get('link_foto', '')
        )
        session.add(nova)
        session.commit()
        return jsonify({"message": "Espécie cadastrada!", "id": nova.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/especies/<int:id>', methods=['PUT'])
def atualizar_especie(id):
    data = request.json
    session = SessionLocal()
    try:
        especie = session.query(Especies).filter(Especies.id == id).first()
        if not especie:
            return jsonify({"error": "Espécie não encontrada"}), 404

        especie.nome_popular = data.get('nome_popular', especie.nome_popular)
        especie.nome_cientifico = data.get('nome_cientifico', especie.nome_cientifico)
        especie.porte = data.get('porte', especie.porte)
        especie.altura_min = data.get('altura_min', especie.altura_min)
        especie.altura_max = data.get('altura_max', especie.altura_max)
        especie.longevidade_min = data.get('longevidade_min', especie.longevidade_min)
        especie.longevidade_max = data.get('longevidade_max', especie.longevidade_max)
        especie.deciduidade = data.get('deciduidade', especie.deciduidade)
        especie.cor_flor = data.get('cor_flor', especie.cor_flor)
        especie.epoca_floracao = data.get('epoca_floracao', especie.epoca_floracao)
        especie.fruto_comestivel = data.get('fruto_comestivel', especie.fruto_comestivel)
        especie.epoca_frutificacao = data.get('epoca_frutificacao', especie.epoca_frutificacao)
        especie.necessidade_rega = data.get('necessidade_rega', especie.necessidade_rega)
        especie.atrai_fauna = data.get('atrai_fauna', especie.atrai_fauna)
        especie.observacoes = data.get('observacoes', especie.observacoes)
        especie.link_foto = data.get('link_foto', especie.link_foto)

        session.commit()
        return jsonify({"message": "Espécie atualizada!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

if __name__ == "__main__":
    app.run(debug=True)
