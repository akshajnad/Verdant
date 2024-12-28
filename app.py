from flask import Flask, request, render_template
import numpy as np
import pandas as pd

# If you're using the optional weather helper:
from weather_api_helper import get_weather_forecast

app = Flask(__name__)

# If you have an OpenWeatherMap API key, put it here (or use environment variables):
OPENWEATHER_API_KEY = "8ff13b9bcdc7e5db9eab3b58f1839512"

# -------------------------------------------
# SIMPLIFIED "AI" / PLANNING LOGIC
# -------------------------------------------
def recommend_crops(num_people, volume_goal, calorie_goal, additional_needs):
    """
    This function returns a recommended list of vegetables to plant
    based on the shelter's input. In a real scenario, you'd train
    an ML model or use a more advanced algorithm. Here, we'll just do
    a simple rule-based approach for demonstration.
    """
    # Example simplistic logic:
    recommended = []

    # If calorie_goal > some threshold, suggest carb-heavy crops (like potatoes, corn)
    if calorie_goal > 2000:
        recommended.append("Potatoes")

    # If volume_goal is large, suggest high-yield vegetables
    if volume_goal > 10:
        recommended.append("Zucchini")
        recommended.append("Tomatoes")
        recommended.append("Bell Peppers")

    # If "leafy greens" is in additional_needs, add lettuce or kale
    if "leafy greens" in additional_needs.lower():
        recommended.append("Lettuce")
        recommended.append("Kale")

    # Default suggestions if none were added
    if not recommended:
        recommended = ["Tomatoes", "Carrots", "Onions"]

    return recommended


def generate_planting_diagram(recommended_crops, garden_size):
    """
    Returns a simple ASCII or textual diagram of how to layout the garden.
    For demonstration, we'll just produce a row-based layout.
    garden_size = total sq. ft. or sq. meters
    """
    diagram = "Garden Layout Diagram (Text-based)\n\n"
    diagram += f"Total garden size: {garden_size} sq ft\n\n"
    diagram += "Rows:\n"

    row_number = 1
    for crop in recommended_crops:
        diagram += f"  Row {row_number}: {crop}\n"
        row_number += 1

    # You can get creative with spacing or more advanced diagrams
    return diagram


def generate_schedule(recommended_crops, weather_forecast=None):
    """
    Generate a simple schedule with planting, watering, weeding,
    and expected harvest times.
    We'll assume a generic timeframe for demonstration. 
    """
    schedule = []
    # We'll just assign fixed intervals for each crop (very naive example)
    # In a real model, you'd factor in climate zone, forecast, growth cycles, etc.
    base_planting_date = pd.Timestamp("2025-03-01")  # arbitrary "start"

    for i, crop in enumerate(recommended_crops):
        # Plant each crop 1 week apart, harvest ~ 8-12 weeks later
        planting_date = base_planting_date + pd.Timedelta(weeks=i)
        harvest_date = planting_date + pd.Timedelta(weeks=10)  # naive assumption
        schedule.append({
            "crop": crop,
            "planting_date": str(planting_date.date()),
            "watering_instructions": "Water 1 inch per week (adjust if no rain).",
            "weeding_instructions": "Weed once a week or as needed.",
            "harvest_date": str(harvest_date.date())
        })

    # Optionally factor in weather data if provided
    # For demonstration, we'll just note if there's predicted rain on planting day
    if weather_forecast:
        # Convert forecast list of dicts into a quick lookup
        weather_dict = {day["date"]: day for day in weather_forecast}

        for entry in schedule:
            plant_date = entry["planting_date"]
            if plant_date in weather_dict:
                desc = weather_dict[plant_date]["weather"]
                entry["weather_note"] = f"On planting day, forecast: {desc}"
            else:
                entry["weather_note"] = "No specific forecast data for planting day."

    return schedule


# -------------------------------------------
# FLASK ROUTES
# -------------------------------------------

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Displays the form for the shelter to submit data.
    """
    if request.method == "POST":
        # Grab inputs from the form
        num_people = int(request.form.get("num_people", 0))
        volume_goal = float(request.form.get("volume_goal", 0))
        calorie_goal = float(request.form.get("calorie_goal", 0))
        additional_needs = request.form.get("additional_needs", "")
        garden_size = float(request.form.get("garden_size", 0))
        latitude = float(request.form.get("latitude", 0))
        longitude = float(request.form.get("longitude", 0))

        # 1) Recommend crops
        recommended_crops = recommend_crops(num_people, volume_goal, calorie_goal, additional_needs)

        # 2) Generate diagram
        diagram = generate_planting_diagram(recommended_crops, garden_size)

        # 3) (Optional) Get weather forecast
        #    If no API key or lat/lon not provided, skip
        weather_forecast = None
        if OPENWEATHER_API_KEY and latitude and longitude:
            weather_forecast = get_weather_forecast(OPENWEATHER_API_KEY, latitude, longitude)

        # 4) Generate schedule
        schedule = generate_schedule(recommended_crops, weather_forecast)

        # Return everything to a results page
        return render_template("results.html",
                               recommended_crops=recommended_crops,
                               diagram=diagram,
                               schedule=schedule)
    else:
        return render_template("index.html")


@app.route("/results")
def results():
    """ This route is used after POSTing from index. """
    # Normally, you'd do the logic in the POST route and pass results.
    # We'll just redirect to "/" if accessed directly.
    return "Please submit your data via the form on the home page."


if __name__ == "__main__":
    app.run(debug=True)
