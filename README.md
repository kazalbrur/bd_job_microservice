
# Bangladeshi Government Job Circular Microservice

A production-ready microservice for scraping, processing, and serving Bangladeshi government job circulars with advanced parsing, caching, and notification capabilities.

## 🚀 Features

- **Multi-source Scraping**: Automated scraping from multiple government job portals
- **Intelligent Parsing**: 95-98% accuracy extraction of skills, eligibility, and structured data
- **REST API**: FastAPI-based API with rate limiting and caching
- **Real-time Notifications**: Email alerts for job matches
- **Export Capabilities**: CSV, JSON, and PDF export formats
- **Production Ready**: Docker containerized with monitoring and logging
- **High Performance**: Asynchronous processing with Redis caching

## 📋 Table of Contents

- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Deployment](#deployment)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)

## 🔧 Installation

### Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Docker & Docker Compose (for containerized deployment)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/bd-job-microservice.git
   cd bd-job-microservice
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**
   Playwright is required for browser-driven scrapers. You can install the
   browsers directly with the Playwright CLI or use the convenience helper
   included in this repo.

   Direct (recommended):
   ```bash
   playwright install chromium
   ```

   Or via the helper script (runs `python -m playwright install` using
   your current virtualenv):
   ```bash
   python scripts/install_playwright.py --browsers chromium --yes --with-deps
   ```

5. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Setup database**
   ```bash
   python scripts/setup_db.py --sample-data
   ```

7. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## ⚙️ Configuration

Key environment variables in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/bd_jobs
REDIS_URL=redis://localhost:6379/0

# Email Notifications
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=noreply@bdjobs.com

# Scraping
SCRAPER_DELAY=1.0
SCRAPER_TIMEOUT=30
SCRAPER_RETRIES=3

# API
SECRET_KEY=your-very-secure-secret-key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

## 🎯 Usage

### Running the Scraper

**Manual scraping:**
```bash
python scripts/run_scraper.py
```

**Scraping without saving to DB:**
```bash
python scripts/run_scraper.py --no-save
```

**Limit number of jobs:**
```bash
python scripts/run_scraper.py --max-jobs 50
```

### Starting the API Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Running with Docker

```bash
docker-compose up -d
```

## 📚 API Endpoints

### Jobs API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/jobs/` | List all jobs with optional filtering |
| GET | `/jobs/{id}` | Get specific job details |
| GET | `/jobs/search/{query}` | Full-text search across jobs |

**Query Parameters for `/jobs/`:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Number of records to return (max: 100)
- `title`: Filter by job title
- `department`: Filter by department
- `location`: Filter by location
- `active_only`: Show only active jobs (default: true)

**Example Requests:**
```bash
# Get all jobs
curl "http://localhost:8000/jobs/"

# Search for engineering jobs
curl "http://localhost:8000/jobs/search/engineer"

# Filter by location
curl "http://localhost:8000/jobs/?location=dhaka&limit=10"
```

### Bookmarks API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/bookmarks/` | Create a bookmark |
| GET | `/bookmarks/?user_id={id}` | Get user's bookmarks |
| DELETE | `/bookmarks/{id}` | Delete a bookmark |

### Export API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/export/csv` | Export jobs as CSV |
| GET | `/export/json` | Export jobs as JSON |

### Health & Monitoring

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Basic metrics |

## 🚢 Deployment

### Docker Deployment

1. **Build and run with Docker Compose:**
   ```bash
   docker-compose up -d
   ```

2. **Check logs:**
   ```bash
   docker-compose logs -f app
   ```

### AWS ECS Deployment

1. **Build and push Docker image:**
   ```bash
   docker build -t bd-jobs-api .
   docker tag bd-jobs-api:latest your-ecr-repo/bd-jobs-api:latest
   docker push your-ecr-repo/bd-jobs-api:latest
   ```

2. **Use the provided ECS task definition:**
   ```bash
   aws ecs register-task-definition --cli-input-json file://deploy/aws_ecs_task.json
   ```

### Kubernetes Deployment

```bash
kubectl apply -f deploy/k8s_deployment.yaml
```

## 🔨 Development

### Project Structure

```
bd_job_microservice/
├── app/
│   ├── scrapers/         # Web scraping modules
│   ├── parsers/          # Data parsing and cleaning
│   ├── db/              # Database models and connections
│   ├── api/             # FastAPI routes
│   ├── alerts/          # Notification system
│   ├── cache/           # Redis caching
│   └── utils/           # Utility functions
├── tests/               # Test suite
├── scripts/             # Utility scripts
├── deploy/              # Deployment configurations
└── docker/              # Docker configurations
```

### Adding New Scrapers

1. **Create scraper class:**
   ```python
   # app/scrapers/new_site_scraper.py
   from .base_scraper import BaseScraper
   
   class NewSiteScraper(BaseScraper):
       async def scrape_jobs(self):
           # Implementation
           pass
   ```

2. **Register in scraper manager:**
   ```python
   # app/scrapers/scraper_manager.py
   from .new_site_scraper import NewSiteScraper
   
   self.scrapers = [
       GovBDScraper,
       NewSiteScraper,  # Add here
   ]
   ```

### Code Quality

**Format code:**
```bash
black app/ tests/
isort app/ tests/
```

**Type checking:**
```bash
mypy app/
```

## 🧪 Testing

**Run all tests:**
```bash
pytest
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
```

**Run specific test file:**
```bash
pytest tests/test_scrapers.py -v
```

## 📊 Monitoring

### Metrics Available

- Total jobs in database
- Active jobs count
- Recent jobs (last 7 days)
- API response times
- Scraper success/failure rates

### Logging

Structured JSON logging is configured by default. Logs include:
- Timestamp
- Log level
- Module and function
- Structured data

**Example log entry:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "app.scrapers.govbd_scraper",
  "message": "Scraped 25 jobs successfully",
  "module": "govbd_scraper",
  "jobs_count": 25,
  "execution_time": 12.5
}
```

## 🔄 Scheduled Tasks

The application includes these scheduled tasks:

- **Job Scraping**: Every 6 hours
- **Alert Processing**: Every 1 hour  
- **Cleanup Old Jobs**: Daily at 2 AM

## 🚨 Alerts System

### Setting Up Alerts

Users can set up job alerts based on:
- Keywords in job title/description
- Location preferences
- Department preferences

### Email Templates

Customizable HTML email templates with job details and direct application links.

## 🔒 Security

- Rate limiting on all API endpoints
- Input validation and sanitization
- SQL injection prevention via SQLAlchemy
- CORS configuration for production
- Environment-based configuration

## ⚡ Performance Optimizations

- **Database Indexing**: Optimized indexes for common queries
- **Redis Caching**: API responses cached for 5-60 minutes
- **Connection Pooling**: PostgreSQL connection pooling
- **Async Processing**: Asynchronous scraping and API endpoints
- **Bulk Operations**: Batch database inserts

## 🐛 Troubleshooting

### Common Issues

1. **Playwright Installation**
   ```bash
   # If Playwright reports missing browsers, run either:
   playwright install --with-deps chromium

   # or the helper (non-interactive):
   python scripts/install_playwright.py --browsers chromium --yes --with-deps
   ```

2. **Database Connection Issues**
   - Check PostgreSQL is running
   - Verify DATABASE_URL format
   - Check firewall settings

3. **Redis Connection Issues**
   - Verify Redis is running: `redis-cli ping`
   - Check REDIS_URL configuration

4. **Email Notifications Not Working**
   - Verify SMTP credentials
   - Check Gmail App Passwords if using Gmail
   - Test SMTP connection manually

### Logs Location

- **Development**: Console output
- **Docker**: `docker-compose logs app`
- **Production**: Configure log aggregation (ELK, CloudWatch)

## 📈 Scaling

### Horizontal Scaling

- Multiple API instances behind load balancer
- Separate scraper instances with distributed job queue
- Database read replicas for query performance

### Vertical Scaling

- Increase container resources (CPU, Memory)
- Database performance tuning
- Redis memory optimization

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

- **Issues**: GitHub Issues
- **Documentation**: [Wiki](https://github.com/your-org/bd-job-microservice/wiki)
- **Email**: support@bdjobs.com

## 🙏 Acknowledgments

- Government of Bangladesh for open data access
- FastAPI and SQLAlchemy communities
- Playwright team for excellent web automation tools

---

**Built with ❤️ for the Bangladeshi job seekers community**
"""