# Salon Reservations API

A robust and secure REST API for managing event hall reservations with advanced features including user authentication, role-based access control, rate limiting, and comprehensive test coverage.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Security](#security)
- [Testing](#testing)
- [Database](#database)
- [Docker Deployment](#docker-deployment)
- [Development](#development)
- [License](#license)

## 🎯 Overview

This is a robust and feature-complete API for managing salon/event hall reservations currently in active development. It provides comprehensive functionality for users to browse available halls, make reservations, and manage their bookings, while administrators can manage halls and view all reservations. The API implements JWT-based authentication, password hashing with Argon2, rate limiting, and role-based access control. Production deployment is planned once the frontend web application is completed.

## ✨ Features

### Core Functionality
- **User Management**: User registration, authentication, and profile management with soft-delete support
- **Hall Management**: Create, update, and manage event halls with detailed information
- **Reservation System**: Complete reservation lifecycle with status tracking
- **Search & Filtering**: Advanced search and filtering capabilities for halls and reservations
- **Pagination**: Efficient data pagination with configurable limits

### Security Features
- **JWT Authentication**: Secure token-based authentication with configurable expiration
- **Password Security**: Argon2id password hashing with recommended security defaults
- **Rate Limiting**: Global rate limiting and endpoint-specific rate limiting (especially strict on login and registration)
- **Role-Based Access Control**: Three-tier permission system (SUPERADMIN, ADMIN, USER)
- **CORS Support**: Configurable cross-origin resource sharing
- **Input Validation**: Comprehensive data validation using Pydantic models

### Operational Features
- **Async Processing**: Fully asynchronous API using FastAPI for high performance
- **Database Migrations**: Automated schema migrations with Alembic
- **Background Tasks**: Background worker for automatic cleanup of expired reservations
- **Health Checks**: Container health checks for production deployments
- **Structured Logging**: Comprehensive logging for debugging and monitoring
- **Error Handling**: Consistent error responses with meaningful error messages

## 🛠️ Tech Stack

### Backend Framework
- **FastAPI** (0.128.0) - Modern, fast web framework for building APIs
- **Uvicorn** (0.40.0) - ASGI server implementation

### Database
- **PostgreSQL** (18 Alpine) - Production-grade relational database
- **SQLAlchemy** (2.0.46) - SQL toolkit and ORM with async support
- **Alembic** (1.18.1) - Database migration management
- **asyncpg** (0.31.0) - PostgreSQL adapter for asyncio
- **aiosqlite** (0.22.1) - SQLite adapter for testing

### Authentication & Security
- **PyJWT** (2.11.0) - JWT token creation and validation
- **argon2-cffi** (25.1.0) - Argon2id password hashing
- **pwdlib** (0.3.0) - Password hashing abstraction layer

### Data Validation & Configuration
- **Pydantic** (2.12.5) - Data validation and serialization
- **Pydantic Settings** (2.12.0) - Settings management
- **Python Dotenv** (1.2.1) - Environment variable management

### Testing
- **pytest** (9.0.2) - Testing framework
- **pytest-asyncio** (1.3.0) - Async test support
- **httpx** (0.28.1) - Async HTTP client for testing

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL 18+ (for production)
- Git
- Docker & Docker Compose (optional, for containerized setup)

### Installation

#### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <https://github.com/JesusHM0406/hall-reservations-api.git>
   cd hall-reservations-api
   ```

2. **Create and activate virtual environment**
   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip setuptools wheel
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Create .env file from example (or create new one)
   cp .env.example .env
   ```
   
   Configure the following variables in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/salon_db
   SECRET_KEY=your-super-secret-key-change-in-production
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
   POSTGRES_USER=salon_user
   POSTGRES_PASSWORD=secure_password
   POSTGRES_DB=salon_db
   ```

5. **Set up database**
   ```bash
   # Start PostgreSQL (if not already running)
   # Then run migrations
   alembic upgrade head
   ```

#### Docker Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone <https://github.com/JesusHM0406/hall-reservations-api.git>
   cd hall-reservations-api
   ```

2. **Create .env file**
   ```bash
   cp .env.example .env
   # Update with your configuration
   ```

3. **Build and start services**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ |
| `SECRET_KEY` | JWT signing secret key | - | ✅ |
| `ALLOWED_ORIGINS` | CORS allowed origins (comma-separated) | - | ✅ |
| `POSTGRES_USER` | PostgreSQL user | - | ✅ |
| `POSTGRES_PASSWORD` | PostgreSQL password | - | ✅ |
| `POSTGRES_DB` | PostgreSQL database name | - | ✅ |
| `PROJECT_NAME` | API project name | "Hall Reservations API" | ❌ |
| `PROJECT_VERSION` | API version | "0.0.1" | ❌ |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | 60 | ❌ |
| `PAGINATION_LIMIT_PER_PAGE` | Default pagination limit | 10 | ❌ |
| `MIN_PASSWORD_SIZE` | Minimum password length | 8 | ❌ |
| `MIN_NAME_SIZE` | Minimum username length | 3 | ❌ |

### Security Configuration

Key security settings are configured in `app/core/config.py`:

```python
ALGORITHM = "HS256"                    # JWT algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = 60       # Token expiration
MIN_PASSWORD_SIZE = 8                  # Password minimum length
MIN_NAME_SIZE = 3                      # Username minimum length
```

## 🏃 Running the Application

### Local Development

1. **Activate virtual environment**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # macOS/Linux
   source .venv/bin/activate
   ```

2. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

3. **Start the development server**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

Interactive API documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Docker

Start all services:
```bash
docker-compose -f docker-compose.dev.yml up
```

The API will be available at `http://localhost:8000`

View logs:
```bash
docker-compose -f docker-compose.dev.yml logs -f api
```

Stop services:
```bash
docker-compose -f docker-compose.dev.yml down
```

## 📚 API Endpoints

### Authentication Endpoints (`/auth`)
- `POST /auth/login` - User login with rate limiting (returns JWT token)
- Rate limiting: 5 attempts per 15 minutes per IP

### User Endpoints (`/users`)
- `POST /users/` - Register new user (rate limited)
- `GET /users/` - List all users (paginated, admin only)
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user profile
- `DELETE /users/{user_id}` - Soft delete user

### Hall Endpoints (`/halls`)
- `POST /halls/` - Create new hall (admin only)
- `GET /halls/` - List halls with filtering and pagination
- `GET /halls/{hall_id}` - Get hall details
- `PUT /halls/{hall_id}` - Update hall (admin only)
- `DELETE /halls/{hall_id}` - Delete hall (admin only)

### Reservation Endpoints (`/reservations`)
- `POST /reservations/` - Create new reservation
- `GET /reservations/` - List reservations (paginated, with filtering)
- `GET /reservations/{reservation_id}` - Get reservation details
- `PUT /reservations/{reservation_id}` - Update reservation
- `DELETE /reservations/{reservation_id}` - Cancel reservation

### Health Check
- `GET /health` - API health status check

All endpoints (except login and registration) require valid JWT authentication via the `Authorization: Bearer <token>` header.

## 🔒 Security

### Authentication & Authorization

- **JWT Tokens**: Secure token-based authentication with configurable expiration (default: 60 minutes)
- **Password Hashing**: Industry-standard Argon2id hashing with recommended security settings
- **Role-Based Access Control (RBAC)**:
  - `SUPERADMIN`: Full system access
  - `ADMIN`: Hall and reservation management
  - `USER`: Personal reservation management
- **User Soft Deletion**: Users are marked as deleted rather than hard-deleted for audit trails

### Rate Limiting

- **Global Rate Limiting**: Applied to all requests to prevent abuse
- **Endpoint-Specific Rate Limiting**:
  - **Login**: 5 attempts per 15 minutes per IP address
  - **Registration**: Rate limited to prevent account enumeration
- **IP-Based Tracking**: Rate limits are tracked per client IP address

### Input Validation

- Comprehensive Pydantic model validation for all inputs
- Password strength requirements (minimum 8 characters)
- Username requirements (minimum 3 characters, maximum 100 characters)

### CORS Configuration

Configurable cross-origin resource sharing via `ALLOWED_ORIGINS` environment variable (comma-separated list).

### API Security Best Practices

- Secrets managed through environment variables
- HTTPS-ready configuration
- Input sanitization via Pydantic
- SQL injection prevention via parameterized queries
- Password storage using Argon2id
- Rate limiting on sensitive endpoints
- Structured error handling (no sensitive information leakage)

## 🧪 Testing

### Test Coverage

The project includes **25+ comprehensive test files** covering:

- **Authentication Tests** (`test_auth/`):
  - JWT token validation
  - Login functionality
  - Password security
  - Access control

- **User Tests** (`test_users/`):
  - User registration and profile updates
  - User management operations
  - Soft deletion functionality
  - Normal user full flow
  - Hierarchy escalation flow

- **Hall Tests** (`test_halls/`):
  - Hall creation and management
  - Hall retrieval with filtering
  - Permission checks

- **Reservation Tests** (`test_reservations/`):
  - Reservation creation and lifecycle
  - Conflict detection
  - Status management

- **Middleware Tests** (`test_middleware/`):
  - Rate limiting verification
  - Request/response handling

There are 313 tests passing and 5 skipped (related to hall search).

### Running Tests

**Run all tests**
```bash
pytest
```

**Run with verbose output**
```bash
pytest -v
```

**Run specific test file**
```bash
pytest tests/test_api/test_auth/test_auth_login.py
```

**Run specific test function**
```bash
pytest tests/test_api/test_auth/test_auth_login.py::test_login_success
```

**Run with coverage report**
```bash
pytest --cov=app --cov-report=html
```

**Run tests in parallel** (faster execution)
```bash
pytest -n auto
```

### Test Configuration

Test configuration is defined in `pytest.ini`:
- Asyncio mode: auto (for async test support)
- Default fixture loop scope: session

Tests use SQLite in-memory database for fast, isolated test execution that doesn't interfere with development or production databases.

## 🗄️ Database

### Database Design

The application uses PostgreSQL with SQLAlchemy ORM. Key tables include:

- **users**: User accounts with roles and soft-delete support
- **halls**: Event hall information and availability
- **reservations**: Reservation records with status tracking

### Key Features

- **Async Support**: All database operations are async using `asyncpg`
- **Migrations**: Alembic manages all schema changes
- **Soft Deletes**: Users can be soft-deleted for audit trails
- **Partial Unique Indexes**: PostgreSQL partial unique index on active reservations for the same hall and date
- **Full-Text Search**: PostgreSQL FTS support for searching halls
- **Timestamp Tracking**: Created and updated timestamp columns with indexes

### Database Migrations

View migration status:
```bash
alembic current
```

Run migrations:
```bash
alembic upgrade head
```

Create new migration:
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Important Database Notes

#### Reservation Partial Unique Index

The `reservations` model defines a partial unique index (`uq_hallid_resdate_active`) with environment-specific behavior:

- **PostgreSQL (Production)**: Enforced with `postgresql_where` clause to allow multiple inactive reservations
- **SQLite (Testing)**: Uses `sqlite_where` to mirror PostgreSQL behavior during tests
- **Purpose**: Prevents double-booking of active reservations while allowing soft-deleted reservations

This design ensures test behavior matches production behavior exactly.

## 🐳 Docker Deployment

> **Note**: The current Docker setup is simplified and development-focused. Production-ready Docker configuration will be added once the frontend web application is completed.

### Docker Architecture

The project includes a development-focused Docker setup with two services:

#### **PostgreSQL Service**
- Image: `postgres:18-alpine` (lightweight Alpine Linux variant)
- Volumes: `postgres_data` for persistent storage
- Health checks: Automatic service validation
- Network: Internal `salon-dev-network`

#### **API Service**
- Built from `Dockerfile.dev` with Python 3.12
- Auto-reload enabled for development
- Automatic migrations via `entrypoint.sh`
- Health checks: HTTP health endpoint validation
- Volumes: Source code mounted for hot-reload development

### Dockerfile Details

Key features of `Dockerfile.dev`:

- Base: Python 3.12-slim (small footprint)
- System dependencies: gcc, postgresql-client
- Environment: Production-appropriate variable settings
- Health checks: 30-second interval checks
- Entrypoint: Automatic migrations and server startup

### Docker Compose Configuration

Key orchestration features:

- Service dependencies: API waits for unhealthy database
- Network isolation: Internal bridge network for security
- Port mapping: Expose PostgreSQL (5432) and API (8000)
- Volume management: Persistent database data, mounted source code
- Environment management: Loaded from .env file

### Docker Commands

**Start services** specifying compose file (development)
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**View service logs**
```bash
docker-compose logs -f api
```

**Stop services**
```bash
docker-compose -f docker-compose.dev.yml down
```

**Rebuild images** after dependency changes
```bash
docker-compose -f docker-compose.dev.yml up -d --build
```

**Access database container**
```bash
docker-compose exec db psql -U $POSTGRES_USER -d $POSTGRES_DB
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.