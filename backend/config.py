import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurações base"""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    CORS_ORIGINS = "*"
    JSON_SORT_KEYS = False
    JSONIFY_PRETTYPRINT_REGULAR = True


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
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
