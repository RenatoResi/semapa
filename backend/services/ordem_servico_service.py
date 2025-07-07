from database import SessionLocal
from database.models import OrdemServico

class OrdemServicoService:
    @staticmethod
    def criar(data):
        session = SessionLocal()
        try:
            nova = OrdemServico(
                numero=data['numero'],
                responsavel=data['responsavel'],
                requerimento_id=data['requerimento_id'],
                observacao=data.get('observacao', '')
            )
            if 'data_execucao' in data:
                nova.data_execucao = data['data_execucao']
            session.add(nova)
            session.commit()
            return nova
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    @staticmethod
    def listar():
        session = SessionLocal()
        try:
            return session.query(OrdemServico).all()
        finally:
            session.close()
