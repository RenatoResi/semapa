from database import SessionLocal
from database.models import Arvore

class ArvoreService:
    @staticmethod
    def criar(data):
        session = SessionLocal()
        try:
            nova = Arvore(
                especie=data['especie'],
                endereco=data.get('endereco', ''),
                bairro=data.get('bairro', ''),
                latitude=data['latitude'],
                longitude=data['longitude'],
                data_plantio=data.get('data_plantio'),
                foto=data.get('foto', ''),
                observacao=data.get('observacao', '')
            )
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
            return session.query(Arvore).all()
        finally:
            session.close()

    @staticmethod
    def buscar_por_id(arvore_id):
        session = SessionLocal()
        try:
            return session.query(Arvore).filter_by(id=arvore_id).first()
        finally:
            session.close()
