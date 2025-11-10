# start.ps1 (PowerShell script)
Write-Host "Verificando se o Docker está rodando..."
docker info > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker não está rodando. Por favor, inicie o Docker Desktop."
    exit 1
}

docker-compose up -d --build
Write-Host "Aplicação rodando em http://localhost:5001"