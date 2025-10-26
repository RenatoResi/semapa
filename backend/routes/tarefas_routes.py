from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from database import SessionLocal, Tarefa, Requerimento, Arvore, User
from datetime import datetime, timedelta, date
from sqlalchemy import or_ 

tarefas_bp = Blueprint('tarefas', __name__, url_prefix='/tarefas')

# -------------------- FUNÇÕES AUXILIARES --------------------

def get_week_navigation(semana_atual, ano_atual):
    """Calcula semana anterior e próxima para navegação"""
    # Semana anterior
    if semana_atual == 1:
        ano_anterior = ano_atual - 1
        # Semana ISO: pegue quantas semanas tem o ano anterior (52 ou 53)
        ultima_semana = date(ano_anterior, 12, 28).isocalendar()[1]
        semana_anterior = ultima_semana
    else:
        semana_anterior = semana_atual - 1
        ano_anterior = ano_atual

    # Próxima semana
    semanas_no_ano = date(ano_atual, 12, 28).isocalendar()[1]
    if semana_atual >= semanas_no_ano:
        semana_proxima = 1
        ano_proxima = ano_atual + 1
    else:
        semana_proxima = semana_atual + 1
        ano_proxima = ano_atual

    return (semana_anterior, ano_anterior, semana_proxima, ano_proxima)

def buscar_requerimento_id(session, numero_completo):
    """Busca ID do requerimento pelo número"""
    requerimento = session.query(Requerimento).filter(Requerimento.numero == numero_completo).first()
    return requerimento.id if requerimento else None

# -------------------- ROTAS --------------------

@tarefas_bp.route('/', methods=['GET'])
@login_required
def listar_tarefas():
    """Lista tarefas da semana com opção de busca"""
    semana_str = request.args.get("semana")
    ano_str = request.args.get("ano")
    busca = request.args.get("q", "").strip().lower()
    hoje = datetime.now().date()
    
    if semana_str and semana_str.isdigit():
        ref_week = int(semana_str)
        ref_year = int(ano_str) if ano_str and ano_str.isdigit() else hoje.isocalendar()[0]
    else:
        ref_week = hoje.isocalendar()[1]
        ref_year = hoje.isocalendar()[0]

    inicio_semana = datetime.strptime(f'{ref_year}-W{ref_week}-1', "%G-W%V-%u").date()
    dias_semana = [inicio_semana + timedelta(days=i) for i in range(5)]

    semana_anterior, ano_anterior, semana_proxima, ano_proxima = get_week_navigation(ref_week, ref_year)

    sessao = SessionLocal()
    try:
        if busca:
            # Se há busca, retorna TODAS as tarefas que correspondem (sem limite de semana)
            from sqlalchemy import or_
            tarefas = sessao.query(Tarefa).filter(
                or_(
                    Tarefa.descricao.ilike(f'%{busca}%'),
                    Tarefa.endereco.ilike(f'%{busca}%'),
                    Tarefa.bairro.ilike(f'%{busca}%'),
                    Tarefa.observacoes.ilike(f'%{busca}%')
                )
            ).order_by(Tarefa.data_prevista.desc()).all()
            
            # Se há resultados, usar a semana da primeira tarefa encontrada
            if tarefas:
                primeira_tarefa_data = tarefas[0].data_prevista
                inicio_semana = primeira_tarefa_data - timedelta(days=primeira_tarefa_data.weekday())
                dias_semana = [inicio_semana + timedelta(days=i) for i in range(5)]
        else:
            # Se não há busca, retorna tarefas da semana especificada
            tarefas = sessao.query(Tarefa).filter(
                Tarefa.data_prevista >= inicio_semana,
                Tarefa.data_prevista <= inicio_semana + timedelta(days=4)
            ).order_by(Tarefa.data_prevista.asc()).all()
    finally:
        sessao.close()
    
    tarefas_por_dia = {dia: [] for dia in dias_semana}
    for tarefa in tarefas:
        # Adicionar tarefa apenas se ela estiver dentro da semana mostrada
        if tarefa.data_prevista in tarefas_por_dia:
            tarefas_por_dia[tarefa.data_prevista].append(tarefa)

    return render_template(
        "tarefas_listar.html",
        dias_semana=dias_semana,
        tarefas_por_dia=tarefas_por_dia,
        semana_inicio=inicio_semana,
        semana_fim=inicio_semana + timedelta(days=4),
        semana_anterior=semana_anterior,
        ano_anterior=ano_anterior,
        semana_proxima=semana_proxima,
        ano_proxima=ano_proxima,
        timedelta=timedelta,
        busca=busca
    )

