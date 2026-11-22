# Lance l'API FastAPI (depuis la racine du projet)
Set-Location $PSScriptRoot
& .\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload --port 8000
