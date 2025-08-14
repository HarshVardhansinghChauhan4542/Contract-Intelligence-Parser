# Contract Intelligence System

A comprehensive contract analysis platform that automatically extracts critical financial and operational data from PDF contracts, providing completeness scoring and gap analysis for accounts receivable management.

## 🏗️ Architecture

The system follows a microservices architecture with the following components:

- **Backend**: FastAPI REST API with asynchronous processing
- **Database**: MongoDB for contract data storage  
- **Frontend**: React/Next.js web application with responsive design
- **Processing**: Background contract parsing with PDF extraction
- **Deployment**: Fully containerized with Docker Compose

## 📋 Features

### Core Functionality
- **PDF Contract Upload**: Drag-and-drop interface with 50MB file size limit
- **Asynchronous Processing**: Background contract analysis with real-time status tracking
- **Intelligent Data Extraction**: Automated extraction of:
  - Contract parties and signatories
  - Financial details (amounts, currency, line items)
  - Payment structure (terms, methods, schedules)
  - Revenue classification (recurring/one-time, billing cycles)
  - Service Level Agreements (SLAs, performance metrics)
  - Account information (billing details, contact info)

### Scoring & Analysis
- **Weighted Scoring System** (0-100 points):
  - Financial completeness: 30 points
  - Party identification: 25 points  
  - Payment terms clarity: 20 points
  - SLA definition: 15 points
  - Contact information: 10 points
- **Gap Analysis**: Identifies missing critical fields with priority levels
- **Confidence Scores**: Per-category extraction confidence ratings

### User Interface
- **Contract Upload**: Intuitive drag-and-drop interface
- **Contract Library**: Paginated list with filtering and search
- **Detailed Analysis**: Comprehensive contract data visualization
- **Real-time Status**: Live processing progress tracking
- **Responsive Design**: Mobile and desktop optimized

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Optional: Free Hugging Face API key for enhanced AI extraction

### 1. Clone the Repository
```bash
git clone <repository-url>
cd contract-intelligence-system
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env file and add your FREE Hugging Face API key (optional)
# Get free key from: https://huggingface.co/settings/tokens
```

### 3. Start the System
```bash
docker-compose up --build
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🛠️ Development Setup

### Backend Development
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB and Redis (via Docker)
docker-compose up mongodb redis

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Running Tests
```bash
cd backend

# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_main.py

# Run with coverage report
pytest --cov=app --cov-report=html
```

## 📡 API Endpoints

### Contract Management
- `POST /contracts/upload` - Upload contract for processing
- `GET /contracts/{contract_id}/status` - Get processing status
- `GET /contracts/{contract_id}` - Get extracted contract data
- `GET /contracts` - List contracts with filtering
- `GET /contracts/{contract_id}/download` - Download original file

### System
- `GET /health` - Health check endpoint

## 📊 Data Models

### Extracted Data Structure
```json
{
  "parties": [
    {
      "name": "Company Name",
      "legal_entity": "Corporation",
      "signatories": ["John Doe"],
      "roles": ["CEO"]
    }
  ],
  "financial_details": {
    "total_value": 100000.0,
    "currency": "USD",
    "line_items": [
      {
        "description": "Service A",
        "quantity": 10,
        "unit_price": 1000.0,
        "total": 10000.0
      }
    ]
  },
  "payment_structure": {
    "payment_terms": "Net 30",
    "payment_methods": ["Credit Card", "Wire Transfer"]
  },
  "revenue_classification": {
    "recurring_payments": true,
    "billing_cycle": "monthly",
    "auto_renewal": true
  },
  "sla": {
    "performance_metrics": ["99.9% uptime"],
    "support_terms": "24/7 support"
  }
}
```

### Scoring Algorithm
The weighted scoring system evaluates contract completeness:

1. **Financial Completeness (30 points)**:
   - Total value present: 15 points
   - Currency identified: 10 points  
   - Line items extracted: 5 points

2. **Party Identification (25 points)**:
   - Two or more parties: 25 points
   - One party only: 15 points

3. **Payment Terms (20 points)**:
   - Payment terms defined: 12 points
   - Payment methods identified: 8 points

4. **SLA Definition (15 points)**:
   - Performance metrics: 10 points
   - Support terms: 5 points

5. **Contact Information (10 points)**:
   - Email addresses: 5 points
   - Phone numbers: 5 points

## 🐳 Docker Deployment

The system includes complete Docker configuration:

### Services
- **mongodb**: Document database with persistent storage
- **redis**: In-memory cache for background processing
- **backend**: FastAPI application server
- **frontend**: React application with Nginx

### Production Deployment
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Scale backend instances
docker-compose up -d --scale backend=3

# Stop all services
docker-compose down
```

