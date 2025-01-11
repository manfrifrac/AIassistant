# Rimuovi tutte le directory __pycache__ e i file .pyc ricorsivamente
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force
Get-ChildItem -Path . -Filter "*.pyc" -Recurse -File | Remove-Item -Force

# Rimuovi la directory .pytest_cache se esiste
if (Test-Path ".pytest_cache") { Remove-Item ".pytest_cache" -Recurse -Force }

# Rimuovi la directory .mypy_cache se esiste
if (Test-Path ".mypy_cache") { Remove-Item ".mypy_cache" -Recurse -Force }

# Rimuovi la directory .ruff_cache se esiste
if (Test-Path ".ruff_cache") { Remove-Item ".ruff_cache" -Recurse -Force }

Write-Host "Cache Python rimossa con successo!"