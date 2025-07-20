from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from semapa.models import SessionLocal, Vistoria, Requerimento, Especies
from sqlalchemy.orm import joinedload
import sqlalchemy as sa

main_bp = Blueprint('main', __name__)

def nivel_requerido(*niveis_permitidos):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if current_user.nivel not in niveis_permitidos:
                if current_user.nivel == 3:
                    return "<script>alert('Acesso negado'); window.location.href = '/os_listar';</script>", 403
                else:
                    flash('Acesso negado', 'error')
                    return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('base.html')

@main_bp.route('/')
@login_required
@nivel_requerido(1, 2)
def index():
    return render_template('index.html')

@main_bp.route('/index')
@login_required
@nivel_requerido(1, 2)
def index_alias():
    return render_template('index.html')

@main_bp.route('/requerimento')
@login_required
@nivel_requerido(1, 2)
def requerimento():
    return render_template('requerimento.html')

@main_bp.route('/requerimento_listar')
@login_required
@nivel_requerido(1, 2)
def requerimento_listar():
    return render_template('requerimento_listar.html')

@main_bp.route('/os_listar')
@login_required
@nivel_requerido(1, 2, 3)
def os_listar():
    return render_template('os_listar.html')

@main_bp.route('/vistoria_listar')
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

@main_bp.route('/vistoria_form')
@login_required
@nivel_requerido(1, 2)
def vistoria_form():
    session = SessionLocal()
    try:
        requerimento_id = request.args.get('requerimento_id', type=int)
        requerimento = None
        if requerimento_id:
            requerimento = session.query(Requerimento).filter(
                Requerimento.id == requerimento_id
            ).first()
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

@main_bp.route('/lista_especies')
@login_required
@nivel_requerido(1, 2, 3)
def lista_especies():
    return render_template('lista_especies.html')

@main_bp.route('/api/especies_autocomplete')
@login_required
def especies_autocomplete():
    termo = request.args.get('q', '').strip()
    session = SessionLocal()
    try:
        query = session.query(Especies)
        if termo:
            termo_like = f"%{termo.lower()}%"
            query = query.filter(
                sa.func.lower(Especies.nome_popular).like(termo_like),
                sa.func.lower(Especies.nome_cientifico).like(termo_like)
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