## 🧪 Testing Strategy

### Backend Tests
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Coverage Target**: 60%+ code coverage
- **Test Categories**:
  - API endpoint functionality
  - Contract processing logic
  - Data model validation
  - Error handling scenarios

### Test Execution
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test category
pytest tests/test_contract_processor.py
```

## 🔧 Configuration

### Environment Variables
```bash
# Database
MONGODB_URL=mongodb://admin:password@localhost:27017/contract_intelligence?authSource=admin
REDIS_URL=redis://localhost:6379

# Hugging Face API (Free - Optional)
HUGGINGFACE_API_KEY=your_free_huggingface_token

# Application
DATABASE_NAME=contract_intelligence
MAX_FILE_SIZE=52428800
PROCESSING_TIMEOUT=300
```

### File Storage
- Uploaded contracts stored in `backend/uploads/`
- Configurable upload directory via environment
- Automatic cleanup of temporary files

## 🚨 Error Handling

### Contract Processing Errors
- **Invalid file type**: Returns HTTP 400 with descriptive message
- **File size exceeded**: Returns HTTP 400 with size limit info
- **Processing failure**: Marks contract as "failed" with error details
- **Missing dependencies**: Graceful degradation without OpenAI API

### API Error Responses
```json
{
  "detail": "Error description",
  "status_code": 400,
  "error_type": "validation_error"
}
```

## 📈 Performance Considerations

### Scalability
- Asynchronous background processing
- MongoDB indexing for efficient queries
- Horizontal scaling support via Docker Compose
- Stateless application design

### Optimization
- PDF text extraction caching
- Confidence score pre-computation
- Efficient database queries with pagination
- Frontend lazy loading and virtualization

## 🔒 Security

### File Upload Security
- File type validation (PDF only)
- File size limits (50MB maximum)
- Secure file storage with unique naming
- No direct file execution

### API Security
- Input validation and sanitization
- Error message sanitization
- CORS configuration for frontend access
- No sensitive data in logs

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards
- Python: PEP 8 compliance
- JavaScript: ESLint configuration
- Type hints for Python functions
- Comprehensive test coverage
- Clear commit messages

## 📚 Additional Resources

### Documentation
- [API Documentation](http://localhost:8000/docs) - Interactive Swagger UI
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://reactjs.org/docs/)
- [MongoDB Documentation](https://docs.mongodb.com/)

### Sample Contracts
Test the system with various contract types:
- Service agreements
- Software licenses  
- Consulting contracts
- Subscription agreements
- Purchase orders

## 🐛 Troubleshooting

### Common Issues

**MongoDB Connection Failed**
```bash
# Check if MongoDB is running
docker-compose ps mongodb

# View MongoDB logs
docker-compose logs mongodb
```

**Frontend Not Loading**
```bash
# Rebuild frontend container
docker-compose build frontend
docker-compose up frontend
```

**PDF Processing Errors**
```bash
# Check backend logs
docker-compose logs backend

# Verify file permissions
ls -la backend/uploads/
```

### Support
For technical issues or questions:
1. Check the logs: `docker-compose logs`
2. Verify configuration: Review `.env` file
3. Test connectivity: Use health check endpoint
4. Review documentation: API docs at `/docs`

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for efficient contract management and accounts receivable optimization.**
