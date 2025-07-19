from semapa import create_app

app = create_app()

if __name__ == "__main__":
    # O modo debug, host e porta podem ser lidos da configuração
    app.run(debug=app.config.get("DEBUG"), host=app.config.get("HOST"), port=app.config.get("PORT"))