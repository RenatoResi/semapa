from flask import Blueprint, request, jsonify
from sqlalchemy import or_
from app.models import Especies
from config import SessionLocal
from flask_login import login_required
from app import app
import sqlalchemy as sa

bp = Blueprint('especies', __name__)


@bp.route('/api/especies_autocomplete')
@login_required
def especies_autocomplete():
    termo = request.args.get('q', '').strip()
    session = SessionLocal()
    try:
        query = session.query(Especies)
        if termo:
            termo_like = f"%{termo.lower()}%"
            query = query.filter(
                or_(
                    sa.func.lower(Especies.nome_popular).like(termo_like),
                    sa.func.lower(Especies.nome_cientifico).like(termo_like)
                )
            )
        especies = query.order_by(Especies.nome_popular).limit(20).all()
        return jsonify([
            {
                "id": e.id,
                "nome_popular": e.nome_popular,
                "nome_cientifico": e.nome_cientifico
            }
            for e in especies
        ])
    finally:
        session.close()

@bp.route('/especies', methods=['GET'])
@login_required
def listar_especies():
    session = SessionLocal()
    try:
        especies = session.query(Especies).order_by(Especies.nome_popular.asc()).all()
        return jsonify([
            {
                "id": e.id,
                "nome_popular": e.nome_popular,
                "nome_cientifico": e.nome_cientifico,
                "porte": e.porte,
                "altura_min": e.altura_min,
                "altura_max": e.altura_max,
                "longevidade_min": e.longevidade_min,
                "longevidade_max": e.longevidade_max,
                "deciduidade": e.deciduidade,
                "cor_flor": e.cor_flor,
                "epoca_floracao": e.epoca_floracao,
                "fruto_comestivel": e.fruto_comestivel,
                "epoca_frutificacao": e.epoca_frutificacao,
                "necessidade_rega": e.necessidade_rega,
                "atrai_fauna": e.atrai_fauna,
                "observacoes": e.observacoes,
                "link_foto": e.link_foto
            } for e in especies
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
        
@bp.route('/especies', methods=['POST'])
@login_required
def cadastrar_especie():
    data = request.json
    session = SessionLocal()
    try:
        nova = Especies(
            nome_popular=data['nome_popular'],
            nome_cientifico=data['nome_cientifico'],
            porte=data['porte'],
            altura_min=data.get('altura_min'),
            altura_max=data.get('altura_max'),
            longevidade_min=data.get('longevidade_min'),
            longevidade_max=data.get('longevidade_max'),
            deciduidade=data.get('deciduidade', ''),
            cor_flor=data.get('cor_flor', ''),
            epoca_floracao=data.get('epoca_floracao', ''),
            fruto_comestivel=data.get('fruto_comestivel', 'não'),
            epoca_frutificacao=data.get('epoca_frutificacao', ''),
            necessidade_rega=data.get('necessidade_rega', ''),
            atrai_fauna=data.get('atrai_fauna', 'não'),
            observacoes=data.get('observacoes', ''),
            link_foto=data.get('link_foto', '')
        )
        session.add(nova)
        session.commit()
        return jsonify({"message": "Espécie cadastrada!", "id": nova.id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()

@bp.route('/especies/<int:id>', methods=['PUT'])
@login_required
def atualizar_especie(id):
    data = request.json
    session = SessionLocal()
    try:
        especie = session.query(Especies).filter(Especies.id == id).first()
        if not especie:
            return jsonify({"error": "Espécie não encontrada"}), 404
        especie.nome_popular = data.get('nome_popular', especie.nome_popular)
        especie.nome_cientifico = data.get('nome_cientifico', especie.nome_cientifico)
        especie.porte = data.get('porte', especie.porte)
        especie.altura_min = data.get('altura_min', especie.altura_min)
        especie.altura_max = data.get('altura_max', especie.altura_max)
        especie.longevidade_min = data.get('longevidade_min', especie.longevidade_min)
        especie.longevidade_max = data.get('longevidade_max', especie.longevidade_max)
        especie.deciduidade = data.get('deciduidade', especie.deciduidade)
        especie.cor_flor = data.get('cor_flor', especie.cor_flor)
        especie.epoca_floracao = data.get('epoca_floracao', especie.epoca_floracao)
        especie.fruto_comestivel = data.get('fruto_comestivel', especie.fruto_comestivel)
        especie.epoca_frutificacao = data.get('epoca_frutificacao', especie.epoca_frutificacao)
        especie.necessidade_rega = data.get('necessidade_rega', especie.necessidade_rega)
        especie.atrai_fauna = data.get('atrai_fauna', especie.atrai_fauna)
        especie.observacoes = data.get('observacoes', especie.observacoes)
        especie.link_foto = data.get('link_foto', especie.link_foto)
        session.commit()
        return jsonify({"message": "Espécie atualizada!"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        session.close()
