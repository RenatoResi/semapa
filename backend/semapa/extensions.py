from flask_login import LoginManager
from ..database import SessionLocal
from .models import User

login_manager = LoginManager()
login_manager.login_view = "auth.login" # Rota de login agora está no blueprint 'auth'

@login_manager.user_loader
def load_user(user_id):
    session = SessionLocal()
    user = session.query(User).get(int(user_id))
    session.close() # Fechar a sessão específica do user_loader
    return user