from database import SessionLocal, User
import bcrypt


def criar_admin():
    session = SessionLocal()
    admin = session.query(User).filter_by(email="admin@example.com").first()
    if not admin:
        senha = "123456"
        # Gera o hash da senha usando bcrypt (salt automático)
        senha_hash = bcrypt.hashpw(senha.encode('utf-8'), bcrypt.gensalt())
        # Decodifica para salvar no banco (string)
        senha_hash_str = senha_hash.decode('utf-8')
        admin = User(
            email="admin@example.com",
            password=senha_hash_str,
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
