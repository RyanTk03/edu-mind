# EDU-MIND

AI-powered educational assistant with document understanding, intelligent chat, and exercise generation.

## Overview

EDU-MIND helps students learn more effectively by:
- Uploading study materials (PDFs, documents)
- Chatting with an AI that understands your documents
- Generating practice exercises with auto-grading

## Architecture

```
EDU-MIND/
├── backend/          # FastAPI + MongoDB + AI Services
├── frontend/         # Next.js + React + TypeScript
└── agents/           # LangGraph AI Agents (optional)
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- MongoDB (local or Atlas)
- GROQ API key (free at https://console.groq.com)

### 1. Backend Setup

```bash
cd backend

# Install dependencies
uv sync  # or: pip install -e .

# Configure environment
cp .env.example .env
# Edit .env with your MongoDB and GROQ_API_KEY

# Run server
uv run uvicorn app.main:app --reload
```

Backend runs at http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local

# Run dev server
npm run dev
```

Frontend runs at http://localhost:3000

### 3. Use the App

1. Open http://localhost:3000
2. Register a new account
3. Create a study session
4. Upload documents (optional)
5. Start chatting with the AI

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI, MongoDB, Beanie ODM |
| Frontend | Next.js 16, React 19, TypeScript, Tailwind |
| AI/LLM | GROQ (Llama 3.3), LangGraph |
| Vector DB | ChromaDB |
| Embeddings | Sentence Transformers |

## Features

- **Authentication**: JWT-based auth with refresh tokens
- **Sessions**: Organize your study by topic/subject
- **RAG Chat**: AI chat with document context
- **File Processing**: PDF and text file ingestion
- **Exercises**: AI-generated quizzes with grading

## Documentation

- [Backend README](./backend/README.md) - API docs, endpoints, configuration
- [Frontend README](./frontend/README.md) - UI setup, components, usage
- [Demo video](https://drive.proton.me/urls/G8ZK5P18T0#OTN0Bwo6fEJm)

## Environment Variables

### Backend (.env)

```env
# MongoDB
DB_HOST=localhost:27017
DB_NAME=edu_mind

# JWT
JWT_SECRET_KEY=your-secret-key

# AI
GROQ_API_KEY=your_groq_api_key
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Team

School project for DSAI (Distributed Systems & AI).

## License

MIT
