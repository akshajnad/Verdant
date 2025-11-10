"""Supabase database client."""
import os
from typing import Optional, Dict, Any, List
from datetime import date, datetime
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Client for Supabase database operations."""

    def __init__(self, url: str, service_role_key: str):
        """Initialize Supabase client with service role key."""
        self.client: Client = create_client(url, service_role_key)

    # =====================================================
    # USER & PROFILE QUERIES
    # =====================================================

    def get_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile by ID."""
        try:
            response = self.client.table("profiles").select("*").eq("id", user_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return None

    # =====================================================
    # GARDEN QUERIES
    # =====================================================

    def get_garden(self, garden_id: str) -> Optional[Dict[str, Any]]:
        """Get garden by ID."""
        try:
            response = self.client.table("gardens").select("*").eq("id", garden_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching garden: {e}")
            return None

    def get_garden_cells(self, garden_id: str) -> List[Dict[str, Any]]:
        """Get all cells for a garden."""
        try:
            response = self.client.table("garden_cells").select("*").eq("garden_id", garden_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching garden cells: {e}")
            return []

    # =====================================================
    # PLANT CATALOG
    # =====================================================

    def get_plant_catalog(self) -> List[Dict[str, Any]]:
        """Get all plants from catalog."""
        try:
            response = self.client.table("plant_catalog").select("*").execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching plant catalog: {e}")
            return []

    def get_plant_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get plant by common name."""
        try:
            response = self.client.table("plant_catalog").select("*").eq("common_name", name).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching plant by name: {e}")
            return None

    # =====================================================
    # PRODUCE REQUESTS
    # =====================================================

    def get_latest_produce_request(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the most recent produce request for a user."""
        try:
            response = (
                self.client.table("produce_requests")
                .select("*")
                .eq("owner_id", user_id)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error fetching produce request: {e}")
            return None

    # =====================================================
    # SCHEDULES
    # =====================================================

    def create_schedule(
        self,
        owner_id: str,
        garden_id: str,
        name: str,
        start_date: date,
        diagram: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new schedule."""
        try:
            response = (
                self.client.table("schedules")
                .insert({
                    "owner_id": owner_id,
                    "garden_id": garden_id,
                    "name": name,
                    "start_date": str(start_date),
                    "diagram": diagram or ""
                })
                .execute()
            )
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating schedule: {e}")
            return None

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule by ID."""
        try:
            response = self.client.table("schedules").select("*").eq("id", schedule_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            return None

    # =====================================================
    # SCHEDULE TASKS
    # =====================================================

    def create_tasks_batch(self, tasks: List[Dict[str, Any]]) -> bool:
        """Create multiple schedule tasks."""
        try:
            self.client.table("schedule_tasks").insert(tasks).execute()
            logger.info(f"Created {len(tasks)} tasks")
            return True
        except Exception as e:
            logger.error(f"Error creating tasks: {e}")
            return False

    def get_schedule_tasks(self, schedule_id: str) -> List[Dict[str, Any]]:
        """Get all tasks for a schedule."""
        try:
            response = (
                self.client.table("schedule_tasks")
                .select("*")
                .eq("schedule_id", schedule_id)
                .order("week_index")
                .execute()
            )
            return response.data or []
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a schedule task."""
        try:
            self.client.table("schedule_tasks").update(updates).eq("id", task_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating task: {e}")
            return False

    # =====================================================
    # FEEDBACK
    # =====================================================

    def create_feedback(
        self,
        schedule_id: str,
        text: str,
        task_id: Optional[str] = None,
        mood: Optional[str] = None,
        photos: Optional[List[str]] = None,
        ai_response: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a feedback entry."""
        try:
            data = {
                "schedule_id": schedule_id,
                "text": text,
                "task_id": task_id,
                "mood": mood,
                "photos": photos,
                "ai_response": ai_response
            }
            response = self.client.table("schedule_feedback").insert(data).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Error creating feedback: {e}")
            return None

    # =====================================================
    # WEATHER CACHE
    # =====================================================

    def get_cached_weather(
        self,
        garden_id: str,
        date: date,
        provider: str = "open-meteo"
    ) -> Optional[Dict[str, Any]]:
        """Get cached weather data."""
        try:
            response = (
                self.client.table("weather_cache")
                .select("*")
                .eq("garden_id", garden_id)
                .eq("date", str(date))
                .eq("provider", provider)
                .single()
                .execute()
            )
            return response.data
        except Exception as e:
            # Cache miss is expected, don't log as error
            return None

    def cache_weather(
        self,
        garden_id: str,
        date: date,
        provider: str,
        payload: Dict[str, Any]
    ) -> bool:
        """Cache weather data."""
        try:
            self.client.table("weather_cache").insert({
                "garden_id": garden_id,
                "date": str(date),
                "provider": provider,
                "payload": payload
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error caching weather: {e}")
            return False
