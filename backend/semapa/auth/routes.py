from flask import Blueprint, request, render_template, redirect, url_for, g, flash
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from semapa.models import User

auth_bp = Blueprint('auth', __name__, template_folder='./templates/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        user = g.db.query(User).filter_by(email=email).first()
        if user and bcrypt.checkpw(senha.encode(), user.password.encode()):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('E-mail ou senha inválidos.', 'danger')
            return redirect(url_for('auth.login'))
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['password']
        if g.db.query(User).filter_by(email=email).first():
            flash('Este e-mail já está cadastrado.', 'warning')
            return redirect(url_for('auth.register'))

        hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
        novo = User(nome=nome, email=email, telefone=telefone, password=hash_senha, nivel=3)
        g.db.add(novo)
        g.db.commit()
        flash('Cadastro realizado com sucesso! Por favor, faça o login.', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html')

@auth_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    # ... (lógica de alterar senha movida para cá)
    # Lembre-se de usar g.db em vez de criar uma nova SessionLocal()
    # e de usar url_for('main.dashboard') ou similar para redirecionar
    pass