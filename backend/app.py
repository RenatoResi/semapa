import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from config import DevelopmentConfig
from database import criar_banco, SessionLocal
from routes import all_blueprints

# ---- Flask-Login ----
from flask_login import LoginManager
from database.models import User

# Carregar variáveis de ambiente (.env)
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Carregar configuração
    app.config.from_object(DevelopmentConfig)

    # Ativa CORS de forma global
    CORS(app, resources={r"/*": {"origins": "*"}})

    # Cria as tabelas do banco, se necessário
    criar_banco()

    # Configuração do Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "web.login"  # ajuste para sua rota de login

    @login_manager.user_loader
    def load_user(user_id):
        session = SessionLocal()
        user = session.query(User).get(int(user_id))
        session.close()
        return user

    # Registra todos os blueprints centralizados
    for bp in all_blueprints:
        app.register_blueprint(bp)

    # Rota de status/healthcheck (para API)
    @app.route('/api-status')
    def api_status():
        return {"status": "API rodando"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
