# SEMAPA - Backend do Sistema de Gestão


## 🌳 Sobre o Projeto


Este é o serviço de backend para o sistema SEMAPA. Construído com Flask, ele fornece uma API RESTful para gerenciar as principais entidades do sistema, como usuários, requerentes, árvores, requerimentos, ordens de serviço e vistorias.


O sistema é projetado para ser modular, utilizando Flask Blueprints para separar as responsabilidades de cada recurso.


## 🛠️ Tecnologias Utilizadas


- **Framework**: Flask
- **ORM**: SQLAlchemy
- **Autenticação**: Flask-Login
- **Banco de Dados**: Suporte para PostgreSQL (produção/desenvolvimento) e SQLite (testes)
- **Gerenciamento de Ambiente**: `python-dotenv`
- **CORS**: `Flask-Cors`


## 📁 Estrutura do Projeto


```
backend/
├── app.py                 # Ponto de entrada da aplicação, configuração do Flask e blueprints
├── config.py              # Classes de configuração para diferentes ambientes (Dev, Prod, Test)
├── database.py            # Definição dos modelos SQLAlchemy e configuração do banco de dados
├── requirements.txt       # Dependências do projeto
├── .env                   # Arquivo para variáveis de ambiente (NÃO versionar)
├── routes/                # Módulos com as rotas (Blueprints)
│   ├── auth_routes.py
│   ├── arvores_routes.py
│   ├── os_routes.py
│   └── ...
└── temp/                  # Diretório temporário para arquivos gerados (ex: KML)
```


## 🚀 Como Executar


### 1. Pré-requisitos


- Python 3.8+
- PostgreSQL 17
- Docker e Docker Compose (recomendado para desenvolvimento consistente em múltiplos ambientes)
- Um ambiente virtual (opcional para execução local sem Docker)


### 2. Instalação e Configuração Local


```bash
# Clone o repositório
git clone <url-do-repositorio>
cd semapa/backend

# Crie e ative ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Instale dependências
pip install -r requirements.txt
```

Crie o arquivo `.env` na raiz do backend com as variáveis:

```env
SECRET_KEY="sua-chave-secreta-aqui"
DATABASE_URL="postgresql://usuario:senha@host:porta/nome_do_banco"
FLASK_ENV="development"
```

Para rodar localmente:

```bash
python app.py
```

Ou com flask e gunicorn:

```bash
flask run
gunicorn --config gunicorn_config.py wsgi:app
```

***

### 3. Usando Docker e Docker Compose (altamente recomendado)


##### Arquivo `docker-compose.yml` (exemplo):

```yaml
version: "3.9"
services:
  db:
    image: postgres:17
    container_name: semapa-db
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-semapa}
      POSTGRES_USER: ${POSTGRES_USER:-semapa}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-semapa}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-semapa} -d ${POSTGRES_DB:-semapa}"]
      interval: 5s
      timeout: 5s
      retries: 12
      start_period: 5s

  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: semapa-backend
    depends_on:
      db:
        condition: service_healthy
    environment:
      SECRET_KEY: ${SECRET_KEY}
      FLASK_ENV: ${FLASK_ENV:-production}
      DATABASE_URL: ${DATABASE_URL:-postgresql://${POSTGRES_USER:-semapa}:${POSTGRES_PASSWORD:-semapa}@db:5432/${POSTGRES_DB:-semapa}}
      GUNICORN_BIND: ${GUNICORN_BIND:-0.0.0.0:5001}
      GUNICORN_WORKERS: ${GUNICORN_WORKERS:-3}
    ports:
      - "5001:5001"
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "wget -qO- http://localhost:5001/ || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 6
      start_period: 15s

volumes:
  pgdata:
```

##### Arquivo `.env` para Docker Compose:

```env
SECRET_KEY=troque-isto
FLASK_ENV=development
POSTGRES_DB=semapa
POSTGRES_USER=semapa
POSTGRES_PASSWORD=secreto123
DATABASE_URL=postgresql://semapa:secreto123@db:5432/semapa
GUNICORN_BIND=0.0.0.0:5001
GUNICORN_WORKERS=3
```

***

### 4. Scripts para facilitar execução


Crie um script `start.sh` para facilitar o uso:

```bash
#!/bin/bash
if ! systemctl is-active --quiet docker; then
  echo "Docker não está rodando. Iniciando..."
  sudo systemctl start docker
fi

docker compose up -d --build
echo "Aplicação rodando em http://localhost:5001"
```

Use:

```bash
chmod +x start.sh
./start.sh
```

***

### 5. Comandos úteis


- Subir containers com build: `docker compose up -d --build`
- Acompanhar logs: `docker compose logs -f backend`
- Criar tabelas no banco: `docker compose exec backend python database.py`
- Parar e limpar containers e volumes: `docker compose down -v`

***

### 6. Suporte para banco SQLite (testes)


Para testes rápidos e sem dependência de PostgreSQL, configure:

```env
DATABASE_URL=sqlite:///:memory:
```

E rode localmente, sem Docker.

***

## ✨ Funcionalidades Principais


- Autenticação de usuários com controle de acesso.
- API REST para CRUD de Requerentes, Árvores, Espécies, Requerimentos, Ordens de Serviço e Vistorias.
- Geração de arquivos KML para visualização de árvores em mapas.
- Configuração flexível para desenvolvimento local, testes e produção via Docker.

***

Este README dá instruções claras para rodar o projeto em qualquer ambiente, priorizando Docker para replicabilidade e facilidade, e mostrando a opção tradicional local para iniciantes. As dicas de scripts e configuração reduzem atritos iniciais com Docker.