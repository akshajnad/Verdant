"""Pydantic schemas for API validation."""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, UUID4


# =====================================================
# REQUEST MODELS
# =====================================================

class GenerateScheduleRequest(BaseModel):
    """Request to generate a new planting schedule."""
    user_id: str = Field(..., description="UUID of the user")
    garden_id: str = Field(..., description="UUID of the garden")
    schedule_name: str = Field(..., description="Name for the schedule")
    start_date: date = Field(..., description="Start date for the schedule")


class ReviseFeedbackRequest(BaseModel):
    """Request to revise schedule based on user feedback."""
    schedule_id: str = Field(..., description="UUID of the schedule")
    task_id: Optional[str] = Field(None, description="Optional specific task UUID")
    text: str = Field(..., description="User feedback text")
    mood: Optional[str] = Field(None, description="User mood tag")
    photos: Optional[List[str]] = Field(None, description="Optional photo URLs")


# =====================================================
# RESPONSE MODELS
# =====================================================

class TaskSchema(BaseModel):
    """Schema for a schedule task."""
    week_index: int
    title: str
    description: Optional[str] = None
    plant_catalog_id: Optional[str] = None
    due_date: Optional[str] = None


class GenerateScheduleResponse(BaseModel):
    """Response from schedule generation."""
    schedule_id: str
    diagram: Optional[str] = None
    tasks: List[TaskSchema]


class ReviseScheduleResponse(BaseModel):
    """Response from schedule revision."""
    ok: bool
    message: str
    updated_tasks: List[str] = []


# =====================================================
# INTERNAL MODELS (for Claude communication)
# =====================================================

class ClaudeScheduleResponse(BaseModel):
    """Expected structure from Claude API for schedule generation."""
    diagram: Optional[str] = None
    tasks: List[dict]


class ClaudeRevisionAction(BaseModel):
    """Action to take based on Claude's revision suggestion."""
    action_type: str  # "update_task", "add_task", "reschedule", etc.
    task_id: Optional[str] = None
    data: dict
