import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, Float, Table, LargeBinary
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime
from flask_login import UserMixin
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

ordem_servico_requerimento = Table(
    'ordem_servico_requerimento', Base.metadata,
    Column('ordem_servico_id', Integer, ForeignKey('ordens_servico.id'), primary_key=True),
    Column('requerimento_id', Integer, ForeignKey('requerimentos.id'), primary_key=True)
)

class User(Base, UserMixin):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)  # Guarde apenas o hash!
    nome = Column(String(100))
    telefone = Column(String(20))
    nivel = Column(Integer, nullable=False, default=3)  # 1=admin, 2, 3, etc

    requerentes = relationship("Requerente", back_populates="user", foreign_keys='Requerente.criado_por')
    arvores = relationship("Arvore", back_populates="user", foreign_keys='Arvore.criado_por')
    requerimentos = relationship("Requerimento", back_populates="user", foreign_keys='Requerimento.criado_por')
    ordens_servico = relationship("OrdemServico", back_populates="user", foreign_keys='OrdemServico.criado_por')

class Requerente(Base):
    __tablename__ = 'requerentes'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    telefone = Column(String(20))
    requerimentos = relationship("Requerimento", back_populates="requerente")
    observacao = Column(Text)
    data_criacao = Column(DateTime, default=datetime.now)
    criado_por = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="requerentes", foreign_keys=[criado_por])
    data_atualizacao = Column(DateTime)
    atualizado_por = Column(Integer, ForeignKey('users.id'))
    atualizador = relationship("User", foreign_keys=[atualizado_por])

class Arvore(Base):
    __tablename__ = 'arvores'
    id = Column(Integer, primary_key=True)
    endereco = Column(String(200))
    bairro = Column(String(100))
    latitude = Column(String(20))
    longitude = Column(String(20))
    data_plantio = Column(DateTime)
    especie_id = Column(Integer, ForeignKey('especies.id'))
    foto = Column(String(200))
    requerimentos = relationship("Requerimento", back_populates="arvore")
    observacao = Column(Text)
    data_criacao = Column(DateTime, default=datetime.now)
    criado_por = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="arvores", foreign_keys=[criado_por])
    data_atualizacao = Column(DateTime)
    atualizado_por = Column(Integer, ForeignKey('users.id'))
    especie = relationship("Especies", back_populates="arvores")
    atualizador = relationship("User", foreign_keys=[atualizado_por])

class Requerimento(Base):
    __tablename__ = 'requerimentos'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), unique=True)
    data_abertura = Column(DateTime, default=datetime.now)
    tipo = Column(Text)
    motivo = Column(Text)
    status = Column(String(30), default="Pendente")
    prioridade = Column(String(20), default="Normal")
    requerente_id = Column(Integer, ForeignKey('requerentes.id'))
    arvore_id = Column(Integer, ForeignKey('arvores.id'))
    requerente = relationship("Requerente", back_populates="requerimentos")
    arvore = relationship("Arvore", back_populates="requerimentos")
    observacao = Column(Text)
    data_criacao = Column(DateTime, default=datetime.now)
    criado_por = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="requerimentos", foreign_keys=[criado_por])
    data_atualizacao = Column(DateTime)
    atualizado_por = Column(Integer, ForeignKey('users.id'))
    atualizador = relationship("User", foreign_keys=[atualizado_por])
    # RELAÇÃO CORRETA: muitos-para-muitos com OrdemServico
    ordens_servico = relationship(
        "OrdemServico",
        secondary=ordem_servico_requerimento,
        back_populates="requerimentos"
    )
    
class Vistoria(Base):
    __tablename__ = 'vistoria'
    id = Column(Integer, primary_key=True)
    requerimento_id = Column(Integer, ForeignKey('requerimentos.id', ondelete="CASCADE"), nullable=False)
    vistoria_data = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="SET NULL"), nullable=True)
    status = Column(String(30), nullable=False, default="Pendente")
    observacoes = Column(Text)
    especie_id = Column(Integer, ForeignKey('especies.id'))
    condicoes = Column(Text)  # Armazenará JSON ou string delimitada
    conflitos = Column(Text)
    risco_queda = Column(String(10))
    diagnostico = Column(Text)
    acao_recomendada = Column(String(20))
    tipo_poda = Column(Text)
    galhos_cortar = Column(Text)
    medidas_seguranca = Column(Text)
    observacoes_tecnicas = Column(Text)

    especie = relationship("Especies")
    requerimento = relationship("Requerimento", backref="vistorias")
    user = relationship("User", backref="vistorias")
    fotos = relationship("VistoriaFoto", back_populates="vistoria", cascade="all, delete-orphan")

class VistoriaFoto(Base):
    __tablename__ = 'vistoria_foto'
    id = Column(Integer, primary_key=True)
    vistoria_id = Column(Integer, ForeignKey('vistoria.id', ondelete="CASCADE"), nullable=False)
    arquivo_nome = Column(String(255))
    arquivo = Column(LargeBinary, nullable=False)  # Use BYTEA no banco, mas pode usar LargeBinary no SQLAlchemy

    vistoria = relationship("Vistoria", back_populates="fotos")
    
