from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for
from flask_cors import CORS
from database import SessionLocal, criar_banco, Requerente, Arvore, Requerimento, OrdemServico, Especies, User
import os
from simplekml import Kml
from sqlalchemy.orm import joinedload
import sqlalchemy as sa
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import bcrypt

app = Flask(__name__)
app.secret_key = "SUA_CHAVE_SECRETA_AQUI"
CORS(app, resources={r"/*": {"origins": "*"}})
criar_banco()

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

# -------------------- AUTENTICAÇÃO --------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        session = SessionLocal()
        user = session.query(User).filter_by(email=email).first()
        session.close()
        if user and bcrypt.checkpw(senha.encode(), user.password.encode()):
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="E-mail ou senha inválidos")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['password']
        session = SessionLocal()
        if session.query(User).filter_by(email=email).first():
            session.close()
            return render_template('register.html', error="E-mail já cadastrado.")
        hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        novo = User(nome=nome, email=email, telefone=telefone, password=hash_senha, nivel=3)
        session.add(novo)
        session.commit()
        session.close()
        return render_template('login.html', error="Cadastro realizado. Faça login.")
    return render_template('register.html')

@app.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    senha_atual = request.form['senha_atual']
    nova_senha = request.form['nova_senha']
    confirma = request.form['confirma_senha']
    session = SessionLocal()
    user = session.query(User).get(current_user.id)
    if not user or not bcrypt.checkpw(senha_atual.encode(), user.password.encode()):
        session.close()
        return render_template('index.html', error="Senha atual incorreta.")
    if nova_senha != confirma:
        session.close()
        return render_template('index.html', error="As novas senhas não coincidem.")
    user.password = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
    session.commit()
    session.close()
    return render_template('index.html', error="Senha alterada com sucesso.")

# -------------------- TELAS PRINCIPAIS --------------------

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/index')
@login_required
def index_alias():
    return render_template('index.html')

@app.route('/requerimento')
@login_required
def requerimento():
    return render_template('requerimento.html')

@app.route('/requerimento_listar')
@login_required
def requerimento_listar():
    return render_template('requerimento_listar.html')

@app.route('/os_listar')
@login_required
def os_listar():
    return render_template('os_listar.html')

@app.route('/lista_especies')
@login_required
def lista_especies():
    return render_template('lista_especies.html')

# -------------------- KML --------------------

@app.route('/gerar_kml')
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

@app.route('/gerar_kml/<int:arvore_id>')
@login_required
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

# -------------------- REQUERENTES --------------------

@app.route('/requerente', methods=['POST'])
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

@app.route('/requerentes/<int:id>', methods=['PUT'])
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

@app.route('/requerentes', methods=['GET'])
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

@app.route('/requerentes/todos', methods=['GET'])
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

@app.route('/api/requerente/existe', methods=['GET'])
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

@app.route('/arvores/todos', methods=['GET'])
@login_required
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
            "observacao": a.observacao,
            "data_criacao": a.data_criacao.isoformat() if a.data_criacao else None,
            "criado_por": a.criado_por,
            "data_atualizacao": a.data_atualizacao.isoformat() if a.data_atualizacao else None,
            "atualizado_por": a.atualizado_por
        } for a in arvores]), 200
    finally:
        session.close()

