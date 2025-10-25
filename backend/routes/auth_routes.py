from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database import SessionLocal, User
import bcrypt

auth_bp = Blueprint('auth', __name__)

# -------------------- ROTAS --------------------

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuário"""
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        session = SessionLocal()
        try:
            user = session.query(User).filter_by(email=email).first()
            if user and bcrypt.checkpw(senha.encode(), user.password.encode()):
                login_user(user)
                return redirect(url_for('pages.dashboard'))
            else:
                return render_template('login.html', error="E-mail ou senha inválidos")
        finally:
            session.close()
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout de usuário"""
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de novo usuário"""
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form['telefone']
        senha = request.form['password']
        
        session = SessionLocal()
        try:
            # Verificar se e-mail já existe
            if session.query(User).filter_by(email=email).first():
                return render_template('register.html', error="E-mail já cadastrado.")
            
            # Criar novo usuário
            hash_senha = bcrypt.hashpw(senha.encode(), bcrypt.gensalt()).decode()
            novo = User(
                nome=nome,
                email=email,
                telefone=telefone,
                password=hash_senha,
                nivel=3  # Nível padrão para novos usuários
            )
            session.add(novo)
            session.commit()
            
            return render_template('login.html', error="Cadastro realizado. Faça login.")
        except Exception as e:
            session.rollback()
            return render_template('register.html', error=f"Erro ao registrar: {str(e)}")
        finally:
            session.close()
    
    return render_template('register.html')


@auth_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    """Altera senha do usuário autenticado"""
    senha_atual = request.form['senha_atual']
    nova_senha = request.form['nova_senha']
    confirma = request.form['confirma_senha']
    
    session = SessionLocal()
    try:
        user = session.query(User).get(current_user.id)
        
        # Validar senha atual
        if not user or not bcrypt.checkpw(senha_atual.encode(), user.password.encode()):
            return render_template('base.html', error="Senha atual incorreta.")
        
        # Validar confirmação de nova senha
        if nova_senha != confirma:
            return render_template('base.html', error="As novas senhas não coincidem.")
        
        # Validar senha não vazia
        if not nova_senha:
            return render_template('base.html', error="A nova senha não pode estar vazia.")
        
        # Atualizar senha
        user.password = bcrypt.hashpw(nova_senha.encode(), bcrypt.gensalt()).decode()
        session.commit()
        
        return render_template('base.html', error="Senha alterada com sucesso.")
    except Exception as e:
        session.rollback()
        return render_template('base.html', error=f"Erro ao alterar senha: {str(e)}")
    finally:
        session.close()
