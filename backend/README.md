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
- Um ambiente virtual (recomendado)

### 2. Instalação

```bash
# Clone o repositório (se ainda não o fez)
# git clone <url-do-repositorio>
# cd semapa/backend

# Crie e ative um ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
# source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 3. Configuração do Ambiente

Crie um arquivo chamado `.env` na raiz do diretório `backend/` e adicione as seguintes variáveis:

```env
# Chave secreta para o Flask (use um valor aleatório e seguro)
SECRET_KEY="sua-chave-secreta-aqui"

# URL de conexão com o banco de dados PostgreSQL
DATABASE_URL="postgresql://usuario:senha@host:porta/nome_do_banco"

# Ambiente da aplicação (development, production, testing)
FLASK_ENV="development"
```

### 4. Inicialização do Banco de Dados

Se for a primeira vez executando com um novo banco de dados, as tabelas precisam ser criadas. O script `database.py` pode ser executado para isso, ou a aplicação principal pode ser configurada para fazer isso na inicialização.

### 5. Execução

```bash
# Inicie o servidor de desenvolvimento do Flask
python app.py
```
# Digitar no terminal:
$env:FLASK_ENV = "development"
flask run
# Ou entao
gunicorn --config gunicorn_config.py wsgi:app


A aplicação estará disponível em `http://0.0.0.0:5001`.

## ✨ Funcionalidades Principais

- Autenticação de usuários com controle de acesso.
- API para CRUD de Requerentes, Árvores, Espécies, Requerimentos, Ordens de Serviço e Vistorias.
- Geração de arquivos KML para visualização de árvores em mapas.
- Sistema de configuração flexível para diferentes ambientes.
