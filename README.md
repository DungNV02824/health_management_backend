# Health Management API

A modern FastAPI application for health management with PostgreSQL database and raw SQL queries.

## 🚀 Features

- **FastAPI** - Modern, fast web framework for building APIs
- **PostgreSQL** - Robust relational database with asyncpg for async operations
- **Raw SQL Queries** - Direct database control for optimal performance
- **Docker Ready** - Complete containerization setup
- **Authentication** - JWT-based user authentication
- **Database Migrations** - Alembic for schema management
- **Testing** - Comprehensive test suite with pytest
- **Type Safety** - Full Python type hints and Pydantic validation

## 📁 Project Structure

```
health_management/
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── config.py               # Configuration settings
│   ├── utils.py                # Utility functions
│   ├── db/
│   │   ├── database.py         # Database connection pool
│   │   └── user.py            # User database operations
│   ├── api/
│   │   └── user.py            # User API endpoints
│   ├── services/
│   │   └── user.py            # Business logic layer
│   └── schemas/
│       ├── base.py            # Base Pydantic models
│       └── user.py            # User schemas
├── tests/                      # Test suite
│   ├── conftest.py            # Test configuration
│   └── test_user.py           # User tests
├── scripts/
│   ├── alembic.ini            # Alembic configuration
│   ├── init_db.sql            # Database initialization
│   └── migrations/            # Database migration scripts
├── docker-compose.yml          # Development environment
├── Dockerfile                 # Application container
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Setup

### Prerequisites

**All Platforms:**

- Python 3.13
- PostgreSQL 15+ (or access to a PostgreSQL database)
- Docker & Docker Compose (optional, for containerized development)

**Platform-Specific:**

- **Linux**: Most distributions have Python and PostgreSQL in repositories. For Python 3.13, you may need to use deadsnakes PPA (Ubuntu) or compile from source
- **macOS**: Install via Homebrew (`brew install python@3.13 postgresql@15`)
- **Windows**: Install Python 3.13 from [python.org](https://www.python.org/downloads/) and PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/)

### Local Development

#### Step 1: Clone and Setup Environment

**Linux & macOS:**

```bash
git clone <repository-url>
cd health_management
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
git clone <repository-url>
cd health_management
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (Command Prompt):**

```cmd
git clone <repository-url>
cd health_management
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Note:** Make sure Python 3.13 is installed and accessible. On Linux/macOS, you may need to use `python3.13` explicitly if multiple Python versions are installed.

#### Step 2: Configure Environment Variables

**All Platforms:**

```bash
# Linux & macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env

# Windows (Command Prompt)
copy .env.example .env
```

Edit `.env` file with your database credentials:

**Linux & macOS:**

```bash
# If PostgreSQL is running locally
DATABASE_URL=postgresql://username:password@localhost:5432/health_management

# Example with common defaults
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/health_management
```

**Windows:**

```env
# If PostgreSQL is running locally
DATABASE_URL=postgresql://username:password@localhost:5432/health_management

# Example with common defaults
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/health_management
```

#### Step 3: Setup Database

**Linux & macOS:**

```bash
# Create PostgreSQL database
createdb health_management

# Or using psql
psql -U postgres
CREATE DATABASE health_management;
\q

# Run migrations
cd scripts
alembic upgrade head
```

**Windows:**

```powershell
# Using psql (add PostgreSQL bin to PATH first)
psql -U postgres
CREATE DATABASE health_management;
\q

# Or use pgAdmin GUI to create database

