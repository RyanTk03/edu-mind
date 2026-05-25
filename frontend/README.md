# EDU-MIND Frontend

Modern educational assistant interface built with Next.js 16, React 19, TypeScript, and Tailwind CSS.

## Prerequisites

- Node.js 18+ (recommended: 20+)
- npm, yarn, pnpm, or bun
- Backend server running (see `../backend/README.md`)

## Installation

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local
```

## Configuration

Edit `.env.local`:

```env
# Backend API URL (no trailing slash)
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## Running the App

```bash
# Development mode (with hot reload)
npm run dev

# Production build
npm run build
npm start
```

The app will be available at [http://localhost:3000](http://localhost:3000)

## Features

- **Authentication**: Register/Login with JWT tokens
- **Sessions**: Create and manage study sessions
- **Chat**: AI-powered chat with markdown support
- **File Upload**: Upload PDFs/documents for AI context (RAG)
- **Exercises**: AI-generated exercises with auto-grading

## Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Home page
│   │   ├── login/              # Login page
│   │   ├── register/           # Registration page
│   │   ├── profile/            # User profile
│   │   └── sessions/           # Study sessions
│   │       ├── page.tsx        # Sessions list
│   │       └── [id]/page.tsx   # Session detail (chat)
│   ├── components/
│   │   ├── ui/                 # Reusable UI components
│   │   └── layout/             # Layout components
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   ├── auth-context.tsx    # Auth state management
│   │   └── utils.ts            # Utility functions
│   └── types/                  # TypeScript types
├── .env.example
├── package.json
├── tailwind.config.ts
└── README.md
```

## Usage Guide

### 1. Register/Login

- Go to `/register` to create an account
- Or `/login` if you already have one

### 2. Create a Session

- Click "Nouvelle session" on the sessions page
- Give it a title and optional description

### 3. Upload Documents (Optional)

- In a session, switch to the "Fichiers" tab
- Upload PDF or text files
- Wait for processing (status badge shows progress)
- The AI will use these documents as context

### 4. Chat with AI

- Type your question in the chat
- The AI will respond using your uploaded documents as context
- Supports markdown formatting (bold, lists, code blocks)

### 5. Generate Exercises

- Ask the AI to generate exercises on a topic
- Submit your answers for auto-grading

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Next.js 16 | React framework with App Router |
| React 19 | UI library |
| TypeScript | Type safety |
| Tailwind CSS 4 | Styling |
| react-markdown | Markdown rendering |

## Development

### Linting

```bash
npm run lint
```

### Type Checking

```bash
npx tsc --noEmit
```

## Troubleshooting

### API Connection Failed

1. Make sure backend is running on port 8000
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Check browser console for CORS errors

### Login Not Working

1. Verify backend is running
2. Check that you've registered first
3. Look at backend logs for errors

### File Upload Stuck

1. Check backend logs for processing errors
2. Ensure GROQ_API_KEY is set in backend `.env`
3. File must be PDF, TXT, or MD format

## Contributing

1. Create a feature branch
2. Make your changes
3. Test locally
4. Submit a pull request
