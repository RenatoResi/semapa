#!/bin/sh
python seed_admin.py          # cria usuário admin caso não exista
exec gunicorn --config gunicorn_config.py wsgi:app  # inicia o servidor Gunicorn
