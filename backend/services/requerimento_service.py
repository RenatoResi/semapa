from database import SessionLocal
from database.models import Requerimento

class RequerimentoService:
    @staticmethod
    def criar(data):
        session = SessionLocal()
        try:
            novo = Requerimento(
                numero=data['numero'],
                tipo=data['tipo'],
                motivo=data['motivo'],
                prioridade=data.get('prioridade', 'Normal'),
                requerente_id=data['requerente_id'],
                arvore_id=data.get('arvore_id'),
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
            return session.query(Requerimento).all()
        finally:
            session.close()
