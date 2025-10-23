from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from database import SessionLocal, AgendaSemanal, AgendaTarefa, AgendaTarefaTrabalhador, AgendaHistorico, User
from sqlalchemy import and_, or_
import calendar

agenda_bp = Blueprint('agenda', __name__, url_prefix='/agenda')


def tem_permissao(cargo_minimo):
    """Decorator para verificar permissões"""
    hierarquia = {
        'secretario': 4,
        'engenheiro': 3,
        'chefe_equipe': 2,
        'trabalhador': 1
    }
    return hierarquia.get(getattr(current_user, 'cargo', None), 0) >= hierarquia.get(cargo_minimo, 0)


@agenda_bp.route('/')
@login_required
def index():
    """Página principal da agenda"""
    hoje = datetime.now().date()
    session = SessionLocal()
    try:
        # Buscar próximas 3 semanas
        agendas = session.query(AgendaSemanal).filter(
            AgendaSemanal.semana_inicio >= hoje
        ).order_by(AgendaSemanal.semana_inicio).limit(3).all()
        
        # Se não houver agendas, criar placeholders para as próximas 3 semanas
        if not agendas:
            agendas = gerar_semanas_vazias(3)
        
        return render_template('agenda.html', agendas=agendas)
    finally:
        session.close()


@agenda_bp.route('/semana/<int:agenda_id>')
@login_required
def ver_semana(agenda_id):
    """Visualizar detalhes de uma semana específica"""
    session = SessionLocal()
    try:
        agenda = session.query(AgendaSemanal).get(agenda_id)
        if not agenda:
            flash('Agenda não encontrada.', 'error')
            return redirect(url_for('agenda.index'))
        
        tarefas = session.query(AgendaTarefa).filter_by(agenda_id=agenda_id).order_by(AgendaTarefa.data_prevista).all()
        
        # Agrupar tarefas por dia
        tarefas_por_dia = {}
        for tarefa in tarefas:
            dia = tarefa.data_prevista
            if dia not in tarefas_por_dia:
                tarefas_por_dia[dia] = []
            tarefas_por_dia[dia].append(tarefa)
        
        return render_template('agenda_semana.html', agenda=agenda, tarefas_por_dia=tarefas_por_dia)
    finally:
        session.close()


@agenda_bp.route('/tarefa/nova', methods=['GET', 'POST'])
@login_required
def nova_tarefa():
    """Criar nova tarefa - apenas engenheiro e secretário"""
    if not tem_permissao('engenheiro'):
        flash('Você não tem permissão para criar tarefas.', 'error')
        return redirect(url_for('agenda.index'))
    
    session = SessionLocal()
    try:
        if request.method == 'POST':
            try:
                # Extrair dados do formulário
                data_prevista = datetime.strptime(request.form['data_prevista'], '%Y-%m-%d').date()
                
                # Verificar ou criar agenda para a semana
                agenda = obter_ou_criar_agenda(session, data_prevista)
                
                # Criar tarefa
                tarefa = AgendaTarefa(
                    agenda_id=agenda.id,
                    descricao=request.form['descricao'],
                    tipo_atividade=request.form['tipo_atividade'],
                    local=request.form['local'],
                    endereco=request.form.get('endereco'),
                    latitude=request.form.get('latitude'),
                    longitude=request.form.get('longitude'),
                    data_prevista=data_prevista,
                    hora_inicio=request.form.get('hora_inicio'),
                    hora_fim=request.form.get('hora_fim'),
                    prioridade=request.form.get('prioridade', 'normal'),
                    observacoes=request.form.get('observacoes'),
                    chefe_equipe_id=request.form.get('chefe_equipe_id'),
                    criada_por=current_user.id
                )
                
                session.add(tarefa)
                session.commit()
                
                # Registrar histórico
                registrar_historico(session, tarefa.id, current_user.id, 'criada', 'Tarefa criada')
                
                # Enviar notificação WhatsApp (se configurado)
                enviar_notificacao_nova_tarefa(tarefa)
                
                flash('Tarefa criada com sucesso!', 'success')
                return redirect(url_for('agenda.ver_semana', agenda_id=agenda.id))
            except Exception as e:
                session.rollback()
                flash(f'Erro ao criar tarefa: {str(e)}', 'error')
                return redirect(url_for('agenda.nova_tarefa'))
        
        # GET - exibir formulário
        chefes = session.query(User).filter_by(nivel=3).all()
        return render_template('agenda_tarefa_form.html', chefes=chefes, tarefa=None)
    finally:
        session.close()