@tarefas_bp.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_tarefa():
    """Cria nova tarefa"""
    session = SessionLocal()
    try:
        chefes = session.query(User).filter(User.nivel == 4).order_by(User.nome).all()
        
        if request.method == 'POST':
            form = request.form
            requerimento_numero = form.get('requerimento_numero', '').strip()
            requerimento_id = buscar_requerimento_id(session, requerimento_numero)
            
            tarefa = Tarefa(
                descricao=form['descricao'],
                data_prevista=form['data_prevista'],
                prioridade=form.get('prioridade', 'normal'),
                status=form.get('status', 'planejada'),
                observacoes=form.get('observacoes'),
                chefe_equipe_id=form.get('chefe_equipe_id'),
                criada_por=current_user.id,
                atualizada_por=current_user.id,
                periodo=form.get('periodo'),
                complexidade=form.get('complexidade'),
                endereco=form.get('endereco'),
                bairro=form.get('bairro'),
                latitude=form.get('latitude'),
                longitude=form.get('longitude'),
                requerimento_id=requerimento_id
            )
            session.add(tarefa)
            session.commit()
            flash("Tarefa criada com sucesso!", "success")
            return redirect(url_for('tarefas.listar_tarefas'))
        
        # GET - preparar formulário vazio
        data_prevista_ini = request.args.get('data_prevista', '')
        tarefa = type('FakeTarefa', (), {})()
        tarefa.data_prevista = None
        tarefa.chefe_equipe_id = None
        
        if data_prevista_ini:
            try:
                tarefa.data_prevista = datetime.strptime(data_prevista_ini, "%Y-%m-%d").date()
            except Exception:
                tarefa.data_prevista = None
        
        return render_template("tarefa_form.html", tarefa=tarefa, chefes=chefes, current_year=datetime.now().year)
    finally:
        session.close()

