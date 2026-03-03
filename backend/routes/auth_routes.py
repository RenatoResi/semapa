from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from database import get_session, User
import bcrypt

auth_bp = Blueprint('auth', __name__)

# -------------------- ROTAS --------------------

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuário"""
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['password']
        with get_session() as session:
            user = session.query(User).filter_by(email=email).first()
            
            # Verificar se o usuário existe e a senha está correta
            if user and bcrypt.checkpw(senha.encode(), user.password.encode()):
                # Verificar se o usuário está ativo
                if not user.ativo:
                    return render_template('login.html', 
                        error="Sua conta ainda não foi ativada. Aguarde a liberação do acesso.")
                
                login_user(user)
                return redirect(url_for('dashboard.dashboard'))
            else:
                return render_template('login.html', error="E-mail ou senha inválidos")
    
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
        
        try:
            with get_session() as session:
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
                    ativo=False,  # Usuário inicia inativo
                    nivel=3  # Nível padrão para novos usuários
                )
                session.add(novo)
            
            return render_template('login.html', error="Cadastro realizado. Aguarde nossa verificação para liberar seu login.")
        except Exception as e:
            return render_template('register.html', error=f"Erro ao registrar: {str(e)}")
    
    return render_template('register.html')


@auth_bp.route('/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    """Altera senha do usuário autenticado"""
    senha_atual = request.form['senha_atual']
    nova_senha = request.form['nova_senha']
    confirma = request.form['confirma_senha']
    
    try:
        with get_session() as session:
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
        
        return render_template('base.html', error="Senha alterada com sucesso.")
    except Exception as e:
        return render_template('base.html', error=f"Erro ao alterar senha: {str(e)}")
