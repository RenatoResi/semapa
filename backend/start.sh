#!/bin/bash
if ! systemctl is-active --quiet docker; then
  echo "Docker não está rodando. Iniciando..."
  sudo systemctl start docker
fi

docker-compose up -d --build
echo "Aplicação rodando em http://localhost:5001"