@tarefas_bp.route('/<int:tarefa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tarefa(tarefa_id):
    """Edita tarefa existente"""
    sessao = SessionLocal()
    try:
        tarefa = sessao.query(Tarefa).get(tarefa_id)
        if not tarefa:
            flash("Tarefa não encontrada", "error")
            return redirect(url_for('tarefas.listar_tarefas'))

        chefes = sessao.query(User).filter(User.nivel == 4).order_by(User.nome).all()

        if request.method == 'POST':
            form = request.form
            requerimento_numero = form.get('requerimento_numero', '').strip()
            requerimento_id = None
            if requerimento_numero:
                requerimento = sessao.query(Requerimento).filter(Requerimento.numero == requerimento_numero).first()
                requerimento_id = requerimento.id if requerimento else None

            tarefa.descricao = form['descricao']
            tarefa.data_prevista = form['data_prevista']
            tarefa.prioridade = form.get('prioridade', 'normal')
            tarefa.status = form.get('status', 'planejada')
            tarefa.observacoes = form.get('observacoes')
            tarefa.chefe_equipe_id = form.get('chefe_equipe_id')
            tarefa.atualizada_por = current_user.id
            tarefa.atualizada_em = datetime.now()
            tarefa.periodo = form.get('periodo')
            tarefa.complexidade = form.get('complexidade')
            tarefa.endereco = form.get('endereco')
            tarefa.bairro = form.get('bairro')
            tarefa.latitude = form.get('latitude')
            tarefa.longitude = form.get('longitude')
            tarefa.requerimento_id = requerimento_id
            sessao.commit()
            flash("Tarefa atualizada com sucesso!", "success")
            return redirect(url_for('tarefas.listar_tarefas'))

        # GET - preencher formulário
        return render_template("tarefa_form.html", tarefa=tarefa, chefes=chefes, current_year=datetime.now().year)
    finally:
        sessao.close()

@tarefas_bp.route('/<int:tarefa_id>/detalhes')
@login_required
def tarefa_detalhes(tarefa_id):
    """Exibe detalhes da tarefa"""
    sessao = SessionLocal()
    try:
        tarefa = sessao.query(Tarefa).get(tarefa_id)
        if not tarefa:
            flash("Tarefa não encontrada.", "error")
            return redirect(url_for('tarefas.listar_tarefas'))
        return render_template("tarefa_detalhes.html", tarefa=tarefa)
    finally:
        sessao.close()

@tarefas_bp.route('/<int:tarefa_id>/status', methods=['POST'])
@login_required
def atualizar_tarefa_status(tarefa_id):
    """Atualiza status da tarefa (concluir/cancelar)"""
    sessao = SessionLocal()
    try:
        tarefa = sessao.query(Tarefa).get(tarefa_id)
        if not tarefa:
            flash("Tarefa não encontrada.", "error")
            return redirect(url_for('tarefas.listar_tarefas'))

        acao = request.form.get('acao')
        if acao == 'concluir':
            tarefa.status = 'concluida'
        elif acao == 'cancelar':
            tarefa.status = 'cancelada'

        tarefa.atualizada_por = current_user.id
        tarefa.atualizada_em = datetime.now()
        sessao.commit()
        flash("Status atualizado com sucesso!", "success")
        return redirect(url_for('tarefas.tarefa_detalhes', tarefa_id=tarefa.id))
    finally:
        sessao.close()

@tarefas_bp.route('/<int:tarefa_id>/reagendar', methods=['GET', 'POST'])
@login_required
def reagendar_tarefa(tarefa_id):
    """Reagenda tarefa para nova data"""
    sessao = SessionLocal()
    try:
        tarefa = sessao.query(Tarefa).get(tarefa_id)
        if not tarefa:
            flash("Tarefa não encontrada", "error")
            return redirect(url_for('tarefas.listar_tarefas'))

        if request.method == 'POST':
            # É necessário buscar os chefes aqui também para o caso de erro no POST
            chefes = sessao.query(User).filter(User.nivel == 4).order_by(User.nome).all()

            # ... (código do POST)
            form = request.form
            nova_data = form.get('data_prevista')
            if not nova_data:
                flash("Escolha uma nova data.", "error")
                return render_template("tarefa_form.html", tarefa=tarefa, current_year=datetime.now().year, is_reagendar=True)

            # Marcar tarefa original como prorrogada
            tarefa.status = 'prorrogada'
            tarefa.atualizada_por = current_user.id
            tarefa.atualizada_em = datetime.now()
            sessao.commit()

            # Cria nova tarefa com dados copiados e nova data
            nova_tarefa = Tarefa(
                descricao=tarefa.descricao,
                requerimento_id=tarefa.requerimento_id,
                endereco=tarefa.endereco,
                bairro=tarefa.bairro,
                latitude=tarefa.latitude,
                longitude=tarefa.longitude,
                periodo=tarefa.periodo,
                complexidade=tarefa.complexidade,
                prioridade=tarefa.prioridade,
                status='reagendada',
                observacoes=tarefa.observacoes,
                chefe_equipe_id=tarefa.chefe_equipe_id,
                criada_por=current_user.id,
                atualizada_por=current_user.id,
                data_prevista=datetime.strptime(nova_data, '%Y-%m-%d').date(),
                reagendada=tarefa.reagendada
            )
            sessao.add(nova_tarefa)
            sessao.commit()
            flash("Tarefa reagendada com sucesso!", "success")
            return redirect(url_for('tarefas.listar_tarefas'))

        # GET - mostra form já preenchido, menos data
        # Busca a lista de chefes para popular o dropdown
        chefes = sessao.query(User).filter(User.nivel == 4).order_by(User.nome).all()

        tarefa_para_form = Tarefa(
            descricao=tarefa.descricao,
            requerimento_id=tarefa.requerimento_id,
            endereco=tarefa.endereco,
            bairro=tarefa.bairro,
            latitude=tarefa.latitude,
            longitude=tarefa.longitude,
            periodo=tarefa.periodo,
            complexidade=tarefa.complexidade,
            prioridade=tarefa.prioridade,
            status=tarefa.status,
            observacoes=tarefa.observacoes,
            chefe_equipe_id=tarefa.chefe_equipe_id,
            reagendada=(tarefa.reagendada or 0) + 1
        )
        tarefa_para_form.requerimento = tarefa.requerimento  # Carrega o objeto do requerimento
        # Data prevista em branco!
        tarefa_para_form.data_prevista = None
        return render_template("tarefa_form.html", tarefa=tarefa_para_form, chefes=chefes, current_year=datetime.now().year, is_reagendar=True)
    finally:
        sessao.close()

@tarefas_bp.route('/<int:tarefa_id>/excluir', methods=['POST'])
@login_required
def excluir_tarefa(tarefa_id):
    """Exclui uma tarefa permanentemente."""
    sessao = SessionLocal()
    try:
        tarefa = sessao.query(Tarefa).get(tarefa_id)
        if not tarefa:
            flash("Tarefa não encontrada.", "error")
            return redirect(url_for('tarefas.listar_tarefas'))

        sessao.delete(tarefa)
        sessao.commit()
        flash("Tarefa excluída com sucesso!", "success")
    except Exception as e:
        sessao.rollback()
        flash(f"Erro ao excluir a tarefa: {str(e)}", "error")
    finally:
        sessao.close()
    return redirect(url_for('tarefas.listar_tarefas'))

# -------------------- API DE SUPORTE --------------------

@tarefas_bp.route('/api/requerimento')
@login_required
def api_requerimento():
    """API para buscar dados do requerimento"""
    req_numero = request.args.get('numero')
    if not req_numero:
        return jsonify({'error': 'Número do requerimento não informado'}), 400

    session = SessionLocal()
    try:
        req_numero = req_numero.strip()
        requerimento = session.query(Requerimento).filter(Requerimento.numero == req_numero).first()
        if not requerimento:
            return jsonify({'error': 'Requerimento não encontrado'}), 404

        arvore = None
        if requerimento.arvore_id:
            arvore = session.query(Arvore).get(requerimento.arvore_id)

        if not arvore:
            return jsonify({'error': 'Árvore não encontrada para este requerimento'}), 404
        
        observacoes_concat = ''
        if requerimento.observacao:
            observacoes_concat += requerimento.observacao
        if requerimento.observacao and arvore.observacao:
            observacoes_concat += ';\n'
        if arvore.observacao:
            observacoes_concat += arvore.observacao

        return jsonify({
            'descricao': requerimento.tipo + ' - ' + requerimento.motivo,
            'endereco': arvore.endereco,
            'bairro': arvore.bairro,
            'latitude': arvore.latitude,
            'longitude': arvore.longitude,
            'prioridade': requerimento.prioridade.lower() if requerimento.prioridade else 'normal',
            'observacoes': observacoes_concat or ''
        })
    finally:
        session.close()
