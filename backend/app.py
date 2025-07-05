from flask import Flask, request, jsonify, send_file, render_template, redirect, url_for, flash
from flask_cors import CORS
from database import SessionLocal, Requerente, Arvore, Requerimento, OrdemServico, Especies, User, Vistoria, VistoriaFoto
import os
from simplekml import Kml
from sqlalchemy.orm import joinedload
import sqlalchemy as sa
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
import bcrypt
from functools import wraps
from werkzeug.utils import secure_filename
import io
from sqlalchemy import or_

app = Flask(__name__)
app.secret_key = "SUA_CHAVE_SECRETA_AQUI"
CORS(app, resources={r"/*": {"origins": "*"}})

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

def nivel_requerido(*niveis_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            # Verificar se o nível do usuário está nos permitidos
            if current_user.nivel not in niveis_permitidos:
                # Resposta com alerta JavaScript para nível 3
                if current_user.nivel == 3:
                    return "<script>alert('Acesso negado'); window.location.href = '/os_listar';</script>", 403
                # Redirecionamento padrão para outros níveis
                else:
                    flash('Acesso negado', 'error')
                    return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

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
            return redirect(url_for('dashboard'))
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
        return render_template('base.html', error="Senha atual incorreta.")
    if nova_senha != confirma:
        session.close()
        return render_template('base.html', error="As novas senhas não coincidem.")
    user.password = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
    session.commit()
    session.close()
    return render_template('base.html', error="Senha alterada com sucesso.")

# -------------------- TELAS PRINCIPAIS --------------------

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('base.html')

@app.route('/')
@login_required
@nivel_requerido(1, 2)
def index():
    return render_template('index.html')

@app.route('/index')
@login_required
@nivel_requerido(1, 2)
def index_alias():
    return render_template('index.html')

@app.route('/requerimento')
@login_required
@nivel_requerido(1, 2)
def requerimento():
    return render_template('requerimento.html')

@app.route('/requerimento_listar')
@login_required
@nivel_requerido(1, 2)
def requerimento_listar():
    return render_template('requerimento_listar.html')

@app.route('/os_listar')
@login_required
@nivel_requerido(1, 2, 3)
def os_listar():
    return render_template('os_listar.html')

@app.route('/vistoria_listar')
@login_required
@nivel_requerido(1, 2)
def vistoria_listar():
    session = SessionLocal()
    try:
        vistorias = session.query(Vistoria).options(
            joinedload(Vistoria.requerimento),
            joinedload(Vistoria.user)
        ).all()
        return render_template('vistoria_listar.html', vistorias=vistorias)
    finally:
        session.close()

@app.route('/vistoria_form')
@login_required
@nivel_requerido(1, 2)
def vistoria_form():
    session = SessionLocal()
    try:
        # Captura o requerimento_id da URL
        requerimento_id = request.args.get('requerimento_id', type=int)
        requerimento = None
        
        # Se foi passado um requerimento_id, busca o requerimento específico
        if requerimento_id:
            requerimento = session.query(Requerimento).filter(
                Requerimento.id == requerimento_id
            ).first()
        
        # Lista todos os requerimentos para o select (caso não tenha requerimento_id)
        requerimentos = session.query(Requerimento).filter(
            sa.func.lower(Requerimento.status) != 'concluído'
        ).order_by(Requerimento.data_abertura.desc()).all()
        
        return render_template('vistoria_form.html', 
                             requerimento_id=requerimento_id,
                             requerimento=requerimento,
                             requerimentos=requerimentos)
    except Exception as e:
        print(f"Erro ao carregar formulário de vistoria: {str(e)}")
        return render_template('vistoria_form.html', 
                             requerimento_id=None,
                             requerimento=None,
                             requerimentos=[])
    finally:
        session.close()


@app.route('/lista_especies')
@login_required
@nivel_requerido(1, 2, 3)
def lista_especies():
    return render_template('lista_especies.html')

# -------------------- Rotas Auxiliares --------------------

@app.route('/api/especies_autocomplete')
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

@app.route('/arvores', methods=['POST'])
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

@app.route('/arvores/<int:id>', methods=['PUT'])
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
                "status": r.status,  # CAMPO ESSENCIAL ADICIONADO
                "data_abertura": r.data_abertura.isoformat() if r.data_abertura else None,
                "requerente_nome": r.requerente.nome if r.requerente else "",
                "arvore_endereco": r.arvore.endereco if r.arvore else "",
                # Adicione outros campos necessários para a interface
                "data_atualizacao": r.data_atualizacao.isoformat() if r.data_atualizacao else None,
                "atualizado_por": r.atualizado_por
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
        
        status_anterior = requerimento.status
        
        # Atualiza apenas campos fornecidos
        if 'status' in data:
            requerimento.status = data['status']
        
        # Campos obrigatórios de auditoria
        requerimento.data_atualizacao = datetime.now()
        requerimento.atualizado_por = current_user.id

        if status_anterior != "Concluído" and requerimento.status == "Concluído":
            # Obter todas as OS associadas a este requerimento
            ordens_servico = requerimento.ordens_servico
            
            # Verificar cada OS associada
            for os in ordens_servico:
                # Verificar se todos requerimentos desta OS estão concluídos
                todos_concluidos = all(
                    req.status == "Concluído" 
                    for req in os.requerimentos
                    if req.id != requerimento.id  # Excluir o próprio requerimento
                )
                
                # Atualizar status da OS
                if todos_concluidos:
                    os.status = "Concluída"
                else:
                    os.status = "Em Andamento"
                
                # Atualizar dados de auditoria da OS
                os.data_atualizacao = datetime.now()
                os.atualizado_por = current_user.id
        
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

@app.route('/requerimentos/todos', methods=['GET'])
@login_required
def listar_todos_requerimentos():
    session = SessionLocal()
    try:
        requerimentos = (
            session.query(Requerimento)
            .options(joinedload(Requerimento.arvore))
            .filter(sa.func.lower(Requerimento.status) != 'concluído')
            .order_by(Requerimento.data_abertura.desc())
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
                "arvore_especie": arvore.especie.nome_popular if arvore and arvore.especie else "",
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
                    "status": req.status,  # CAMPO ADICIONADO
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
                "status": req.status,  # CAMPO ESSENCIAL ADICIONADO
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
        
# -------------------- VISTORIAS --------------------

@app.route('/vistorias', methods=['GET'])
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
@app.route('/vistorias/nova', methods=['GET'])
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
@app.route('/vistorias', methods=['POST'])
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
@app.route('/vistorias/<int:id>/editar', methods=['GET'])
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
@app.route('/vistorias/<int:id>', methods=['POST'])
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

@app.route('/vistoria_foto/<int:foto_id>', methods=['GET'])
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
        
@app.route('/vistoria_foto/<int:foto_id>', methods=['DELETE'])
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
    app.run(debug=True, host='0.0.0.0', port=5000)
