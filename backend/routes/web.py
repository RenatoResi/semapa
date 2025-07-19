from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from database import SessionLocal
from database.models import User

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
@login_required
def home():
    return render_template('index.html')

@web_bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@web_bp.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    print(f"[DEBUG] Tentando login para email: {email}")
    session = SessionLocal()
    user = session.query(User).filter_by(email=email).first()
    session.close()
    if user:
        print(f"[DEBUG] Usuário encontrado: id={user.id}, email={user.email}")
        hash_ok = check_password_hash(user.password, password)
        print(f"[DEBUG] Hash confere? {hash_ok}")
    else:
        print("[DEBUG] Usuário não encontrado!")
    if user and check_password_hash(user.password, password):
        from flask_login import login_user
        login_user(user)
        print("[DEBUG] Login realizado com sucesso!")
        return redirect(url_for('web.home'))
    else:
        error = 'Usuário ou senha inválidos!'
        print(f"[DEBUG] Falha no login: {error}")
        return render_template('login.html', error=error), 401

@web_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso.')
    return redirect(url_for('web.login'))

@web_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    nome = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    password = request.form.get('password')
    if not nome or not email or not password:
        error = 'Preencha todos os campos obrigatórios.'
        return render_template('register.html', error=error)
    session = SessionLocal()
    if session.query(User).filter_by(email=email).first():
        session.close()
        error = 'E-mail já cadastrado.'
        return render_template('register.html', error=error)
    from werkzeug.security import generate_password_hash
    user = User(nome=nome, email=email, telefone=telefone, password=generate_password_hash(password), nivel=5)
    session.add(user)
    session.commit()
    session.close()
    flash("Usuário cadastrado com sucesso!")
    return redirect(url_for('web.login'))

@web_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    senha_atual = request.form.get('senha_atual')
    nova_senha = request.form.get('nova_senha')
    confirma_senha = request.form.get('confirma_senha')

    if not nova_senha or nova_senha.strip() == '' or nova_senha != confirma_senha:
        flash('Nova senha e confirmação obrigatórias e devem ser iguais!')
        return redirect(url_for('web.home'))

    session = SessionLocal()
    user = session.query(User).filter_by(id=current_user.id).first()
    if not user or not check_password_hash(user.password, senha_atual):
        session.close()
        flash('Senha atual incorreta!')
        return redirect(url_for('web.home'))

    user.password = generate_password_hash(nova_senha)
    session.commit()
    session.close()
    flash('Senha alterada com sucesso!')
    logout_user()
    return redirect(url_for('web.login'))

@web_bp.route('/requerimento')
@login_required
def requerimento():
    return render_template('requerimento.html')

@web_bp.route('/requerimentos')
@login_required
def listar_requerimentos():
    return render_template('requerimento_listar.html')

@web_bp.route('/ordens_servico')
@login_required
def listar_ordens():
    return render_template('os_listar.html')

@web_bp.route('/vistoria_form')
@login_required
def vistoria_form():
    return render_template('vistoria_form.html')

@web_bp.route('/vistorias')
@login_required
def listar_vistorias():
    return render_template('vistoria_listar.html')

@web_bp.route('/especies')
@login_required
def lista_especies():
    return render_template('lista_especies.html')

# Adicione outros endpoints conforme seus templates existentes
