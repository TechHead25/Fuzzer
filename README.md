# Fuzz-Sentinel

Intelligent continuous fuzzing and security-assurance platform.

## Setup Instructions (Phase 1 MVP)

### Prerequisites
- Docker & Docker Compose
- Node.js (v18+)
- Python 3.10+

### 1. Database & Backend Setup
```bash
# Start PostgreSQL Database
docker-compose up -d db

# Setup Python Environment
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Run Migrations
alembic upgrade head

# Start Backend Server
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```

### 3. Verify
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
