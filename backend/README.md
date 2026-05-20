# EDU-MIND Backend

AI-powered educational assistant backend built with FastAPI, MongoDB, and Beanie ODM.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- MongoDB (local or Atlas)

## Installation

```bash
# Navigate to backend
cd backend

# Install dependencies
uv sync

# Copy environment file
cp .env.example .env
```

## Configuration

Edit `.env` with your settings:

```env
# MongoDB - Local
DB_HOST=localhost:27017
DB_NAME=edu_mind

# MongoDB - Atlas (cloud)
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=cluster0.xxxxx.mongodb.net
DB_NAME=edu_mind
DB_OPTIONS=retryWrites=true&w=majority&appName=Cluster0

# JWT Authentication
JWT_SECRET_KEY=your-super-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# File uploads
UPLOAD_DIR=./uploads
MAX_UPLOAD_SIZE_MB=50

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Running the Server

```bash
# With uv (recommended)
uv run uvicorn app.main:app --reload

# Or activate venv first
source .venv/bin/activate
uvicorn app.main:app --reload

# Custom port
uvicorn app.main:app --reload --port 8080
```

The server will start at `http://127.0.0.1:8000`

## API Documentation

Once the server is running:

| Resource | URL |
|----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| OpenAPI JSON | http://localhost:8000/openapi.json |
| Health Check | http://localhost:8000/health |

## Authentication

The API uses JWT Bearer tokens.

### Register a new user

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123", "name": "John Doe"}'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepass123"}'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Use the token

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Refresh token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/profile` | Get user profile |
| PATCH | `/api/users/profile` | Update user profile |

### Sessions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions` | List all sessions |
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions/{id}` | Get session details |
| PATCH | `/api/sessions/{id}` | Update session |
| DELETE | `/api/sessions/{id}` | Delete session |

### Attachments
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/{id}/attachments` | List attachments |
| POST | `/api/sessions/{id}/attachments` | Upload file |
| GET | `/api/sessions/{id}/attachments/{aid}` | Get attachment info |
| DELETE | `/api/sessions/{id}/attachments/{aid}` | Delete attachment |
| GET | `/api/sessions/{id}/attachments/{aid}/download` | Download file |
| GET | `/api/sessions/{id}/attachments/{aid}/status` | Processing status |

### Chat Messages
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/{id}/chat` | Get chat history |
| POST | `/api/sessions/{id}/chat` | Send message |
| DELETE | `/api/sessions/{id}/chat` | Clear chat history |

### Exercises
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/sessions/{id}/exercises` | List exercises |
| POST | `/api/sessions/{id}/exercises/generate` | Generate exercise |
| GET | `/api/sessions/{id}/exercises/{eid}` | Get exercise |
| POST | `/api/sessions/{id}/exercises/{eid}/submit` | Submit answers |
| GET | `/api/sessions/{id}/exercises/{eid}/results` | Get results |

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Settings from environment
│   ├── api/                  # Route handlers
│   │   ├── router.py        # Main API router
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── users.py         # User profile endpoints
│   │   ├── sessions.py      # Session CRUD
│   │   ├── attachments.py   # File upload/download
│   │   ├── messages.py      # Chat functionality
│   │   └── exercises.py     # Exercise generation
│   ├── core/                 # Core utilities
│   │   ├── database.py      # MongoDB/Beanie setup
│   │   ├── security.py      # JWT & password hashing
│   │   ├── exceptions.py    # Custom exceptions
│   │   └── deps.py          # Auth dependencies
│   ├── models/              # Beanie document models
│   ├── schemas/             # Pydantic DTOs
│   └── seeds/               # Database seeding
├── .env.example
├── pyproject.toml
└── README.md
```

## Development

### Using Docker for MongoDB

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Seed the database

```bash
uv run python -m app.seeds.seed
```

## Troubleshooting

### MongoDB Atlas SSL Error

If you get `SSL handshake failed` errors:
1. Whitelist your IP in MongoDB Atlas -> Network Access
2. Or use local MongoDB for development

### Module not found

```bash
uv sync  # Reinstall dependencies
```

### Port already in use

```bash
uvicorn app.main:app --reload --port 8080
```
