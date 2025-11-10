"""Claude AI service integration."""
import json
import logging
from typing import Dict, Any, List, Optional
from anthropic import Anthropic
from datetime import date, timedelta

logger = logging.getLogger(__name__)


class ClaudeService:
    """Service for interacting with Claude AI."""

    def __init__(self, api_key: str):
        """Initialize Claude service with API key."""
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    async def generate_schedule(
        self,
        profile: Dict[str, Any],
        garden: Dict[str, Any],
        cells: List[Dict[str, Any]],
        produce_request: Optional[Dict[str, Any]],
        weather_summary: str,
        plant_catalog: List[Dict[str, Any]],
        start_date: date
    ) -> Dict[str, Any]:
        """
        Generate a planting schedule using Claude.

        Args:
            profile: User profile data
            garden: Garden configuration
            cells: Garden cells with existing plants
            produce_request: User's produce goals
            weather_summary: Weather forecast summary
            plant_catalog: Available plants
            start_date: Schedule start date

        Returns:
            Dict with 'diagram' and 'tasks' keys
        """
        system_prompt = """You are Verdant's expert agronomy AI planner. You help users plan their vegetable gardens.

Your response MUST be valid JSON with this exact structure:
{
  "diagram": "optional ASCII or text diagram",
  "tasks": [
    {
      "week_index": 0,
      "title": "Task title",
      "description": "Detailed description",
      "plant_catalog_id": "uuid-or-null"
    }
  ]
}

Guidelines:
1. Create realistic, actionable weekly tasks for at least 8-12 weeks
2. Consider weather patterns (avoid planting before last frost, schedule watering around rain)
3. Respect garden dimensions and plant spacing requirements
4. Balance nutrition goals with practical growing requirements
5. Group plants with similar water/sun needs together
6. Include soil prep, planting, maintenance, and harvest tasks
7. Be specific with locations (e.g., "Row 0, Columns 0-3")
8. Return ONLY valid JSON, no additional text"""

        user_prompt = self._build_prompt(
            profile, garden, cells, produce_request,
            weather_summary, plant_catalog, start_date
        )

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.4,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            # Extract text content
            content = response.content[0].text

            # Parse JSON response
            result = json.loads(content)

            # Validate structure
            if "tasks" not in result:
                raise ValueError("Response missing 'tasks' key")

            logger.info(f"Generated schedule with {len(result['tasks'])} tasks")
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude response as JSON: {e}")
            logger.error(f"Response content: {content[:500]}")
            raise ValueError("Claude returned invalid JSON")
        except Exception as e:
            logger.error(f"Error generating schedule: {e}")
            raise

    async def revise_schedule(
        self,
        schedule: Dict[str, Any],
        tasks: List[Dict[str, Any]],
        feedback_text: str,
        mood: Optional[str],
        garden: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Revise schedule based on user feedback.

        Args:
            schedule: Current schedule data
            tasks: Current tasks
            feedback_text: User's feedback
            mood: Optional mood indicator
            garden: Garden configuration

        Returns:
            Dict with revision actions
        """
        system_prompt = """You are Verdant's adaptive garden planner. A user has provided feedback on their schedule.

Analyze the feedback and suggest revisions. Return JSON with this structure:
{
  "analysis": "Brief analysis of the feedback",
  "actions": [
    {
      "action_type": "update_task|add_task|reschedule",
      "task_id": "uuid-if-updating",
      "data": {
        "week_index": 0,
        "title": "Updated title",
        "description": "Updated description",
        "status": "pending"
      }
    }
  ]
}

Be conservative - only suggest necessary changes. Consider:
- Weather impacts (rain delays, heat stress)
- User capability/time constraints
- Plant health observations
- Seasonal timing adjustments"""

        # Build context
        task_summary = "\n".join([
            f"Week {t['week_index']}: {t['title']} ({t.get('status', 'pending')})"
            for t in tasks[:20]  # Limit context
        ])

        user_prompt = f"""Schedule: {schedule['name']}
Garden: {garden['rows']}x{garden['cols']} grid, {garden.get('area_m2', 'N/A')} m²
Start Date: {schedule['start_date']}

Current Tasks (first 20):
{task_summary}

User Feedback:
Mood: {mood or 'Not specified'}
"{feedback_text}"

Suggest revisions based on this feedback."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                temperature=0.3,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}]
            )

            content = response.content[0].text
            result = json.loads(content)

            logger.info(f"Generated {len(result.get('actions', []))} revision actions")
            return result

        except Exception as e:
            logger.error(f"Error revising schedule: {e}")
            raise

    def _build_prompt(
        self,
        profile: Dict[str, Any],
        garden: Dict[str, Any],
        cells: List[Dict[str, Any]],
        produce_request: Optional[Dict[str, Any]],
        weather_summary: str,
        plant_catalog: List[Dict[str, Any]],
        start_date: date
    ) -> str:
        """Build the user prompt for schedule generation."""

        # Garden layout
        existing_plants = [
            f"R{c['r']}C{c['c']}: {c.get('label', 'Unknown')}"
            for c in cells if c.get('label')
        ]

        # Available plants
        plant_list = [
            f"- {p['common_name']}: {p.get('spacing_cm', 30)}cm spacing, "
            f"{p.get('cycle_weeks', 10)} weeks, "
            f"water={p.get('water_need', 'medium')}, "
            f"sun={p.get('sun_requirement', 'full')}"
            for p in plant_catalog
        ]

        # Goals
        goals = "No specific goals"
        if produce_request:
            goals = f"""- People to feed: {produce_request.get('num_people', 0)}
- Volume goal: {produce_request.get('volume_goal', 0)} kg/week
- Calorie goal: {produce_request.get('calorie_goal', 0)} kcal/week
- Additional needs: {produce_request.get('additional_needs', 'None')}
- Urgency: {produce_request.get('urgency', 1)}/5"""

        prompt = f"""Generate a detailed planting schedule for the following garden:

=== Garden Configuration ===
Dimensions: {garden['rows']} rows × {garden['cols']} columns
Area: {garden.get('area_m2', 'Unknown')} m²
Location: {garden.get('location_lat', 'N/A')}, {garden.get('location_lon', 'N/A')}
Timezone: {garden.get('timezone', 'Unknown')}

=== Existing Plants ===
{chr(10).join(existing_plants) if existing_plants else 'None - new garden'}

=== Goals ===
{goals}

=== Available Plants ===
{chr(10).join(plant_list[:15])}

=== Weather Forecast ===
{weather_summary}

=== Schedule Details ===
Start Date: {start_date}
Duration: 12 weeks minimum

Please create a comprehensive schedule that:
1. Prepares the soil in early weeks
2. Staggers planting to extend harvest season
3. Respects spacing requirements (assume 30cm per grid cell)
4. Groups plants by water/sun needs
5. Schedules maintenance (weeding, watering, feeding)
6. Plans harvest windows

Return ONLY valid JSON."""

        return prompt


# Service will be initialized with API key in main.py
