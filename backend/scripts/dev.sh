#!/bin/bash
# dev.sh - Start development environment

set -e  # Exit on any error

echo "Starting Morse-Me Backend development environment..."

# Load environment variables from .env file
if [ -f ../.env ]; then
    echo "Loading environment variables from .env..."
    # Load only our app variables, not all system variables
    set -a  # automatically export variables
    source <(grep -E '^(POSTGRES_|BACKEND_)' ../.env | grep -v '^#')
    set +a  # stop auto-exporting
else
    echo "ERROR: .env file not found!"
    exit 1
fi

# Use environment variables for configuration
CONTAINER_NAME="morse-me-postgres-dev"
DB_PORT=${POSTGRES_PORT:-5432}

# Cleanup function to run on script exit
cleanup() {
    echo ""
    echo "Stopping PostgreSQL container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    exit 0
}

# Set trap to cleanup on script exit (Ctrl+C, kill, etc.)
trap cleanup SIGINT SIGTERM EXIT

echo "Starting PostgreSQL container on port $DB_PORT..."
docker run -d \
  --name $CONTAINER_NAME \
  --env-file ../.env \
  -p $DB_PORT:5432 \
  --rm \
  postgres:15

# Wait for postgres to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 3

# Check if postgres is responding (using env vars)
until docker exec $CONTAINER_NAME pg_isready -U $POSTGRES_USER -d $POSTGRES_DB >/dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 1
done

echo "PostgreSQL is ready!"
echo "Starting FastAPI server on port $BACKEND_APP_PORT from $BACKEND_DIR..."
echo "API docs will be available at http://localhost:$BACKEND_APP_PORT/docs"
echo "Press Ctrl+C to stop both services"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get the backend directory (parent of scripts directory)
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Change to the backend directory
cd "$BACKEND_DIR"

# Option C: Keep simple uvicorn but run initial checks
echo "Running initial code quality checks..."
ruff check . --quiet || echo "Ruff found issues"
mypy . --no-error-summary || echo "MyPy found type issues"
echo "Starting uvicorn (checks will run on each reload via app startup)..."


# Start uvicorn (we're already in backend directory)
uvicorn app.main:app --reload --port $BACKEND_APP_PORT