# SEMAPA — Arborização Urbana

**Backend Flask para gerenciamento de árvores, requerimentos, vistorias e ordens de serviço urbanas.**

---

## Estrutura do Projeto

backend/
├── app.py
├── config.py
├── database/
│ ├── init.py
│ └── models.py
├── routes/
│ ├── init.py
│ ├── arvore.py
│ ├── requerente.py
│ ├── requerimento.py
│ └── ordem_servico.py
├── schemas/
│ ├── init.py
│ ├── arvore_schema.py
│ ├── requerente_schema.py
│ ├── requerimento_schema.py
│ └── ordem_servico_schema.py
├── services/
│ ├── init.py
│ ├── arvore_service.py
│ ├── requerente_service.py
│ ├── requerimento_service.py
│ └── ordem_servico_service.py
├── utils/
│ ├── init.py
│ ├── kml_utils.py
│ ├── response_utils.py
│ └── validation_utils.py
├── static/
│ └── ...
├── templates/
│ └── ...
├── temp/
│ └── ...
├── tests/
│ ├── init.py
│ └── test_arvore.py
└── requirements.txt


## Instalação

1. **Clone o repositório e acesse a pasta**  
   `git clone ...`  
   `cd repos/semapa/backend`

2. **Crie o ambiente virtual:**  
   `python -m venv venv`  
   `source venv/bin/activate` (Linux/macOS)  
   `venv\Scripts\activate` (Windows)

3. **Instale as dependências:**  
   `pip install -r requirements.txt`

4. **Configure o arquivo `.env`:**
   - Crie um arquivo `.env` e adicione:
     ```
     SECRET_KEY=<sua chave ultra-secreta, ex: saída do secrets.token_urlsafe(32)>
     DATABASE_URL=postgresql+psycopg2://usuario:senha@localhost/nome_banco
     ```

5. **Inicialize o banco de dados:**  
   O banco de dados é criado automaticamente ao subir a aplicação.

6. **Execute a aplicação:**  
   `python app.py`

## Testes

- **Automatizados:**  
  `pytest`
- **Manuais:**  
  Use Postman/Insomnia para testar os endpoints.

## Endpoints Principais

- `GET /arvores`  
- `POST /arvores`  
- `GET /arvores/{id}`  
- `GET /gerar_kml`, `GET /gerar_kml/{id}`  
- `GET /requerentes`, `POST /requerente`  
- `GET /requerimentos`, `POST /requerimento`  
- `GET /ordens_servico`, `POST /ordens_servico`

(veja código para mais detalhes)

## Padrão de Código

- **Arquitetura modular:** cada domínio tem seu blueprint, service e schema.
- **Configurações centralizadas em `config.py` e `.env`.**
- **Padronização de mensagens e tratamento de erros.**
- **Utilitários em `utils/`.**

---

**Colabore!**  
Sugestões, contribuições e issues são bem-vindos.