@agenda_bp.route('/tarefa/<int:tarefa_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_tarefa(tarefa_id):
    """Editar tarefa existente"""
    session = SessionLocal()
    try:
        tarefa = session.query(AgendaTarefa).get(tarefa_id)
        if not tarefa:
            flash('Tarefa não encontrada.', 'error')
            return redirect(url_for('agenda.index'))
        
        if not tem_permissao('engenheiro'):
            flash('Você não tem permissão para editar tarefas.', 'error')
            return redirect(url_for('agenda.index'))
        
        if request.method == 'POST':
            try:
                # Registrar alterações
                alteracoes = []
                
                if tarefa.descricao != request.form['descricao']:
                    alteracoes.append("Descrição alterada")
                    tarefa.descricao = request.form['descricao']
                
                if tarefa.local != request.form['local']:
                    alteracoes.append("Local alterado")
                    tarefa.local = request.form['local']
                
                # Atualizar outros campos
                tarefa.tipo_atividade = request.form['tipo_atividade']
                tarefa.endereco = request.form.get('endereco')
                tarefa.data_prevista = datetime.strptime(request.form['data_prevista'], '%Y-%m-%d').date()
                tarefa.hora_inicio = request.form.get('hora_inicio')
                tarefa.hora_fim = request.form.get('hora_fim')
                tarefa.prioridade = request.form.get('prioridade', 'normal')
                tarefa.observacoes = request.form.get('observacoes')
                tarefa.chefe_equipe_id = request.form.get('chefe_equipe_id')
                
                session.commit()
                
                # Registrar histórico
                if alteracoes:
                    registrar_historico(session, tarefa.id, current_user.id, 'editada', '; '.join(alteracoes))
                    
                    # Enviar notificação de alteração
                    enviar_notificacao_edicao_tarefa(tarefa, alteracoes)
                
                flash('Tarefa atualizada com sucesso!', 'success')
                return redirect(url_for('agenda.ver_semana', agenda_id=tarefa.agenda_id))
            except Exception as e:
                session.rollback()
                flash(f'Erro ao atualizar tarefa: {str(e)}', 'error')
        
        chefes = session.query(User).filter_by(nivel=3).all()
        return render_template('agenda_tarefa_form.html', chefes=chefes, tarefa=tarefa)
    finally:
        session.close()


@agenda_bp.route('/tarefa/<int:tarefa_id>/atribuir_trabalhadores', methods=['POST'])
@login_required
def atribuir_trabalhadores(tarefa_id):
    """Atribuir trabalhadores a uma tarefa - chefe de equipe"""
    session = SessionLocal()
    try:
        tarefa = session.query(AgendaTarefa).get(tarefa_id)
        if not tarefa:
            flash('Tarefa não encontrada.', 'error')
            return redirect(url_for('agenda.index'))
        
        if not (tem_permissao('chefe_equipe') or current_user.id == tarefa.chefe_equipe_id):
            flash('Você não tem permissão para atribuir trabalhadores.', 'error')
            return redirect(url_for('agenda.index'))
        
        try:
            trabalhadores_ids = request.form.getlist('trabalhadores')
            
            # Remover atribuições antigas
            session.query(AgendaTarefaTrabalhador).filter_by(tarefa_id=tarefa_id).delete()
            
            # Adicionar novas atribuições
            for trabalhador_id in trabalhadores_ids:
                atribuicao = AgendaTarefaTrabalhador(
                    tarefa_id=tarefa_id,
                    trabalhador_id=int(trabalhador_id),
                    atribuido_por=current_user.id
                )
                session.add(atribuicao)
            
            session.commit()
            
            # Registrar histórico
            registrar_historico(session, tarefa_id, current_user.id, 'atribuida', 
                                f'{len(trabalhadores_ids)} trabalhador(es) atribuído(s)')
            
            # Notificar trabalhadores
            for trabalhador_id in trabalhadores_ids:
                trabalhador = session.query(User).get(trabalhador_id)
                enviar_notificacao_atribuicao(trabalhador, tarefa)
            
            flash('Trabalhadores atribuídos com sucesso!', 'success')
        except Exception as e:
            session.rollback()
            flash(f'Erro ao atribuir trabalhadores: {str(e)}', 'error')
        
        return redirect(url_for('agenda.ver_semana', agenda_id=tarefa.agenda_id))
    finally:
        session.close()


@agenda_bp.route('/tarefa/<int:tarefa_id>/atualizar_status', methods=['POST'])
@login_required
def atualizar_status(tarefa_id):
    """Atualizar status da tarefa"""
    session = SessionLocal()
    try:
        tarefa = session.query(AgendaTarefa).get(tarefa_id)
        if not tarefa:
            return jsonify({'success': False, 'message': 'Tarefa não encontrada'}), 404
        
        novo_status = request.form.get('status')
        if novo_status not in ['planejada', 'aprovada', 'em_andamento', 'concluida', 'cancelada']:
            return jsonify({'success': False, 'message': 'Status inválido'}), 400
        
        # Verificar permissões
        if novo_status == 'aprovada' and not tem_permissao('secretario'):
            return jsonify({'success': False, 'message': 'Apenas o secretário pode aprovar'}), 403
        
        if novo_status in ['em_andamento', 'concluida'] and not tem_permissao('chefe_equipe'):
            return jsonify({'success': False, 'message': 'Sem permissão'}), 403
        
        try:
            status_anterior = tarefa.status
            tarefa.status = novo_status
            
            if novo_status == 'concluida':
                tarefa.concluida_em = datetime.utcnow()
            
            session.commit()
            
            # Registrar histórico
            registrar_historico(session, tarefa_id, current_user.id, novo_status, 
                                f'Status alterado de {status_anterior} para {novo_status}')
            
            return jsonify({'success': True, 'message': 'Status atualizado'})
        except Exception as e:
            session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        session.close()


@agenda_bp.route('/semana/<int:agenda_id>/aprovar', methods=['POST'])
@login_required
def aprovar_semana(agenda_id):
    """Aprovar agenda semanal - apenas secretário"""
    if not tem_permissao('secretario'):
        flash('Apenas o secretário pode aprovar agendas.', 'error')
        return redirect(url_for('agenda.index'))
    
    session = SessionLocal()
    try:
        agenda = session.query(AgendaSemanal).get(agenda_id)
        if not agenda:
            flash('Agenda não encontrada.', 'error')
            return redirect(url_for('agenda.index'))
        
        try:
            agenda.aprovada = True
            agenda.aprovada_por = current_user.id
            agenda.aprovada_em = datetime.utcnow()
            
            # Atualizar status de todas as tarefas para 'aprovada'
            session.query(AgendaTarefa).filter_by(agenda_id=agenda_id).update({'status': 'aprovada'})
            
            session.commit()
            
            flash('Agenda aprovada com sucesso!', 'success')
            
            # Notificar chefe de equipe e trabalhadores
            enviar_notificacao_aprovacao_semana(session, agenda)
        except Exception as e:
            session.rollback()
            flash(f'Erro ao aprovar agenda: {str(e)}', 'error')
        
        return redirect(url_for('agenda.ver_semana', agenda_id=agenda_id))
    finally:
        session.close()


# ========== FUNÇÕES AUXILIARES ==========

class AgendaFake:
    def __init__(self, data):
        self.semana_inicio = data['semana_inicio']
        self.semana_fim = data['semana_fim']
        self.numero_semana = data['numero_semana']
        self.ano = data['ano']
        self.vazia = data.get('vazia', False)
        self.aprovada = False
        self.tarefas = []
        self.id = None  # Atributo necessário para o template

# Função modificada para retornar objetos AgendaFake em vez de dicionários simples
def gerar_semanas_vazias(quantidade=3):
    hoje = datetime.now().date()
    inicio_semana = hoje - timedelta(days=hoje.weekday())

    semanas = []
    for i in range(quantidade):
        inicio = inicio_semana + timedelta(weeks=i)
        fim = inicio + timedelta(days=6)
        data = {
            'semana_inicio': inicio,
            'semana_fim': fim,
            'numero_semana': inicio.isocalendar()[1],
            'ano': inicio.year,
            'vazia': True
        }
        semanas.append(AgendaFake(data))

    return semanas



def obter_ou_criar_agenda(session, data):
    """Obtém agenda existente ou cria uma nova para a data"""
    inicio_semana = data - timedelta(days=data.weekday())
    fim_semana = inicio_semana + timedelta(days=6)
    
    agenda = session.query(AgendaSemanal).filter(
        and_(
            AgendaSemanal.semana_inicio == inicio_semana,
            AgendaSemanal.semana_fim == fim_semana
        )
    ).first()
    
    if not agenda:
        agenda = AgendaSemanal(
            semana_inicio=inicio_semana,
            semana_fim=fim_semana,
            ano=inicio_semana.year,
            numero_semana=inicio_semana.isocalendar()[1],
            criada_por=current_user.id
        )
        session.add(agenda)
        session.commit()
    
    return agenda


def registrar_historico(session, tarefa_id, usuario_id, acao, descricao):
    """Registra ação no histórico"""
    historico = AgendaHistorico(
        tarefa_id=tarefa_id,
        usuario_id=usuario_id,
        acao=acao,
        descricao=descricao
    )
    session.add(historico)
    session.commit()


# ========== FUNÇÕES DE NOTIFICAÇÃO WHATSAPP ==========

def enviar_notificacao_nova_tarefa(tarefa):
    """Envia notificação de nova tarefa"""
    if not tarefa.chefe_equipe or not tarefa.chefe_equipe.telefone:
        return
    
    mensagem = f"""
🌳 *SEMAPA - Nova Tarefa*

*Tipo:* {tarefa.tipo_atividade.upper()}
*Local:* {tarefa.local}
*Data:* {tarefa.data_prevista.strftime('%d/%m/%Y')}
*Horário:* {tarefa.hora_inicio or 'A definir'}

{tarefa.descricao}

Acesse o sistema para mais detalhes.
    """.strip()
    
    enviar_whatsapp(tarefa.chefe_equipe.telefone, mensagem)


def enviar_notificacao_edicao_tarefa(tarefa, alteracoes):
    """Envia notificação de edição de tarefa"""
    if not tarefa.chefe_equipe or not tarefa.chefe_equipe.telefone:
        return
    
    mensagem = f"""
⚠️ *SEMAPA - Tarefa Alterada*

*Tarefa:* {tarefa.descricao[:50]}
*Alterações:* {', '.join(alteracoes)}

Acesse o sistema para ver detalhes.
    """.strip()
    
    enviar_whatsapp(tarefa.chefe_equipe.telefone, mensagem)


def enviar_notificacao_atribuicao(trabalhador, tarefa):
    """Envia notificação de atribuição ao trabalhador"""
    if not trabalhador.telefone :
        return
    
    mensagem = f"""
👷 *SEMAPA - Tarefa Atribuída*

Olá {trabalhador.nome},

Você foi atribuído a uma nova tarefa:

*Tipo:* {tarefa.tipo_atividade.upper()}
*Local:* {tarefa.local}
*Data:* {tarefa.data_prevista.strftime('%d/%m/%Y')}
*Horário:* {tarefa.hora_inicio or 'A definir'}

Bom trabalho!
    """.strip()
    
    enviar_whatsapp(trabalhador.telefone, mensagem)


def enviar_notificacao_aprovacao_semana(session, agenda):
    """Envia notificação de aprovação da semana"""
    # Buscar chefe de equipe e trabalhadores
    tarefas = session.query(AgendaTarefa).filter_by(agenda_id=agenda.id).all()
    
    for tarefa in tarefas:
        if tarefa.chefe_equipe and tarefa.chefe_equipe.telefone:
            mensagem = f"""
✅ *SEMAPA - Agenda Aprovada*

A programação da semana {agenda.numero_semana}/{agenda.ano} foi aprovada pelo secretário.

Você pode iniciar as atividades planejadas.
            """.strip()
            
            enviar_whatsapp(tarefa.chefe_equipe.telefone, mensagem)


def enviar_whatsapp(numero, mensagem):
    """Função base para envio de mensagens WhatsApp via Twilio"""
    # TODO: Implementar integração com Twilio
    # Exemplo básico:
    """
    from twilio.rest import Client
    
    account_sid = 'SEU_ACCOUNT_SID'
    auth_token = 'SEU_AUTH_TOKEN'
    client = Client(account_sid, auth_token)
    
    message = client.messages.create(
        from_='whatsapp:+14155238886',  # Número Twilio
        to=f'whatsapp:+55{numero}',
        body=mensagem
    )
    
    return message.sid
    """
    print(f"[WHATSAPP] Para: {numero}\nMensagem: {mensagem}\n")
    pass
