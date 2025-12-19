from flask import Blueprint, request, render_template, redirect, url_for
from flask_login import login_required, current_user
from database import SessionLocal, Vistoria, Requerimento, User, Arvore, Especies, OrdemServico
from sqlalchemy.orm import joinedload
from sqlalchemy import func as sa_func
from functools import wraps
from routes.decorators import nivel_requerido

pages_bp = Blueprint('pages', __name__)


# -------------------- ROTAS --------------------


@pages_bp.route('/')
@login_required
@nivel_requerido(1, 2)
def index():
    """Página inicial/index"""
    return render_template('index.html')


@pages_bp.route('/index')
@login_required
@nivel_requerido(1, 2)
def index_alias():
    """Alias para /index que redireciona para /"""
    return render_template('index.html')


@pages_bp.route('/requerimento')
@login_required
@nivel_requerido(1, 2)
def requerimento():
    """Formulário para novo requerimento"""
    return render_template('requerimento.html')


@pages_bp.route('/requerimento_listar')
@login_required
@nivel_requerido(1, 2)
def requerimento_listar():
    """Listagem de requerimentos"""
    return render_template('requerimento_listar.html')


@pages_bp.route('/os_listar')
@login_required
@nivel_requerido(1, 2, 3)
def os_listar():
    """Listagem de ordens de serviço"""
    return render_template('os_listar.html')


@pages_bp.route('/vistoria_listar')
@login_required
@nivel_requerido(1, 2)
def vistoria_listar():
    """Listagem de vistorias"""
    session = SessionLocal()
    try:
        vistorias = session.query(Vistoria).options(
            joinedload(Vistoria.requerimento),
            joinedload(Vistoria.user)
        ).order_by(Vistoria.vistoria_data.desc()).all()
        return render_template('vistoria_listar.html', vistorias=vistorias)
    finally:
        session.close()


@pages_bp.route('/vistoria_form')
@login_required
@nivel_requerido(1, 2)
def vistoria_form():
    """Formulário para nova vistoria"""
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
            sa_func.lower(Requerimento.status) != 'concluído'
        ).order_by(Requerimento.data_abertura.desc()).all()
        
        return render_template('vistoria_form.html', 
                             requerimento_id=requerimento_id,
                             requerimento=requerimento,
                             requerimentos=requerimentos)
    except Exception as e:
        print(f"Erro ao carregar formulário de vistoria: {str(e)}")
        return render_template('vistoria_form.html', url_for('pages.vistoria_listar'),
                             requerimento_id=None,
                             requerimento=None,
                             requerimentos=[])
    finally:
        session.close()


@pages_bp.route('/lista_especies')
@login_required
@nivel_requerido(1, 2, 3)
def lista_especies():
    """Listagem de espécies"""
    return render_template('lista_especies.html')


@pages_bp.route('/agenda')
@login_required
@nivel_requerido(1, 2, 3)
def agenda():
    """Redireciona para agenda de tarefas"""
    return redirect(url_for('tarefas.listar_tarefas'))

@pages_bp.route('/requerimentos/<int:requerimento_id>/detalhes')
@login_required
@nivel_requerido(1, 2)
def requerimento_detalhes(requerimento_id):
    """Detalhes de um requerimento específico"""
    session = SessionLocal()
    try:
        requerimento = session.query(Requerimento).filter(
            Requerimento.id == requerimento_id
        ).first()
        
        if not requerimento:
            return "Requerimento não encontrado", 404
        
        # Carrega as vistorias associadas ao requerimento
        vistorias = session.query(Vistoria).filter(
            Vistoria.requerimento_id == requerimento_id
        ).all()
        
        return render_template('requerimento_detalhes.html', 
                               requerimento=requerimento, 
                               vistorias=vistorias)
    finally:
        session.close()