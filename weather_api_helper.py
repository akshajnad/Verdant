import requests
import datetime

def get_weather_forecast(api_key, lat, lon):
    """
    Fetch 7-day weather forecast (daily data) from OpenWeatherMap OneCall API.
    Returns a list of dicts with 'date', 'temp', and 'weather' keys.
    """
    url = "https://api.openweathermap.org/data/2.5/onecall"
    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "current,minutely,hourly,alerts",
        "units": "metric",
        "appid": api_key
    }

    response = requests.get(url, params=params)
    data = response.json()

    forecasts = []
    for day in data["daily"]:
        date = datetime.datetime.fromtimestamp(day["dt"]).strftime('%Y-%m-%d')
        temp = day["temp"]["day"]  # daily average temperature
        weather_desc = day["weather"][0]["description"]
        forecasts.append({
            "date": date,
            "temp": temp,
            "weather": weather_desc
        })
    return forecasts
