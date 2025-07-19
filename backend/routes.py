from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
import bcrypt
from ..models import User
from ..database import SessionLocal

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        session = SessionLocal()
        user = session.query(User).filter_by(email=email).first()
        session.close()
        if user and bcrypt.checkpw(senha.encode(), user.password.encode()):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            return render_template('login.html', error="E-mail ou senha inválidos")
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
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
        return render_template('login.html', message="Cadastro realizado. Faça login.")
    return render_template('register.html')

@auth_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    # ... (lógica de alterar senha movida para cá)
    # Lembre-se de usar g.db em vez de criar uma nova SessionLocal()
    # e de usar url_for('main.dashboard') ou similar para redirecionar
    pass