"""Weather service integration using Open-Meteo API."""
import httpx
from datetime import date, datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from Open-Meteo."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    async def get_weather_forecast(
        self,
        latitude: float,
        longitude: float,
        days: int = 14
    ) -> Dict[str, Any]:
        """
        Fetch weather forecast from Open-Meteo API.

        Args:
            latitude: Location latitude
            longitude: Location longitude
            days: Number of days to forecast (default 14)

        Returns:
            Dict with weather forecast data
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_mean,windspeed_10m_max",
            "timezone": "auto",
            "forecast_days": days
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(self.BASE_URL, params=params)
                response.raise_for_status()
                data = response.json()

                logger.info(f"Weather data fetched for lat={latitude}, lon={longitude}")
                return data

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching weather: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching weather: {e}")
            raise

    def summarize_forecast(self, forecast_data: Dict[str, Any]) -> str:
        """
        Create a human-readable summary of the weather forecast.

        Args:
            forecast_data: Raw forecast data from Open-Meteo

        Returns:
            Formatted string summary
        """
        if not forecast_data or "daily" not in forecast_data:
            return "Weather data unavailable."

        daily = forecast_data["daily"]
        dates = daily.get("time", [])
        temp_max = daily.get("temperature_2m_max", [])
        temp_min = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        precip_prob = daily.get("precipitation_probability_mean", [])

        summary_lines = ["Weather Forecast (next 7 days):"]

        for i in range(min(7, len(dates))):
            date_str = dates[i]
            t_max = temp_max[i] if i < len(temp_max) else "N/A"
            t_min = temp_min[i] if i < len(temp_min) else "N/A"
            rain = precip[i] if i < len(precip) else 0
            rain_prob = precip_prob[i] if i < len(precip_prob) else 0

            # Format line
            line = f"  {date_str}: {t_min}°C - {t_max}°C"
            if rain > 0 or rain_prob > 30:
                line += f", Rain: {rain}mm ({rain_prob}% chance)"
            summary_lines.append(line)

        # Add key insights
        avg_temp_max = sum(temp_max[:7]) / min(7, len(temp_max)) if temp_max else 0
        total_precip = sum(precip[:7]) if precip else 0

        summary_lines.append(f"\nKey insights:")
        summary_lines.append(f"  - Avg high temp: {avg_temp_max:.1f}°C")
        summary_lines.append(f"  - Total precipitation expected: {total_precip:.1f}mm")

        # Identify dry windows
        dry_days = []
        for i in range(min(7, len(dates))):
            rain_prob_val = precip_prob[i] if i < len(precip_prob) else 100
            if rain_prob_val < 30:
                dry_days.append(dates[i])

        if dry_days:
            summary_lines.append(f"  - Best days for outdoor work: {', '.join(dry_days[:3])}")

        return "\n".join(summary_lines)


# Singleton instance
weather_service = WeatherService()
