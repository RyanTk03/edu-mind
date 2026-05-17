# EDU-MIND Backend

Backend API for the EDU-MIND learning platform.

## Tech Stack

- **Python 3.12+**
- **MongoDB** (via MongoDB Atlas)
- **Beanie** - Async ODM for MongoDB
- **Pydantic** - Data validation

## Project Structure

```
backend/
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies & build config
├── .env                    # Environment variables (not in git)
├── .env.example            # Environment template
└── app/
    ├── __init__.py
    ├── config.py           # Settings from environment
    ├── core/
    │   ├── __init__.py
    │   └── database.py     # Database connection
    ├── models/
    │   ├── __init__.py
    │   ├── user.py         # User, UserProfile
    │   ├── session.py      # Study sessions
    │   ├── attachment.py   # File attachments
    │   ├── message.py      # Chat messages
    │   └── exercise.py     # Exercises & questions
    └── seeds/
        ├── __init__.py
        └── seed.py         # Database seeding
```

## Setup

### 1. Install dependencies

```bash
cd backend
uv sync
```

### 2. Configure environment

Copy `.env.example` to `.env` and fill in your MongoDB Atlas credentials:

```bash
cp .env.example .env
```

Edit `.env`:
```env
DB_USER=your_username
DB_PASSWORD=your_password
DB_HOST=cluster0.xxxxx.mongodb.net
DB_NAME=edu_mind
DB_OPTIONS=retryWrites=true&w=majority&appName=Cluster0
```

### 3. Verify connection

```bash
.venv/bin/python main.py
```

## Commands

All commands should be run from the `backend/` directory.

| Command | Description |
|---------|-------------|
| `.venv/bin/python main.py` | Verify database connection |
| `.venv/bin/python -m app.seeds.seed` | Seed test data |
| `.venv/bin/python -m app.seeds.seed --clear` | Clear all data |

## Database Collections

| Collection | Description |
|------------|-------------|
| `users` | User accounts (email, password hash, name) |
| `user_profiles` | Learning profiles (level, weak/strong points) |
| `sessions` | Study sessions (like notebooks) |
| `attachments` | Uploaded files (PDFs, etc.) |
| `messages` | Chat messages within sessions |
| `exercises` | Exercises with questions |
