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
│   │   └── routes/           # API route modules
│   │       └── __init__.py
│   ├── scripts/
│   │   └── dev.sh            # Development startup script
│   ├── requirements.txt      # Python dependencies
│   ├── pyproject.toml        # Python project configuration
│   └── BACKEND-README.md     # This file
├── frontend/                 # Frontend Project Folder
│   └── ....
├── .env                      # Shared Configuration file for BACKEND and FRONEND
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

#### Option 1: Using the dev script (Recommended)
```bash
# Make the script executable (first time only)
chmod +x scripts/dev.sh

# Run the development server (includes PostgreSQL in Docker)
./scripts/dev.sh
```

This script will:
- Start a PostgreSQL container (if Docker is available)
- Wait for the database to be ready
- Start the FastAPI server with auto-reload

#### Option 2: Manual startup
```bash
# Ensure PostgreSQL is running on localhost:5432
# Then start the server from the /backend directory:
uvicorn app.main:app --reload --port 8000
```

### Accessing the API

Once running, the API is available at:
- **API Base URL:** http://localhost:8000
- **PLANNED: Interactive API Docs (Swagger):** http://localhost:8000/docs

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
- `GET /` - Root endpoint, returns welcome message
- `GET /docs` - Swagger UI documentation

### Planned Endpoints
- `/api/v1/auth/` - Authentication endpoints
- `/api/v1/users/` - User management
- `/api/v1/morse/` - Morse code functionality
- `/api/v1/chat/` - Chat/messaging endpoints

## Development

### Adding New Routes

1. Create a new file in `app/routes/`
2. Define your FastAPI router
3. Import and include it in `app/main.py`

Example:
```python
# app/routes/users.py
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
async def get_users():
    return {"users": []}
```

### Database Migrations

Currently using SQLModel's `create_db_and_tables()` for simplicity. For production, consider using Alembic for migrations.

### Testing

```bash
# Run tests (when implemented)
pytest
```

## Troubleshooting

### Common Issues

1. **Cannot connect to PostgreSQL**
   - Ensure PostgreSQL is running
   - Check database credentials in `.env`
   - Verify PostgreSQL is accessible on localhost:5432

2. **Import errors**
   - Ensure you're running from the `backend` directory
   - Check that virtual environment is activated

## Contributing

1. Create a feature branch
2. Make your changes
3. Ensure all tests pass
4. Submit a pull request

## License

Part of the Morse-Me academic project.