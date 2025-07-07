from flask import Flask
from flask_cors import CORS
from database import criar_banco
from routes.arvore import arvore_bp
from routes.requerente import requerente_bp
from routes.requerimento import requerimento_bp
from routes.ordem_servico import ordem_servico_bp

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    criar_banco()

    app.register_blueprint(arvore_bp)
    app.register_blueprint(requerente_bp)
    app.register_blueprint(requerimento_bp)
    app.register_blueprint(ordem_servico_bp)

    @app.route('/')
    def index():
        return {"status": "API rodando"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
