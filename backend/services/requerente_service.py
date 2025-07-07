from database import SessionLocal
from database.models import Requerente

class RequerenteService:
    @staticmethod
    def criar(data):
        session = SessionLocal()
        try:
            novo = Requerente(
                nome=data['nome'],
                telefone=data.get('telefone', ''),
                observacao=data.get('observacao', '')
            )
            session.add(novo)
            session.commit()
            return novo
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def listar():
        session = SessionLocal()
        try:
            return session.query(Requerente).all()
        finally:
            session.close()
