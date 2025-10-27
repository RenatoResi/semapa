"""
Arquivo de configuração do Gunicorn.
"""
import os

# --- Socket Binding ---
# Endereço e porta em que o Gunicorn vai escutar.
# '0.0.0.0' permite conexões de fora do container/máquina.
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:5001')

# --- Worker Processes ---
# O número de workers a serem iniciados.
# Uma regra comum é (2 * número de cores da CPU) + 1.
# Ajuste conforme o seu hardware e testes de carga.
workers = int(os.environ.get('GUNICORN_WORKERS', '3'))

# --- Logging ---
# Onde os logs de acesso e erro serão escritos.
# '-' significa que serão enviados para a saída padrão (stdout).
accesslog = '-'
errorlog = '-'

# --- Process Naming ---
# Um nome para o processo, útil para monitoramento.
proc_name = 'semapa-backend'
