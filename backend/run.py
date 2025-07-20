import os
from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
from dotenv import load_dotenv

# Importar blueprints dos módulos
from semapa.arvores import arvores_bp
from semapa.auth import auth_bp
from semapa.especies import especies_bp
from semapa.main import main_bp
from semapa.os import os_bp
from semapa.requerimentos import requerimentos_bp
from semapa.vistorias import vistorias_bp

load_dotenv()  # Carrega variáveis do .env

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "SUA_CHAVE_SECRETA_AQUI")
CORS(app, resources={r"/*": {"origins": "*"}})

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

# Registrar blueprints
app.register_blueprint(arvores_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(especies_bp)
app.register_blueprint(main_bp)
app.register_blueprint(os_bp)
app.register_blueprint(requerimentos_bp)
app.register_blueprint(vistorias_bp)

# Exemplo de user_loader (ajuste conforme seu modelo User)
from semapa.models import SessionLocal, User
@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    user = session.query(User).get(int(user_id))
    session.close()
    return user

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
