from database import SessionLocal, User
from werkzeug.security import generate_password_hash

def criar_admin():
    session = SessionLocal()
    admin = session.query(User).filter_by(email="admin@example.com").first()
    if not admin:
        senha_hash = generate_password_hash("123456")
        admin = User(
            email="admin@example.com",
            password=senha_hash,
            nome="Administrador",
            nivel=1,
            ativo='True',
            telefone=""  # Pode retirar ou deixar em branco
        )
        session.add(admin)
        session.commit()
        print("Usuário admin criado")
    else:
        print("Usuário admin já existe")
    session.close()

if __name__ == "__main__":
    criar_admin()
