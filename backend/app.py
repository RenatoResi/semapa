from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from database import get_session, User
from config import config
from flask_caching import Cache
from errors import register_error_handlers
import os

# -------------------- CONFIGURAÇÃO INICIAL --------------------

app = Flask(__name__)
app_env = os.getenv("FLASK_ENV", "development")
app.config.from_object(config[app_env])

CORS(app, resources={r"/*": {"origins": app.config['CORS_ORIGINS']}})
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# -------------------- FLASK-LOGIN SETUP --------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"


@login_manager.user_loader
def load_user(user_id):
    """Carrega usuário do banco de dados"""
    with get_session() as session:
        user = session.query(User).get(int(user_id))
        return user


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

# -------------------- REGISTRANDO MANIPULADORES DE ERRO --------------------

register_error_handlers(app)


# -------------------- CONTEXT PROCESSOR --------------------

@app.shell_context_processor
def make_shell_context():
    """Contexto para shell do Flask"""
    from database import SessionLocal
    return {'db': SessionLocal(), 'User': User}


# -------------------- MAIN --------------------

# if __name__ == "__main__":
#     app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=5001)
