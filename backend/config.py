import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações base"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    # Em produção, nunca use "*". Carregue de uma variável de ambiente.
    # O valor deve ser uma lista de origens permitidas.
    # Ex: CORS_ALLOWED_ORIGINS="https://meu-frontend.com,https://outro-frontend.com"
    CORS_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(',')
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    CACHE_TYPE = 'memcached'
    CACHE_MEMCACHED_SERVERS = [os.environ.get('MEMCACHED_SERVERS', '127.0.0.1:11211')]


class DevelopmentConfig(Config):
    """Configurações de desenvolvimento"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configurações de produção"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """Configurações de teste"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///sistema_semapa.db"  # Usa o arquivo real


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
