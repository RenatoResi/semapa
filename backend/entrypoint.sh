#!/bin/sh

# Cria as tabelas no banco (se ainda não existirem)
python -c "from database import criar_banco; criar_banco()"

# Cria o usuário admin caso não exista
python seed-admin.py

# Inicia o servidor Gunicorn
exec gunicorn --config gunicorn_config.py wsgi:app
