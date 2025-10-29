from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from database import SessionLocal, User
from config import config
import os

# -------------------- CONFIGURAÇÃO INICIAL --------------------

app = Flask(__name__)
app_env = os.getenv("FLASK_ENV", "development")
app.config.from_object(config[app_env])

CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})

# -------------------- FLASK-LOGIN SETUP --------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário do banco de dados"""
    session = SessionLocal()
    try:
        user = session.query(User).get(int(user_id))
        return user
    finally:
        session.close()


@login_manager.unauthorized_handler
def unauthorized():
    """Manipula acesso não autorizado"""
    from flask import redirect, url_for, flash
    flash("Você precisa estar autenticado para acessar essa página.", "warning")
    return redirect(url_for("auth.login"))


# -------------------- REGISTRO DE BLUEPRINTS --------------------

def register_blueprints(app):
    """Registra todos os Blueprints da aplicação"""
    from routes.auth_routes import auth_bp
    from routes.pages_routes import pages_bp
    from routes.tarefas_routes import tarefas_bp
    from routes.especies_routes import especies_bp
    from routes.vistorias_routes import vistorias_bp
    from routes.os_routes import os_bp
    from routes.requerimentos_routes import requerimentos_bp
    from routes.arvores_routes import arvores_bp
    from routes.requerentes_routes import requerentes_bp
    from routes.dashboard_routes import dashboard_bp

    blueprints = [
        auth_bp,
        pages_bp,
        tarefas_bp,
        especies_bp,
        vistorias_bp,
        os_bp,
        requerimentos_bp,
        arvores_bp,
        requerentes_bp,
        dashboard_bp
    ]

    for blueprint in blueprints:
        app.register_blueprint(blueprint)


register_blueprints(app)


# -------------------- MANIPULADORES DE ERRO --------------------

@app.errorhandler(404)
def not_found(error):
    """Manipulador para erro 404"""
    return {
        "error": "Página não encontrada",
        "status": 404
    }, 404


@app.errorhandler(500)
def internal_error(error):
    """Manipulador para erro 500"""
    session = SessionLocal()
    session.rollback()
    session.close()
    
    return {
        "error": "Erro interno do servidor",
        "status": 500
    }, 500


@app.errorhandler(403)
def forbidden(error):
    """Manipulador para erro 403"""
    return {
        "error": "Acesso Proibido",
        "status": 403
    }, 403


# -------------------- CONTEXT PROCESSOR --------------------

@app.shell_context_processor
def make_shell_context():
    """Contexto para shell do Flask"""
    return {'db': SessionLocal(), 'User': User}


# -------------------- MAIN --------------------

# if __name__ == "__main__":
#     app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5001)
