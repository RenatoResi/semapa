import os

class Config:
    # Configurações padrão
    SECRET_KEY = os.getenv('Ammy2025WW', 'troque_esse_valor_para_producao')
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'postgresql+psycopg2://semapa_user:Semapa2025WW@localhost/semapa_arborizacao'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Mais configs aqui...

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
