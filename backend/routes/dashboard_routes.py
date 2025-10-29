# routes/dashboard_routes.py
from flask import Blueprint, render_template
from flask_login import login_required
from database import SessionLocal, User, Arvore, Especies, Requerimento, OrdemServico
from sqlalchemy import func as sa_func

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal do usuário"""
    session = SessionLocal()
    try:
        # Estatísticas gerais
        total_usuarios = session.query(sa_func.count(User.id)).scalar()
        total_arvores = session.query(sa_func.count(Arvore.id)).scalar()
        total_especies = session.query(sa_func.count(Especies.id)).scalar()
        
        # Estatísticas de requerimentos
        req_pendentes = session.query(sa_func.count(Requerimento.id)).filter(
            sa_func.lower(Requerimento.status) == 'pendente'
        ).scalar()

        # Listas recentes
        ultimos_requerimentos = session.query(Requerimento).order_by(
            Requerimento.data_abertura.desc()
        ).limit(5).all()
        
        ordens_pendentes = session.query(OrdemServico).filter(
            sa_func.lower(OrdemServico.status).in_(['aberta', 'em andamento'])
        ).order_by(OrdemServico.data_emissao.desc()).limit(5).all()

        stats = {
            'total_usuarios': total_usuarios,
            'total_arvores': total_arvores,
            'total_especies': total_especies,
        }
        req_stats = {'pendentes': req_pendentes}

        return render_template('dashboard.html', 
                             stats=stats, 
                             req_stats=req_stats, 
                             ultimos_requerimentos=ultimos_requerimentos, 
                             ordens_pendentes=ordens_pendentes)
    finally:
        session.close()
