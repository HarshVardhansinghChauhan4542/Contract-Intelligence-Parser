# Agent Instructions - Contract Intelligence System

## Project Structure
- **Backend**: FastAPI REST API with MongoDB (`backend/`)
- **Frontend**: React application with Tailwind CSS (`frontend/`)
- **Docker**: Full containerization with docker-compose
- **Tests**: Comprehensive test suite with 60%+ coverage

## Commands

### Development
```bash
# Start full system
docker-compose up --build

# Backend development
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development  
cd frontend
npm install
npm start

# Database only
docker-compose up mongodb redis
```

### Testing
```bash
# Backend tests with coverage
cd backend
pytest --cov=app --cov-report=html
pytest tests/test_main.py  # Single test file
pytest -k "test_upload"    # Specific test

# Frontend tests
cd frontend
npm test
```

### Production
```bash
# Deploy all services
docker-compose up -d --build

# View logs
docker-compose logs -f backend
```

## Architecture
- **API**: FastAPI with async endpoints for contract processing
- **Database**: MongoDB for contract storage with indexing
- **Processing**: Background PDF parsing and AI extraction
- **Frontend**: React with real-time status updates
- **Scoring**: Weighted algorithm (Financial 30%, Parties 25%, Payment 20%, SLA 15%, Contact 10%)

## Code Style
- **Python**: PEP 8, type hints, async/await patterns
- **JavaScript**: ESLint, functional components, hooks
- **API**: RESTful design with proper status codes
- **Database**: Document-based with efficient queries
- **Testing**: Unit tests with mocking for external dependencies
