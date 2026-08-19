Write-Host "Setting up Fuzz-Sentinel local environment..."

# 1. Setup Backend
Write-Host "Setting up Backend..."
cd ../backend
if (-not (Test-Path "venv")) {
    python -m venv venv
}
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
cd ..

# 2. Setup Frontend
Write-Host "Setting up Frontend..."
cd frontend
npm install
cd ..

Write-Host "Setup complete!"
