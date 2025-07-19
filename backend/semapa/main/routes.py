from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

main_bp = Blueprint('main', __name__, template_folder='../templates/main')

@main_bp.route('/')
def index():
    # Se o usuário já estiver logado, redireciona para o dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    # Caso contrário, mostra a página de login (que está no blueprint 'auth')
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Aqui você pode buscar dados do banco para exibir no dashboard
    # Lembre-se de usar g.db para acessar a sessão do banco
    return render_template('dashboard.html', user=current_user)