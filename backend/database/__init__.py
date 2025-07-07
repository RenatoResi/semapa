import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base  # importa todos os modelos definidos
# Garante que as tabelas sejam registradas no metadata

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://semapa_user:Semapa2025WW@localhost/semapa_arborizacao"
)

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)

def criar_banco():
    Base.metadata.create_all(engine)
