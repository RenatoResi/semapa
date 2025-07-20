from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Inicializar extensões
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Faça login para acessar esta página.'
    
    # Registrar blueprints
    from app.blueprints.cadastro import bp as cadastro_bp
    from app.blueprints.requerimento import bp as requerimento_bp
    from app.blueprints.especies import bp as especies_bp
    from app.blueprints.inventario import bp as inventario_bp
    from app.blueprints.vistoria import bp as vistoria_bp
    from app.blueprints.auth import bp as auth_bp
    from app.blueprints.os import bp as os_bp
    
    app.register_blueprint(cadastro_bp, url_prefix='/cadastro')
    app.register_blueprint(requerimento_bp, url_prefix='/requerimento')
    app.register_blueprint(especies_bp, url_prefix='/especies')
    app.register_blueprint(inventario_bp, url_prefix='/inventario')
    app.register_blueprint(vistoria_bp, url_prefix='/vistoria')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(os_bp, url_prefix='/os')
    
    # Rota principal protegida
    from flask_login import login_required

    @app.route('/')
    @login_required
    def index():
        return render_template('index.html')
    
    # User loader do Flask-Login
    from app.models.database import users

    @login_manager.user_loader
    def load_user(user_id):
        return users.query.get(int(user_id))

    return app
