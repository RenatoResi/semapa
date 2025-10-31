# Use uma imagem base oficial do Python.
# A versão 3.9 é uma boa escolha, atendendo ao requisito de 3.8+
FROM python:3.11-slim-bookworm

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da sua aplicação para o diretório de trabalho
COPY . .

# --- Boas práticas de segurança ---
# Cria um usuário e grupo não-root
RUN addgroup --system nonroot && adduser --system --ingroup nonroot nonroot

# Muda para o usuário não-root
USER nonroot

# Expõe a porta que o Gunicorn vai usar (definida em gunicorn_config.py)
EXPOSE 5001

# Comando para iniciar a aplicação quando o contêiner for executado
# Usa a configuração que você já criou
CMD ["gunicorn", "--config", "gunicorn_config.py", "wsgi:app"]
