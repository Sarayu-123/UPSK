# Setup Instructions

Welcome to the project! Follow these steps to set up your local development environment.

## Prerequisites
- Python 3.11+
- PostgreSQL
- Redis
- Git

## 1. Clone and Install Dependencies

```bash
# Clone the repository
git clone <repository_url>
cd api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Set Up the Database

1. Ensure PostgreSQL is running.
2. Create a local database for development:
   ```sql
   CREATE DATABASE upsk_sdf_test;
   ```
3. Copy the example `.env` file or set the environment variables:
   ```bash
   export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/upsk_sdf_test"
   export REDIS_URL="redis://localhost:6379"
   export SECRET_KEY="your-secret-key"
   ```
4. Run Alembic migrations to initialize the schema:
   ```bash
   alembic upgrade head
   ```

## 3. Run the Development Server

Start the FastAPI application with auto-reloading:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. You can view the interactive Swagger documentation at `http://localhost:8000/docs`.

## 4. Run Tests

To ensure everything is working correctly, run the full test suite:

```bash
pytest -v
```

This command will automatically use a test database context and leave your environment clean.

## Troubleshooting
- If tests fail, ensure Redis is running and PostgreSQL credentials are correct.
- If you encounter missing records during tests, make sure you don't have overlapping data in your `upsk_sdf_test` database, though the `conftest.py` fixture is designed to reset the schema for tests.
