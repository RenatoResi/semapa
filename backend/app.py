from flask import Flask
from flask_cors import CORS
from database import criar_banco
from routes import all_blueprints

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}})
    criar_banco()

    for bp in all_blueprints:
        app.register_blueprint(bp)

    @app.route('/')
    def index():
        return {"status": "API rodando"}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
