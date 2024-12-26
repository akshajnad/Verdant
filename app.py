from flask import Flask, request, render_template
import numpy as np
import pandas as pd
import joblib
import os

# If using optional weather helper:
from weather_api_helper import get_weather_forecast

app = Flask(__name__)

# If you have an OpenWeatherMap API key, set it here or use env variable
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

# 1) Load the trained regression model and encoder at startup
model_path = "crop_yield_model.pkl"
encoder_path = "categorical_encoder.pkl"

if os.path.exists(model_path) and os.path.exists(encoder_path):
    yield_model = joblib.load(model_path)
    categorical_encoder = joblib.load(encoder_path)
    print("Loaded trained yield_model and categorical_encoder.")
else:
    yield_model = None
    categorical_encoder = None
    print("Trained model not found. Running in fallback mode.")


# -------------------------------------------
# COMPLEX AI LOGIC USING OUR MODEL
# -------------------------------------------

def predict_yield(region, climate_type, volume_goal, crop_type):
    """
    Predict the likely yield (in pounds) given user inputs.
    Using our previously trained RandomForestRegressor.
    """
    if (yield_model is None) or (categorical_encoder is None):
        # If we don't have a model, just return a fallback
        return 10.0  # naive fallback

    # We'll replicate the preprocessing we did during training:
    # 1) transform the categorical columns
    # 2) append the numeric volume_goal
    cat_input = [[region, climate_type, crop_type]]  # 3 categorical inputs
    cat_encoded = categorical_encoder.transform(cat_input)
    vol = np.array([[volume_goal]])  # numeric input

    # Combine them
    X_processed = np.hstack([cat_encoded, vol])

    # Predict
    predicted = yield_model.predict(X_processed)
    return float(predicted[0])

def recommend_crops(num_people, volume_goal, calorie_goal, additional_needs, region, climate_type):
    """
    Suggest a set of crops by using:
      - the predicted yield from our model
      - user-specified needs (calorie, volume, etc.)
    For simplicity, let's pick from a small list of potential crops.
    We'll estimate yield for each crop and pick the top 2-3 with highest predicted yield.
    """
    # Potential crops to consider
    possible_crops = ["Tomatoes", "Potatoes", "Zucchini", "Bell Peppers", "Lettuce", "Kale", "Carrots", "Onions"]

    # If user has specific mention like 'leafy greens', we ensure at least one leafy green
    forced_crops = []
    if "leafy" in additional_needs.lower():
        forced_crops = ["Lettuce", "Kale"]

    # Let's generate (crop -> predicted_yield) for each possible crop
    predictions = []
    for crop in possible_crops:
        est_yield = predict_yield(region, climate_type, volume_goal, crop)
        predictions.append((crop, est_yield))

    # Sort by descending yield
    predictions.sort(key=lambda x: x[1], reverse=True)

    # Now pick the top 3
    recommended = [crop for (crop, yld) in predictions[:3]]

    # If forced crops are not in recommended, add them
    for fcrop in forced_crops:
        if fcrop not in recommended:
            recommended.append(fcrop)

    return recommended


def generate_planting_diagram(recommended_crops, garden_size):
    """
    Returns a simple ASCII or textual diagram of how to layout the garden.
    """
    diagram = "Garden Layout Diagram (Text-based)\n\n"
    diagram += f"Total garden size: {garden_size} sq ft\n\n"
    diagram += "Rows:\n"

    row_number = 1
    for crop in recommended_crops:
        diagram += f"  Row {row_number}: {crop}\n"
        row_number += 1

    return diagram


def generate_schedule(recommended_crops, weather_forecast=None):
    """
    Generate a simple schedule with planting, watering, weeding,
    and expected harvest times.
    """
    schedule = []
    base_planting_date = pd.Timestamp("2025-03-01")  # arbitrary start

    for i, crop in enumerate(recommended_crops):
        # Plant each crop 1 week apart
        planting_date = base_planting_date + pd.Timedelta(weeks=i)
        harvest_date = planting_date + pd.Timedelta(weeks=10)  # naive assumption
        schedule.append({
            "crop": crop,
            "planting_date": str(planting_date.date()),
            "watering_instructions": "Water 1 inch per week (adjust if no rain).",
            "weeding_instructions": "Weed once a week or as needed.",
            "harvest_date": str(harvest_date.date()),
            "weather_note": ""
        })

    if weather_forecast:
        # Convert forecast list of dicts into a quick lookup
        weather_dict = {day["date"]: day for day in weather_forecast}
        for entry in schedule:
            plant_date = entry["planting_date"]
            if plant_date in weather_dict:
                desc = weather_dict[plant_date]["weather"]
                entry["weather_note"] = f"On planting day, forecast: {desc}"

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

        # We'll assume region & climate type come from your own domain logic
        # For example, you could map latitude/longitude to a region.
        # For this example, let's just allow user input or guess "north"/"temperate".
        region = request.form.get("region", "north")
        climate_type = request.form.get("climate_type", "temperate")

        # 1) Recommend crops using the advanced model
        recommended_crops = recommend_crops(
            num_people, volume_goal, calorie_goal,
            additional_needs, region, climate_type
        )

        # 2) Generate diagram
        diagram = generate_planting_diagram(recommended_crops, garden_size)

        # 3) (Optional) Get weather forecast
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
    return "Please submit your data via the form on the home page."


if __name__ == "__main__":
    app.run(debug=True)
