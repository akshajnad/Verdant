# Verdant AI Service

FastAPI service that provides AI-powered garden planning using Claude and Supabase.

## Features

- **Schedule Generation**: Creates personalized planting schedules using Claude AI
- **Weather Integration**: Fetches and caches weather data from Open-Meteo
- **Feedback Loop**: Revises schedules based on user feedback
- **Supabase Integration**: Direct database access with service role key

## Setup

### Prerequisites

- Python 3.11+
- Supabase project with schema migrated
- Anthropic API key

### Installation

```bash
cd ai-service
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Service role key (NOT anon key!)
- `ANTHROPIC_API_KEY`: Your Claude API key

### Running

Development mode:
```bash
cd src
python main.py
```

Production mode with Gunicorn:
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker src.main:app
```

## API Endpoints

### POST /ai/generate_schedule

Generate a new planting schedule.

**Request:**
```json
{
  "user_id": "uuid",
  "garden_id": "uuid",
  "schedule_name": "Spring 2025",
  "start_date": "2025-03-01"
}
```

**Response:**
```json
{
  "schedule_id": "uuid",
  "diagram": "ASCII diagram",
  "tasks": [
    {
      "week_index": 0,
      "title": "Prepare soil",
      "description": "...",
      "plant_catalog_id": null,
      "due_date": "2025-03-01"
    }
  ]
}
```

### POST /ai/revise_schedule

Revise schedule based on feedback.

**Request:**
```json
{
  "schedule_id": "uuid",
  "task_id": "uuid",
  "text": "It rained all week, plants are waterlogged",
  "mood": "concerned"
}
```

**Response:**
```json
{
  "ok": true,
  "message": "Schedule revised...",
  "updated_tasks": ["task-uuid-1", "task-uuid-2"]
}
```

## Deployment

### Render

1. Create new Web Service
2. Connect repository
3. Set build command: `pip install -r ai-service/requirements.txt`
4. Set start command: `cd ai-service/src && gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app`
5. Add environment variables

### Fly.io

```bash
fly launch
fly secrets set SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=... ANTHROPIC_API_KEY=...
fly deploy
```

### Cloud Run

```bash
gcloud run deploy verdant-ai \
  --source ai-service \
  --region us-central1 \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...,ANTHROPIC_API_KEY=...
```

## Architecture

```
ai-service/
├── src/
│   ├── main.py              # FastAPI app
│   ├── models/
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── claude.py        # Claude AI integration
│   │   └── weather.py       # Weather API client
│   └── utils/
│       └── database.py      # Supabase client
├── requirements.txt
└── .env.example
```

## Security

- Service role key is ONLY used server-side
- Never expose service role key to clients
- Mobile app uses anon key + RLS policies
- All database queries respect RLS automatically through user context
