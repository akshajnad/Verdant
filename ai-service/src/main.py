"""Main FastAPI application for Verdant AI service."""
import os
import logging
from datetime import date, timedelta
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.schemas import (
    GenerateScheduleRequest,
    GenerateScheduleResponse,
    ReviseFeedbackRequest,
    ReviseScheduleResponse,
    TaskSchema
)
from services.claude import ClaudeService
from services.weather import weather_service
from utils.database import DatabaseClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Verdant AI Service",
    description="AI-powered garden planning service using Claude",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check required environment variables
REQUIRED_ENV_VARS = {
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_ROLE_KEY": os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY")
}

missing_vars = [key for key, value in REQUIRED_ENV_VARS.items() if not value]

# Initialize services (will be None if env vars missing)
db_client = None
claude_service = None

if missing_vars:
    logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
    logger.warning("API endpoints will return errors until environment is configured")
    logger.warning("See .env.example for required configuration")
else:
    # Initialize services
    try:
        db_client = DatabaseClient(
            url=REQUIRED_ENV_VARS["SUPABASE_URL"],
            service_role_key=REQUIRED_ENV_VARS["SUPABASE_SERVICE_ROLE_KEY"]
        )
        logger.info("Database client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database client: {e}")

    try:
        claude_service = ClaudeService(
            api_key=REQUIRED_ENV_VARS["ANTHROPIC_API_KEY"]
        )
        logger.info("Claude service initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Claude service: {e}")


# =====================================================
# ROOT & HEALTH CHECK
# =====================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    config_status = "configured" if not missing_vars else "missing configuration"

    response = {
        "service": "Verdant AI Service",
        "version": "2.0.0",
        "status": "running",
        "configuration": config_status,
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "generate_schedule": "POST /ai/generate_schedule",
            "revise_schedule": "POST /ai/revise_schedule"
        },
        "message": "Welcome to Verdant AI! Visit /docs for interactive API documentation."
    }

    if missing_vars:
        response["warning"] = f"Missing environment variables: {', '.join(missing_vars)}"
        response["help"] = "Copy .env.example to .env and fill in your credentials"

    return response


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health = {
        "status": "ok",
        "service": "verdant-ai",
        "database": "connected" if db_client else "not configured",
        "ai": "connected" if claude_service else "not configured"
    }

    if missing_vars:
        health["status"] = "degraded"
        health["missing_config"] = missing_vars

    return health


# =====================================================
# SCHEDULE GENERATION
# =====================================================

