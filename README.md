# WeAssistant - FastAPI Chatbot

A modern FastAPI chatbot for WeMasterTrade with SQLAlchemy, LangChain, and clean architecture.

## 🚀 Quick Start

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with your API keys

# 2. Install dependencies
uv pip install .

# 3. Initialize database
python -m app.utils.init_db

# 4. Run
uvicorn app.main:app --reload
```

## 📁 Structure

```
app/
├── main.py                 # FastAPI app
├── config/settings.py      # Configuration
├── api/v1/endpoints/       # API endpoints
├── models/                 # SQLAlchemy & domain models
├── services/               # Business logic
├── utils/                  # Database & LLM utilities
└── schemas/                # Request/response models
```

## ⚙️ Configuration

```bash
# Required
DATABASE_URL=postgresql://user:pass@localhost:5432/db
OPENAI_API_KEY=your_key
QDRANT_URL=http://localhost:6333

# Optional
QDRANT_API_KEY=your_key
OPENAI_CHAT_MODEL=gpt-4o-mini
```

## 📋 API

**POST** `/api/v1/chat`
```json
{
  "user_id": "user123",
  "message": "How can I start trading?"
}
```

**Response:**
```json
{
  "reply": "Hi! How can I help you today?",
  "intent": "TRIVIAL",
  "confidence": 0.95,
  "profile_used": "newbie"
}
```

## 🐳 Docker

```bash
docker build -t weassistant .
docker run -p 8000:8000 --env-file .env weassistant
```