@app.route('/arvores', methods=['POST'])
@login_required
def cadastrar_arvore():
    data = request.json
    session = SessionLocal()
    try:
        data_plantio = None
        if data.get('data_plantio'):
            data_plantio = datetime.strptime(data['data_plantio'], '%Y-%m-%d')
        nova = Arvore(
            especie=data['especie'] or None,
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

@app.route('/arvores/<int:id>', methods=['PUT'])
@login_required
def atualizar_arvore(id):
    data = request.json
    session = SessionLocal()
    try:
        arvore = session.query(Arvore).get(id)
        if not arvore:
            return jsonify({"error": "Árvore não encontrada"}), 404
        arvore.especie = data.get('especie', arvore.especie)
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

@app.route('/api/sugestoes/bairros')
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
        
@app.route('/api/sugestoes/enderecos')
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

@app.route('/arvores', methods=['GET'])
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
                "especie": a.especie,
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

# -------------------- REQUERIMENTOS --------------------

@app.route('/requerimento', methods=['POST'])
@login_required
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

@app.route('/requerimentos', methods=['GET'])
@login_required
def listar_requerimentos():
    session = SessionLocal()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)
        order_by = request.args.get('order_by', 'id')
        direction = request.args.get('direction', 'desc').lower()
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
@login_required
def atualizar_requerimento(id):
    data = request.json
    session = SessionLocal()
    try:
        requerimento = session.query(Requerimento).get(id)
        if not requerimento:
            return jsonify({"error": "Requerimento não encontrado"}), 404
        requerimento.numero = data.get('numero', requerimento.numero)
        requerimento.tipo = data.get('tipo', requerimento.tipo)
        requerimento.motivo = data.get('motivo', requerimento.motivo)
        requerimento.prioridade = data.get('prioridade', requerimento.prioridade)
        requerimento.status = data.get('status', requerimento.status)
        requerimento.data_abertura = datetime.strptime(data['data_abertura'], '%Y-%m-%d') if data.get('data_abertura') else requerimento.data_abertura
        requerimento.requerente_id = data.get('requerente_id', requerimento.requerente_id)
        requerimento.arvore_id = data.get('arvore_id', requerimento.arvore_id)
        requerimento.observacao = data.get('observacao', requerimento.observacao)
        requerimento.data_atualizacao = datetime.now()
        requerimento.atualizado_por = current_user.id
        session.commit()
        return jsonify({"message": "Requerimento atualizado com sucesso!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/requerimentos/todos', methods=['GET'])
@login_required
def listar_todos_requerimentos():
    session = SessionLocal()
    try:
        requerimentos = (
            session.query(Requerimento)
            .options(joinedload(Requerimento.arvore))
            .filter(sa.func.lower(Requerimento.status) != 'concluído')
            .order_by(Requerimento.id.desc())
            .all()
        )
        requerimentos_json = []
        for r in requerimentos:
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
        print(f"Erro no backend: {str(e)}")
        return jsonify({"error": "Erro interno no servidor"}), 500
    finally:
        session.close()

# -------------------- ORDEM DE SERVIÇO --------------------

@app.route('/ordens_servico', methods=['GET', 'POST'])
@login_required
def ordens_servico():
    if request.method == 'GET':
        return listar_ordens_servico()
    elif request.method == 'POST':
        return cadastrar_ordem_servico()

def listar_ordens_servico():
    session = SessionLocal()
    try:
        ordens = session.query(OrdemServico).all()
        ordens_json = []
        for os in ordens:
            # Carregar requerimentos com dados completos
            requerimentos = []
            for req in os.requerimentos:
                requerimentos.append({
                    "id": req.id,
                    "numero": req.numero,
                    "requerente_nome": req.requerente.nome if req.requerente else "",
                    "requerente_telefone": req.requerente.telefone if req.requerente else "",
                    "arvore_endereco": req.arvore.endereco if req.arvore else "",
                    "arvore_latitude": req.arvore.latitude if req.arvore else None,
                    "arvore_longitude": req.arvore.longitude if req.arvore else None
                })
            
            ordens_json.append({
                "id": os.id,
                "numero": os.numero,
                "responsavel": os.responsavel,
                "data_emissao": os.data_emissao.isoformat() if os.data_emissao else None,
                "data_execucao": os.data_execucao.isoformat() if os.data_execucao else None,
                "status": os.status,
                "observacao": os.observacao,
                "requerimentos": requerimentos
            })
        return jsonify(ordens_json), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

def cadastrar_ordem_servico():
    data = request.json
    session = SessionLocal()
    try:
        # Verificar se requerimento_ids existe e não está vazio
        requerimento_ids = data.get('requerimento_ids', [])
        if not requerimento_ids:
            return jsonify({"error": "Nenhum requerimento selecionado."}), 400
        
        # Verificar se todos os requerimentos existem
        requerimentos = session.query(Requerimento).filter(Requerimento.id.in_(requerimento_ids)).all()
        if len(requerimentos) != len(requerimento_ids):
            ids_encontrados = {r.id for r in requerimentos}
            ids_nao_encontrados = [rid for rid in requerimento_ids if rid not in ids_encontrados]
            return jsonify({"error": f"Requerimentos não encontrados: {ids_nao_encontrados}"}), 400
        
        nova = OrdemServico(
            numero=data['numero'],
            responsavel=data['responsavel'],
            observacao=data.get('observacao', ''),
            criado_por=current_user.id,
            data_emissao=datetime.now()
        )
        if 'data_execucao' in data:
            nova.data_execucao = data['data_execucao']
        nova.requerimentos = requerimentos
        session.add(nova)
        session.commit()
        return jsonify({"message": "Ordem de serviço cadastrada!", "id": nova.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@app.route('/ordens_servico/<int:id>', methods=['PUT'])
@login_required
def atualizar_ordem_servico(id):
    data = request.json
    session = SessionLocal()
    try:
        ordem = session.query(OrdemServico).get(id)
        if not ordem:
            return jsonify({"error": "Ordem de serviço não encontrada"}), 404
        ordem.numero = data.get('numero', ordem.numero)
        ordem.responsavel = data.get('responsavel', ordem.responsavel)
        ordem.observacao = data.get('observacao', ordem.observacao)
        if 'data_execucao' in data:
            ordem.data_execucao = data['data_execucao']
        ordem.data_atualizacao = datetime.now()
        ordem.atualizado_por = current_user.id
        session.commit()
        return jsonify({"message": "Ordem de serviço atualizada!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
        
@app.route('/ordens_servico/<int:id>', methods=['GET'])
@login_required
def detalhes_ordem_servico(id):
    session = SessionLocal()
    try:
        os = session.query(OrdemServico).get(id)
        if not os:
            return jsonify({"error": "Ordem de serviço não encontrada"}), 404
        
        # Carregar requerimentos com dados completos
        requerimentos = []
        for req in os.requerimentos:
            requerimentos.append({
                "id": req.id,
                "numero": req.numero,
                "tipo": req.tipo,
                "motivo": req.motivo,
                "requerente_nome": req.requerente.nome if req.requerente else "",
                "requerente_telefone": req.requerente.telefone if req.requerente else "",
                "arvore_endereco": req.arvore.endereco if req.arvore else "",
                "arvore_latitude": req.arvore.latitude if req.arvore else None,
                "arvore_longitude": req.arvore.longitude if req.arvore else None
            })
        
        return jsonify({
            "id": os.id,
            "numero": os.numero,
            "responsavel": os.responsavel,
            "data_emissao": os.data_emissao.isoformat() if os.data_emissao else None,
            "data_execucao": os.data_execucao.isoformat() if os.data_execucao else None,
            "status": os.status,
            "observacao": os.observacao,
            "requerimentos": requerimentos
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

# -------------------- ESPÉCIES --------------------

@app.route('/especies', methods=['GET'])
@login_required
def listar_especies():
    session = SessionLocal()
    try:
        especies = session.query(Especies).order_by(Especies.nome_popular.asc()).all()
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
@login_required
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
@login_required
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