@app.post("/ai/generate_schedule", response_model=GenerateScheduleResponse)
async def generate_schedule(request: GenerateScheduleRequest):
    """
    Generate a new planting schedule using Claude AI.

    This endpoint:
    1. Fetches user profile, garden, and produce request data
    2. Retrieves or fetches weather forecast
    3. Calls Claude to generate a structured schedule
    4. Stores the schedule and tasks in Supabase
    5. Returns the schedule ID and task list
    """
    try:
        # Check if services are initialized
        if not db_client or not claude_service:
            raise HTTPException(
                status_code=503,
                detail=f"Service not configured. Missing: {', '.join(missing_vars)}"
            )

        logger.info(f"Generating schedule for user {request.user_id}, garden {request.garden_id}")

        # 1. Fetch user data
        profile = db_client.get_profile(request.user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")

        # 2. Fetch garden data
        garden = db_client.get_garden(request.garden_id)
        if not garden:
            raise HTTPException(status_code=404, detail="Garden not found")

        # Verify ownership
        if garden["owner_id"] != request.user_id:
            raise HTTPException(status_code=403, detail="Unauthorized access to garden")

        # 3. Fetch garden cells and produce request
        cells = db_client.get_garden_cells(request.garden_id)
        produce_request = db_client.get_latest_produce_request(request.user_id)

        # 4. Fetch plant catalog
        plant_catalog = db_client.get_plant_catalog()

        # 5. Get weather forecast
        weather_summary = "Weather data unavailable"
        if garden.get("location_lat") and garden.get("location_lon"):
            # Check cache first
            today = date.today()
            cached = db_client.get_cached_weather(
                garden_id=request.garden_id,
                date=today,
                provider="open-meteo"
            )

            if cached:
                logger.info("Using cached weather data")
                weather_data = cached["payload"]
            else:
                logger.info("Fetching fresh weather data")
                weather_data = await weather_service.get_weather_forecast(
                    latitude=float(garden["location_lat"]),
                    longitude=float(garden["location_lon"]),
                    days=14
                )
                # Cache it
                db_client.cache_weather(
                    garden_id=request.garden_id,
                    date=today,
                    provider="open-meteo",
                    payload=weather_data
                )

            weather_summary = weather_service.summarize_forecast(weather_data)

        # 6. Generate schedule with Claude
        schedule_data = await claude_service.generate_schedule(
            profile=profile,
            garden=garden,
            cells=cells,
            produce_request=produce_request,
            weather_summary=weather_summary,
            plant_catalog=plant_catalog,
            start_date=request.start_date
        )

        # 7. Create schedule in database
        schedule = db_client.create_schedule(
            owner_id=request.user_id,
            garden_id=request.garden_id,
            name=request.schedule_name,
            start_date=request.start_date,
            diagram=schedule_data.get("diagram", "")
        )

        if not schedule:
            raise HTTPException(status_code=500, detail="Failed to create schedule")

        # 8. Create tasks
        tasks_to_insert = []
        for task_data in schedule_data["tasks"]:
            week_idx = task_data["week_index"]
            due_date = request.start_date + timedelta(days=7 * week_idx)

            tasks_to_insert.append({
                "schedule_id": schedule["id"],
                "week_index": week_idx,
                "title": task_data["title"],
                "description": task_data.get("description"),
                "plant_catalog_id": task_data.get("plant_catalog_id"),
                "due_date": str(due_date),
                "status": "pending"
            })

        success = db_client.create_tasks_batch(tasks_to_insert)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create tasks")

        # 9. Return response
        task_schemas = [
            TaskSchema(
                week_index=t["week_index"],
                title=t["title"],
                description=t.get("description"),
                plant_catalog_id=t.get("plant_catalog_id"),
                due_date=t["due_date"]
            )
            for t in tasks_to_insert
        ]

        logger.info(f"Successfully created schedule {schedule['id']} with {len(task_schemas)} tasks")

        return GenerateScheduleResponse(
            schedule_id=schedule["id"],
            diagram=schedule_data.get("diagram"),
            tasks=task_schemas
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# SCHEDULE REVISION (FEEDBACK)
# =====================================================

@app.post("/ai/revise_schedule", response_model=ReviseScheduleResponse)
async def revise_schedule(request: ReviseFeedbackRequest):
    """
    Revise a schedule based on user feedback.

    This endpoint:
    1. Records the user feedback
    2. Fetches current schedule and tasks
    3. Calls Claude to analyze feedback and suggest revisions
    4. Applies the revisions to the database
    5. Returns summary of changes
    """
    try:
        # Check if services are initialized
        if not db_client or not claude_service:
            raise HTTPException(
                status_code=503,
                detail=f"Service not configured. Missing: {', '.join(missing_vars)}"
            )

        logger.info(f"Revising schedule {request.schedule_id} based on feedback")

        # 1. Fetch schedule
        schedule = db_client.get_schedule(request.schedule_id)
        if not schedule:
            raise HTTPException(status_code=404, detail="Schedule not found")

        # 2. Fetch garden (for context)
        garden = db_client.get_garden(schedule["garden_id"])
        if not garden:
            raise HTTPException(status_code=404, detail="Garden not found")

        # 3. Fetch current tasks
        tasks = db_client.get_schedule_tasks(request.schedule_id)

        # 4. Call Claude for revision suggestions
        revision_data = await claude_service.revise_schedule(
            schedule=schedule,
            tasks=tasks,
            feedback_text=request.text,
            mood=request.mood,
            garden=garden
        )

        # 5. Store feedback with AI response
        feedback = db_client.create_feedback(
            schedule_id=request.schedule_id,
            text=request.text,
            task_id=request.task_id,
            mood=request.mood,
            photos=request.photos,
            ai_response=revision_data.get("analysis", "")
        )

        # 6. Apply revision actions
        updated_task_ids = []
        actions = revision_data.get("actions", [])

        for action in actions:
            action_type = action.get("action_type")
            task_id = action.get("task_id")
            data = action.get("data", {})

            if action_type == "update_task" and task_id:
                # Update existing task
                success = db_client.update_task(task_id, data)
                if success:
                    updated_task_ids.append(task_id)

            elif action_type == "add_task":
                # Add new task
                data["schedule_id"] = request.schedule_id
                if "due_date" not in data and "week_index" in data:
                    start_date = date.fromisoformat(schedule["start_date"])
                    due_date = start_date + timedelta(days=7 * data["week_index"])
                    data["due_date"] = str(due_date)

                db_client.create_tasks_batch([data])
                updated_task_ids.append("new")

            # Add more action types as needed (reschedule, etc.)

        logger.info(f"Applied {len(updated_task_ids)} revisions to schedule {request.schedule_id}")

        return ReviseScheduleResponse(
            ok=True,
            message=revision_data.get("analysis", "Schedule revised based on your feedback"),
            updated_tasks=updated_task_ids
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revising schedule: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# SERVER STARTUP
# =====================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=os.getenv("ENVIRONMENT") == "development"
    )
