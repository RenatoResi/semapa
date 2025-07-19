import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv() # Carrega variáveis do .env

# ==============================
# CONFIGURAÇÃO DA CONEXÃO
# ==============================

# Pegue a URL do banco de dados do ambiente, ou use um valor padrão para desenvolvimento
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://semapa_user:Semapa2025WW@localhost/semapa_arborizacao"
)

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
