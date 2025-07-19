import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'SUA_CHAVE_SECRETA_AQUI_MUDE_ISSO'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'sqlite:///../sistema_semapa.db'
    
    # Configurações de execução
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    HOST = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_RUN_PORT', 5000))

