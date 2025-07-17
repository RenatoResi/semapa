from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from database import SessionLocal
from database.models import User

web_bp = Blueprint('web', __name__)

@web_bp.route('/')
def home():
    return render_template('index.html')

@web_bp.route('/login', methods=['GET'])
def login():
    return render_template('login.html')

@web_bp.route('/login', methods=['POST'])
def login_post():
    # Exemplo de login simples — adapte para seu sistema real!
    email = request.form.get('email')
    senha = request.form.get('senha')
    # Adapte para checagem real no banco/conferência de hash
    if email == 'admin@admin.com' and senha == 'senha123':
        # Aqui você deveria usar login_user(user), veja observação abaixo.
        flash('Login de exemplo realizado! (implemente login_user)')
        return redirect(url_for('web.home'))
    else:
        flash('Usuário ou senha inválidos!')
        return render_template('login.html'), 401

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
    # Exemplo: receber dados e criar usuário
    nome = request.form.get('nome')
    email = request.form.get('email')
    senha = request.form.get('senha')
    # salve usuário no banco (implemente conforme modelo real)
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
