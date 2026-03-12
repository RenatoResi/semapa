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
        # Ano selecionado (padrão: ano atual)
        ano_atual = int(request.form.get('ano', datetime.now().year))
        
        # Estatísticas gerais
        total_usuarios = session.query(sa_func.count(User.id)).scalar()
        total_requerimentos = session.query(sa_func.count(Requerimento.id)).filter(extract('year', Requerimento.data_abertura) == ano_atual).scalar() or 0
        total_especies = session.query(sa_func.count(Especies.id)).scalar()

        # Estatísticas de requerimentos (acumulado até o ano selecionado)
        req_pendentes = session.query(sa_func.count(Requerimento.id)).filter(
            sa_func.lower(Requerimento.status) == 'aberto',
            extract('year', Requerimento.data_abertura) <= ano_atual
        ).scalar() or 0

        # Listas recentes
        mes = request.form.get('mes', datetime.now().month)  # Usa o mês atual como padrão
        mes = int(mes)
        ultimos_requerimentos = session.query(Requerimento)\
            .filter(extract('month', Requerimento.data_abertura) == mes,\
                    extract('year', Requerimento.data_abertura) == ano_atual)\
            .filter(sa_func.lower(Requerimento.status) == 'aberto')\
            .order_by(Requerimento.data_abertura.desc())\
            .limit(30)\
            .all()

        requerimentos_concluidos = session.query(Requerimento)\
            .filter(extract('month', Requerimento.data_conclusao) == mes,\
                    extract('year', Requerimento.data_conclusao) == ano_atual)\
            .filter(sa_func.lower(Requerimento.status) == 'concluído')\
            .order_by(Requerimento.data_conclusao.desc())\
            .limit(30)\
            .all()

        # Dados para gráfico anual
        # já temos `ano_atual` definido acima
        meses_nomes = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                       'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        requerimentos_emitidos = []
        requerimentos_finalizados = []
        saldo_acumulado = []

        # Calcula o acumulado carregado do ano anterior e inicia o acumulado com esse valor
        prev_year = ano_atual - 1
        emitidos_prev = session.query(sa_func.count(Requerimento.id)).filter(
            extract('year', Requerimento.data_abertura) == prev_year
        ).scalar() or 0
        concluidos_prev = session.query(sa_func.count(Requerimento.id)).filter(
            extract('year', Requerimento.data_conclusao) == prev_year,
            sa_func.lower(Requerimento.status) == 'concluído'
        ).scalar() or 0
        acumulado = emitidos_prev - concluidos_prev

        for m in range(1, 13):
            # Requerimentos emitidos no mês
            emitidos = session.query(sa_func.count(Requerimento.id)).filter(
                extract('month', Requerimento.data_abertura) == m,
                extract('year', Requerimento.data_abertura) == ano_atual
            ).scalar() or 0

            # Requerimentos concluídos no mês
            concluidos = session.query(sa_func.count(Requerimento.id)).filter(
                extract('month', Requerimento.data_conclusao) == m,
                extract('year', Requerimento.data_conclusao) == ano_atual,
                sa_func.lower(Requerimento.status) == 'concluído'
            ).scalar() or 0

            requerimentos_emitidos.append(emitidos)
            requerimentos_finalizados.append(concluidos)
            acumulado += (emitidos - concluidos)
            saldo_acumulado.append(acumulado)

        stats = {
            'total_usuarios': total_usuarios,
            'total_requerimentos': total_requerimentos,
            'total_especies': total_especies,
        }
        req_stats = {'pendentes': req_pendentes}

        grafico_dados = {
            'meses': meses_nomes,
            'emitidos': requerimentos_emitidos,
            'concluidos': requerimentos_finalizados,
            'saldo': saldo_acumulado
        }

        # Dados para gráfico de pizza: contagem por tipo (ano atual)
        tipo_counts = session.query(
            Requerimento.tipo,
            sa_func.count(Requerimento.id)
        ).filter(
            extract('year', Requerimento.data_abertura) == ano_atual
        ).group_by(Requerimento.tipo).all()

        pie_labels = [t[0].title() if t[0] else 'Outro' for t in tipo_counts]
        pie_data = [t[1] for t in tipo_counts]

        grafico_pie = {
            'labels': pie_labels,
            'data': pie_data
        }
        # faixa de anos para seleção (ex.: últimos 3 anos até próximo ano)
        current_year = datetime.now().year
        years = list(range(current_year - 3, current_year + 2))

        return render_template('dashboard.html', 
                             stats=stats, 
                             req_stats=req_stats, 
                             ultimos_requerimentos=ultimos_requerimentos, 
                             requerimentos_concluidos=requerimentos_concluidos,
                             mes=mes,
                             ano=ano_atual,
                             years=years,
                             grafico_dados=grafico_dados,
                             grafico_pie=grafico_pie)
    finally:
        session.close()
