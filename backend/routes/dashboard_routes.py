from flask import Blueprint, render_template, request
from flask_login import login_required
from database import SessionLocal, User, Tarefa, Especies, Requerimento, OrdemServico
from sqlalchemy import func as sa_func, extract
from datetime import datetime


dashboard_bp = Blueprint('dashboard', __name__)



@dashboard_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Dashboard principal do usuário"""
    session = SessionLocal()
    try:
        # Estatísticas gerais
        total_usuarios = session.query(sa_func.count(User.id)).scalar()
        total_requerimentos = session.query(sa_func.count(Requerimento.id)).scalar()
        total_especies = session.query(sa_func.count(Especies.id)).scalar()
        
        # Estatísticas de requerimentos
        req_pendentes = session.query(sa_func.count(Requerimento.id)).filter(
            sa_func.lower(Requerimento.status) == 'aberto'
        ).scalar()

        # Listas recentes
        mes = request.form.get('mes', datetime.now().month)  # Usa o mês atual como padrão
        mes = int(mes)
        ultimos_requerimentos = session.query(Requerimento)\
            .filter(extract('month', Requerimento.data_abertura) == mes)\
            .filter(sa_func.lower(Requerimento.status) == 'aberto')\
            .order_by(Requerimento.data_abertura.desc())\
            .limit(30)\
            .all()
        
        # ordens_pendentes = session.query(OrdemServico).filter(
        #     sa_func.lower(OrdemServico.status).in_(['aberta', 'em andamento'])
        # ).order_by(OrdemServico.data_emissao.desc()).limit(10).all()

        # tarefas_realizadas = session.query(Tarefa).filter(
        #     sa_func.lower(Tarefa.status) == 'concluida'
        # ).order_by(Tarefa.data_conclusao.desc()).limit(10).all()

        requerimentos_concluidos = session.query(Requerimento)\
            .filter(extract('month', Requerimento.data_atualizacao) == mes)\
            .filter(sa_func.lower(Requerimento.status) == 'concluído')\
            .order_by(Requerimento.data_atualizacao.desc())\
            .limit(30)\
            .all()


        stats = {
            'total_usuarios': total_usuarios,
            'total_requerimentos': total_requerimentos,
            'total_especies': total_especies,
        }
        req_stats = {'pendentes': req_pendentes}


        return render_template('dashboard.html', 
                             stats=stats, 
                             req_stats=req_stats, 
                             ultimos_requerimentos=ultimos_requerimentos, 
                             requerimentos_concluidos=requerimentos_concluidos,
                             mes=mes)
    finally:
        session.close()
