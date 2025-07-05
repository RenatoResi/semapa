# utils.py
from sqlalchemy import text
from database import SessionLocal  # importe sua sessionmaker

def reset_all_sequences():
    stmts = [
        "SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1) + 1, false);",
        "SELECT setval('requerentes_id_seq', COALESCE((SELECT MAX(id) FROM requerentes), 1) + 1, false);",
        "SELECT setval('arvores_id_seq', COALESCE((SELECT MAX(id) FROM arvores), 1) + 1, false);",
        "SELECT setval('requerimentos_id_seq', COALESCE((SELECT MAX(id) FROM requerimentos), 1) + 1, false);",
        "SELECT setval('ordens_servico_id_seq', COALESCE((SELECT MAX(id) FROM ordens_servico), 1) + 1, false);",
        "SELECT setval('especies_id_seq', COALESCE((SELECT MAX(id) FROM especies), 1) + 1, false);",
        "SELECT setval('vistoria_id_seq', COALESCE((SELECT MAX(id) FROM vistoria), 1) + 1, false);",
        "SELECT setval('vistoria_foto_id_seq', COALESCE((SELECT MAX(id) FROM vistoria_foto), 1) + 1, false);"
    ]
    session = SessionLocal()
    try:
        for stmt in stmts:
            session.execute(text(stmt))
        session.commit()
    finally:
        session.close()
