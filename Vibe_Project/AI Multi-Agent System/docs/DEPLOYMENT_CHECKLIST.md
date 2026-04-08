# Deployment Checklist

## Pre-Deployment Checks

### 1. Environment
- [ ] Python 3.10+
- [ ] Docker Desktop
- [ ] Git

### 2. Dependencies
- [ ] pip install -r requirements.txt
- [ ] Vector DB running
- [ ] LLM configured

### 3. Tests
- [ ] pytest tests/test_health_api.py
- [ ] App loads

## Deployment

### Docker (Recommended)
docker build -t ai-multi-agent .
docker-compose up -d

### Local
pip install -r requirements.txt
pytest tests/
uvicorn api.main:app --reload
