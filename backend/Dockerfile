# Use uma imagem base oficial do Python.
# A versão 3.11 é adequada, atende requisito 3.8+
FROM python:3.11-slim-bookworm

# Define o diretório de trabalho dentro do contêiner
WORKDIR /app

# Copia o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código da sua aplicação para o diretório de trabalho
COPY . .

# Copia o script de entrypoint e dá permissão de execução
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# --- Boas práticas de segurança ---
# Cria um usuário e grupo não-root
RUN addgroup --system nonroot && adduser --system --ingroup nonroot nonroot

# Muda para o usuário não-root
USER nonroot

# Expõe a porta que o Gunicorn vai usar (definida em gunicorn_config.py)
EXPOSE 5001

# Usa o entrypoint personalizado para criar admin e iniciar Gunicorn
CMD ["./entrypoint.sh"]
