import os
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from config import DevelopmentConfig
from database import criar_banco, SessionLocal
from routes import all_blueprints

from flask_login import LoginManager
from database.models import User

# Carrega variáveis de ambiente (.env)
load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig)
    CORS(app, resources={r"/*": {"origins": "*"}})
    criar_banco()

    # Configuração do Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "web.login"

    @login_manager.user_loader
    def load_user(user_id):
        session = SessionLocal()
        user = session.query(User).get(int(user_id))
        session.close()
        return user

    # Registra todos os blueprints
    for bp in all_blueprints:
        app.register_blueprint(bp)

    # Healthcheck/API status
    @app.route('/api-status')
    def api_status():
        return {"status": "API rodando"}

    # --- Handlers globais de erro para garantir JSON ---
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"error": "Internal server error"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
