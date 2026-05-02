#!/usr/bin/env python3
"""
Script de migração para adicionar coluna data_conclusao na tabela requerimentos
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def migrate():
    engine = create_engine(DATABASE_URL, echo=True)
    with engine.connect() as conn:
        # Adicionar coluna data_conclusao
        sql = """
        ALTER TABLE requerimentos
        ADD COLUMN IF NOT EXISTS data_conclusao TIMESTAMP;
        """
        conn.execute(text(sql))
        conn.commit()
        print("Coluna data_conclusao adicionada com sucesso!")

if __name__ == "__main__":
    migrate()