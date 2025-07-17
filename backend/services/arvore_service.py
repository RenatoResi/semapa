from database import SessionLocal
from database.models import Arvore
from sqlalchemy.orm import joinedload

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
    @staticmethod
    def listar(com_especie=False):
        session = SessionLocal()
        try:
            query = session.query(Arvore)
            if com_especie:
                query = query.options(joinedload(Arvore.especie))
            return query.all()
        finally:
            session.close()

    @staticmethod
    def buscar_por_id(arvore_id, com_especie=False):
        session = SessionLocal()
        try:
            query = session.query(Arvore)
            if com_especie:
                query = query.options(joinedload(Arvore.especie))
            return query.filter_by(id=arvore_id).first()
        finally:
            session.close()
