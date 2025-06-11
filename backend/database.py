from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class Requerente(Base):
    __tablename__ = 'requerentes'
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    telefone = Column(String(20))
    requerimentos = relationship("Requerimento", back_populates="requerente")
    observacao = Column(Text)

class Arvore(Base):
    __tablename__ = 'arvores'
    id = Column(Integer, primary_key=True)
    especie = Column(String(100))
    endereco = Column(String(200))
    bairro = Column(String(100))
    latitude = Column(String(20))
    longitude = Column(String(20))
    data_plantio = Column(DateTime)
    foto = Column(String(200))  # Caminho/URL da foto
    requerimentos = relationship("Requerimento", back_populates="arvore")
    observacao = Column(Text)

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
    ordens_servico = relationship("OrdemServico", back_populates="requerimento")
    observacao = Column(Text)

class OrdemServico(Base):
    __tablename__ = 'ordens_servico'
    id = Column(Integer, primary_key=True)
    numero = Column(String(20), unique=True)
    data_emissao = Column(DateTime, default=datetime.now)
    data_execucao = Column(DateTime)
    responsavel = Column(String(100))  # Nome do responsável pela execução
    status = Column(String(30), default="Aberta")
    observacao = Column(Text)
    requerimento_id = Column(Integer, ForeignKey('requerimentos.id'))
    requerimento = relationship("Requerimento", back_populates="ordens_servico")

# Configuração do banco SQLite
engine = create_engine('sqlite:///../sistema_semapa.db', echo=True)
SessionLocal = sessionmaker(bind=engine)

def criar_banco():
    Base.metadata.create_all(engine)

if __name__ == "__main__":
    criar_banco()
