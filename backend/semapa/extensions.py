from flask import Flask, g
from flask_cors import CORS
from config import Config
from .extensions import login_manager
from database import SessionLocal

def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Inicializar extensões
    CORS(app, resources={r"/*": {"origins": "*"}})
    login_manager.init_app(app)

    # Registrar Blueprints
    from .auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    from .requerentes.routes import requerentes_bp
    app.register_blueprint(requerentes_bp, url_prefix='/api')

    from .arvores.routes import arvores_bp
    app.register_blueprint(arvores_bp, url_prefix='/api')

    from .requerimentos.routes import requerimentos_bp
    app.register_blueprint(requerimentos_bp, url_prefix='/api')

    from .os.routes import os_bp
    app.register_blueprint(os_bp, url_prefix='/api')

    from .vistorias.routes import vistorias_bp
    app.register_blueprint(vistorias_bp, url_prefix='/api')

    from .especies.routes import especies_bp
    app.register_blueprint(especies_bp, url_prefix='/api')

    @app.before_request
    def before_request():
        g.db = SessionLocal()

    @app.teardown_request
    def teardown_request(exception=None):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    return app