class OrdemServico(Base):
    __tablename__ = 'ordens_servico'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), unique=True)
    data_emissao = Column(DateTime, default=datetime.now)
    data_execucao = Column(DateTime)
    responsavel = Column(String(100))
    status = Column(String(30), default="Aberta")
    observacao = Column(Text)
    criado_por = Column(Integer, ForeignKey('users.id'))
    user = relationship("User", back_populates="ordens_servico", foreign_keys=[criado_por])
    data_atualizacao = Column(DateTime)
    atualizado_por = Column(Integer, ForeignKey('users.id'))
    atualizador = relationship("User", foreign_keys=[atualizado_por])
    # RELAÇÃO CORRETA: muitos-para-muitos com Requerimento
    requerimentos = relationship(
        "Requerimento",
        secondary=ordem_servico_requerimento,
        back_populates="ordens_servico"
    )

class Especies(Base):
    __tablename__ = 'especies'
    id = Column(Integer, primary_key=True)
    nome_popular = Column(String(100), unique=True, nullable=False)
    nome_cientifico = Column(String(150), nullable=False)
    porte = Column(String(20), nullable=False)  # pequeno, medio_grande
    altura_min = Column(Float)
    altura_max = Column(Float)
    longevidade_min = Column(Integer)
    longevidade_max = Column(Integer)
    deciduidade = Column(String(30))
    cor_flor = Column(String(50))
    epoca_floracao = Column(String(50))
    fruto_comestivel = Column(String(10))  # 'sim' ou 'não'
    epoca_frutificacao = Column(String(50))
    necessidade_rega = Column(String(20))
    atrai_fauna = Column(String(10))  # 'sim' ou 'não'
    observacoes = Column(Text)
    link_foto = Column(String(200))  # Caminho/URL da foto
    arvores = relationship("Arvore", back_populates="especie")

    def __repr__(self):
        return f"<Especies(nome_popular='{self.nome_popular}', nome_cientifico='{self.nome_cientifico}')>"

# === INTEGRAÇÃO DE AGENDA SEMANAL ===

class AgendaSemanal(Base):
    __tablename__ = 'agenda_semanal'
    id = Column(Integer, primary_key=True)
    semana_inicio = Column(DateTime, nullable=False)
    semana_fim = Column(DateTime, nullable=False)
    ano = Column(Integer, nullable=False)
    numero_semana = Column(Integer, nullable=False)
    aprovada = Column(Integer, default=0)
    aprovada_por = Column(Integer, ForeignKey('users.id'))
    aprovada_em = Column(DateTime)
    criada_por = Column(Integer, ForeignKey('users.id'), nullable=False)
    criada_em = Column(DateTime, default=datetime.now)
    atualizada_em = Column(DateTime, default=datetime.now)
    tarefas = relationship("AgendaTarefa", back_populates="agenda", cascade="all, delete-orphan")
    criador = relationship("User", foreign_keys=[criada_por])
    aprovador = relationship("User", foreign_keys=[aprovada_por])

class AgendaTarefa(Base):
    __tablename__ = 'agenda_tarefas'
    id = Column(Integer, primary_key=True)
    agenda_id = Column(Integer, ForeignKey('agenda_semanal.id'), nullable=False)
    descricao = Column(Text, nullable=False)
    tipo_atividade = Column(String(50), nullable=False)  # poda, plantio, etc
    local = Column(Text, nullable=False)
    endereco = Column(Text)
    latitude = Column(Float)
    longitude = Column(Float)
    data_prevista = Column(DateTime, nullable=False)
    hora_inicio = Column(String(10))
    hora_fim = Column(String(10))
    prioridade = Column(String(20), default='normal')
    status = Column(String(30), default='planejada')
    observacoes = Column(Text)
    chefe_equipe_id = Column(Integer, ForeignKey('users.id'))
    criada_por = Column(Integer, ForeignKey('users.id'), nullable=False)
    criada_em = Column(DateTime, default=datetime.now)
    atualizada_em = Column(DateTime, default=datetime.now)
    concluida_em = Column(DateTime)
    agenda = relationship("AgendaSemanal", back_populates="tarefas")
    trabalhadores = relationship("AgendaTarefaTrabalhador", back_populates="tarefa", cascade="all, delete-orphan")
    historico = relationship("AgendaHistorico", back_populates="tarefa", cascade="all, delete-orphan")
    chefe_equipe = relationship("User", foreign_keys=[chefe_equipe_id])
    criador = relationship("User", foreign_keys=[criada_por])

class AgendaTarefaTrabalhador(Base):
    __tablename__ = 'agenda_tarefas_trabalhadores'
    id = Column(Integer, primary_key=True)
    tarefa_id = Column(Integer, ForeignKey('agenda_tarefas.id'), nullable=False)
    trabalhador_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    atribuido_em = Column(DateTime, default=datetime.now)
    atribuido_por = Column(Integer, ForeignKey('users.id'), nullable=False)
    tarefa = relationship("AgendaTarefa", back_populates="trabalhadores")
    trabalhador = relationship("User", foreign_keys=[trabalhador_id])
    atribuidor = relationship("User", foreign_keys=[atribuido_por])

class AgendaHistorico(Base):
    __tablename__ = 'agenda_historico'
    id = Column(Integer, primary_key=True)
    tarefa_id = Column(Integer, ForeignKey('agenda_tarefas.id'), nullable=False)
    usuario_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    acao = Column(String(50), nullable=False)  # criada, editada, concluida, etc
    descricao = Column(Text)
    data_hora = Column(DateTime, default=datetime.now)
    tarefa = relationship("AgendaTarefa", back_populates="historico")
    usuario = relationship("User", foreign_keys=[usuario_id])

# === FIM INTEGRAÇÃO DE AGENDA SEMANAL ===

# ==============================
# CONFIGURAÇÃO DO BANCO POSTGRES
# ==============================

# Pegue a URL do banco de dados do ambiente, ou use um valor padrão para testes
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

def criar_banco():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    criar_banco()