# Run migrations
cd scripts
alembic upgrade head
```

#### Step 4: Run the Application

**Linux & macOS:**

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

**Windows (PowerShell/Command Prompt):**

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

The API will be available at:

- **API**: http://localhost:8080
- **API Docs**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### Docker Development

#### Prerequisites for Docker

**Linux:**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install docker.io docker-compose

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS:**

- Install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
- Or via Homebrew: `brew install --cask docker`

**Windows:**

- Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- Requires WSL 2 (Windows Subsystem for Linux 2)

#### Running with Docker

**All Platforms:**

1. **Create `.env` file** (if not already created):

   ```bash
   # Linux & macOS
   cp .env.example .env

   # Windows (PowerShell)
   Copy-Item .env.example .env
   ```

2. **Update `.env` with database connection:**

   **For Linux & macOS (connecting to host PostgreSQL):**

   ```env
   DATABASE_URL=postgresql://username:password@host.docker.internal:5432/health_management
   ```

   **For Windows (connecting to host PostgreSQL):**

   ```env
   DATABASE_URL=postgresql://username:password@host.docker.internal:5432/health_management
   ```

   **Note:** `host.docker.internal` allows Docker containers to access services on the host machine.

3. **Start the application:**

   **Development mode (with hot reload):**

   ```bash
   # Linux & macOS
   docker-compose -f docker-compose.dev.yml up

   # Windows (PowerShell)
   docker-compose -f docker-compose.dev.yml up
   ```

   **Production mode:**

   ```bash
   # All platforms
   docker-compose up -d
   ```

4. **View logs:**

   ```bash
   # Development mode
   docker-compose -f docker-compose.dev.yml logs -f app

   # Production mode
   docker-compose logs -f api
   ```

5. **Stop the application:**

   ```bash
   # Development mode
   docker-compose -f docker-compose.dev.yml down

   # Production mode
   docker-compose down
   ```

6. **Access services:**
   - **API**: http://localhost:8080
   - **API Docs**: http://localhost:8080/docs
   - **ReDoc**: http://localhost:8080/redoc
   - **Redis** (dev mode): localhost:6379

#### Troubleshooting Docker

**Connection to host PostgreSQL from Docker:**

- **Linux**: Use `host.docker.internal` or your actual host IP
- **macOS**: Use `host.docker.internal` (built-in)
- **Windows**: Use `host.docker.internal` (built-in)

If `host.docker.internal` doesn't work:

- **Linux**: Add `--add-host=host.docker.internal:host-gateway` to docker-compose or use your machine's IP
- Check PostgreSQL `pg_hba.conf` allows connections from Docker network

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_user.py -v
```

## 📚 API Documentation

When running in development mode, interactive API documentation is available at:

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### Key Endpoints

- `POST /api/v1/users/` - Create new user
- `GET /api/v1/users/` - List all users (paginated)
- `GET /api/v1/users/{id}` - Get specific user
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user
- `POST /api/v1/users/login` - User authentication
- `GET /health` - Health check endpoint

## 🗄️ Database

### Schema

The application uses PostgreSQL with the following main table:

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE NULL
);
```

### Migrations

Database schema changes are managed with Alembic:

```bash
# Generate migration
cd scripts
alembic revision --autogenerate -m "Description of changes"

# Run migrations
alembic upgrade head

# Check migration status
alembic current
```

## 🔧 Configuration

Configuration is managed through environment variables. Key settings:

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT signing key (change in production!)
- `DEBUG` - Enable/disable debug mode
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)

## 🔐 Security Features

- **Password Hashing** - Bcrypt for secure password storage
- **JWT Authentication** - Token-based authentication
- **Input Validation** - Pydantic models for request validation
- **SQL Injection Protection** - Parameterized queries with asyncpg
- **CORS Configuration** - Configurable cross-origin settings

## 📦 Deployment

### Production Checklist

1. **Environment Variables:**

   ```bash
   DEBUG=false
   SECRET_KEY=<strong-random-key>
   DATABASE_URL=<production-database-url>
   LOG_LEVEL=INFO
   ```

2. **Database:**

   - Run migrations: `alembic upgrade head`
   - Set up database backups
   - Configure connection pooling

3. **Security:**
   - Use HTTPS
   - Configure proper CORS origins
   - Set up rate limiting
   - Enable database SSL

### Docker Production

**All Platforms:**

```bash
# Build production image
docker build -t health-management-api .

# Run container
docker run -d \
  --name health-api \
  -p 8080:8080 \
  --env-file .env.production \
  health-management-api
```

**Note:** Make sure your `.env.production` file contains production database credentials and settings.

## 🤝 Development

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/ tests/
```

### Project Architecture

The application follows a clean architecture pattern:

1. **API Layer** (`app/api/`) - HTTP endpoints and request/response handling
2. **Service Layer** (`app/services/`) - Business logic and orchestration
3. **Data Layer** (`app/db/`) - Database operations and queries
4. **Schema Layer** (`app/schemas/`) - Data validation and serialization

This separation ensures:

- **Testability** - Each layer can be tested independently
- **Maintainability** - Clear boundaries between concerns
- **Scalability** - Easy to modify or extend individual layers

## 📝 License

[Add your license here]

## 👥 Contributing

[Add contribution guidelines here]

---

Built with ❤️ using FastAPI and PostgreSQL
