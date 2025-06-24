# Morse-Me Backend

FastAPI backend for the Morse-Me application - Learn Morse Code, One Friend at a Time!

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLModel
- **Authentication:** JWT
- **Python:** 3.10+

## Project Structure

```
morse-me/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── config.py         # Configuration and settings
│   │   ├── db.py             # Database connection and session
│   │   ├── models.py         # SQLModel database models
│   │   ├── dep.py            # Dependencies for dependency injection
│   │   ├── core/             # Core utilities
│   │   │   ├── exceptions.py # Custom exception handlers
│   │   │   └── response.py   # Custom response models
│   │   └── routes/           # API route modules
│   │       ├── __init__.py
│   │       └── user.py       # User management endpoints
│   ├── tests/                # Test files
│   │   ├── __init__.py
│   │   ├── conftest.py       # Shared test configuration
│   │   ├── test_main.py      # Main app tests
│   │   └── test_users.py     # User endpoint tests
│   ├── scripts/
│   │   └── dev.sh            # Development startup script
│   ├── requirements.txt      # Python dependencies (includes test deps)
│   ├── pyproject.toml        # Python project configuration
│   └── BACKEND-README.md     # This file
├── frontend/                 # Frontend Project Folder
│   └── ....
├── .env                      # Shared Configuration file for BACKEND and FRONTEND
└── README.md                 # Main project README
```

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker (for PostgreSQL) or PostgreSQL installed locally
- pip (Python package manager)

### Installation

1. **Create and activate virtual environment**
   ```bash
   # From the backend directory
   python -m venv .venv
   
   # Activate virtual environment
   # On Linux/Mac:
   source .venv/bin/activate
   
   # On Windows:
   .venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Development Server

#### Manual startup
Setting up the Database with Docker
```bash
docker run -d --name morse-postgres -e POSTGRES_USER=morse_user -e POSTGRES_PASSWORD=morse_password -e POSTGRES_DB=morse_me_db -p 5432:5432 postgres:latest
```

```bash
# Ensure PostgreSQL is running on localhost:5432
# Then start the server from the /backend directory:
uvicorn app.main:app --reload --port 8000
```

### Accessing the API

Once running, the API is available at:
- **API Base URL:** http://localhost:8000
- **Interactive API Docs (Swagger):** http://localhost:8000/docs
- **Alternative API Docs (ReDoc):** http://localhost:8000/redoc

## Testing

The backend includes comprehensive tests for all endpoints and functionality.

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_users.py

# Run tests with coverage report
pytest --cov=app

# Install coverage tool if needed
pip install pytest-cov
```

### Test Structure

- **`tests/conftest.py`** - Shared test fixtures and configuration
- **`tests/test_main.py`** - Tests for main application endpoints
- **`tests/test_users.py`** - Tests for user management endpoints

### What's Tested

- ✅ User registration and validation
- ✅ User retrieval by ID and callsign
- ✅ Search and pagination functionality
- ✅ Password hashing security
- ✅ Error handling and edge cases
- ✅ Main application endpoints
- ✅ Data integrity and constraints

## Environment Variables

The backend uses the following environment variables (with `BACKEND_` prefix):

```env
# Application
BACKEND_APP_NAME=Morse-Me-Backend
BACKEND_APP_PORT=8000
BACKEND_ADMIN_EMAIL=admin@morse-me.com

# Database
BACKEND_DATABASE_URL=postgresql://user:password@localhost:5432/morse_me_db

# Security
BACKEND_SECRET_KEY=your-secret-key-here
BACKEND_ALGORITHM=HS256
BACKEND_ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Development
BACKEND_DEVELOPMENT_MODE=true
```

## API Endpoints

### Current Endpoints

#### Root & Health
- `GET /` - Root endpoint, returns welcome message
- `GET /health` - Health check endpoint

#### User Management
- `GET /users/` - List users with search and pagination
- `GET /users/{user_id}` - Get user by ID
- `GET /users/callsign/{callsign}` - Get user by callsign
- `POST /users/` - Register new user

### Planned Endpoints
- `/api/v1/auth/` - Authentication endpoints
- `/api/v1/morse/` - Morse code functionality
- `/api/v1/chat/` - Chat/messaging endpoints

## Development

### Adding New Routes

1. Create a new file in `app/routes/`
2. Define your FastAPI router
3. Import and include it in `app/main.py`

Example:
```python
# app/routes/morse.py
from fastapi import APIRouter

router = APIRouter(prefix="/morse", tags=["morse"])

@router.get("/")
async def get_morse_codes():
    return {"codes": []}

# In app/main.py
from .routes import user, morse
app.include_router(user.router)
app.include_router(morse.router)
```

### Database Migrations

Currently using SQLModel's `create_db_and_tables()` for simplicity. For production, consider using Alembic for migrations.

### Testing New Features

When adding new endpoints:
1. Write tests in the appropriate `test_*.py` file
2. Follow the existing test patterns
3. Test both success and error cases
4. Run tests to ensure they pass: `pytest`

## Troubleshooting

### Common Issues

1. **Cannot connect to PostgreSQL**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify PostgreSQL is accessible on localhost:5432

2. **Import errors**
   - Ensure you're running from the `backend` directory
   - Check that virtual environment is activated

3. **Test failures**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check that you're running tests from the backend directory
   - Verify database connection (tests use SQLite in-memory database)

## Contributing

1. Create a feature branch
2. Make your changes
3. Write tests for new functionality
4. Ensure all tests pass: `pytest`
5. Submit a pull request

## License

Part of the Morse-Me academic project.