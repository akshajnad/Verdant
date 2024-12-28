from flask import Flask, request, render_template
import numpy as np
import pandas as pd

app = Flask(__name__)

# -------------------------------------------
# ADVANCED RULE-BASED RECOMMENDATION
# -------------------------------------------
def recommend_crops(num_people, volume_goal, calorie_goal, additional_needs, free_space):
    """
    Suggest crops based on:
      - calorie goals
      - volume goals
      - specific needs (e.g. 'leafy greens')
      - remaining garden space (free_space)

    Returns a list of recommended crops that fit into the free space.
    """

    # Potential crops (crop_name -> space_required in sq ft)
    # This is a simplistic assumption about how much space each crop might need.
    # Adjust as appropriate for real-world data.
    crop_space_requirements = {
        "Potatoes": 10,
        "Corn": 12,
        "Zucchini": 8,
        "Tomatoes": 6,
        "Bell Peppers": 6,
        "Lettuce": 4,
        "Kale": 4,
        "Carrots": 5,
        "Onions": 5,
    }

    recommended = []

    # 1) If user has large calorie_goal, prefer carb-heavy
    if calorie_goal > 2000:
        recommended.append("Potatoes")
        recommended.append("Corn")

    # 2) If volume_goal is large, suggest high-yield
    if volume_goal > 10:
        recommended.append("Zucchini")
        recommended.append("Tomatoes")
        recommended.append("Bell Peppers")

    # 3) If user specifically requests 'leafy greens', ensure lettuce or kale
    if "leafy greens" in additional_needs.lower():
        recommended.append("Lettuce")
        recommended.append("Kale")

    # 4) If nothing was added, provide some default suggestions
    if not recommended:
        recommended = ["Tomatoes", "Carrots", "Onions"]

    # 5) Ensure crops fit into the available space
    final_crops = []
    space_left = free_space

    # We'll keep them in the order chosen. If one doesn't fit, skip it.
    for crop in recommended:
        space_req = crop_space_requirements.get(crop, 5)  # default 5 if not found
        if space_req <= space_left:
            final_crops.append(crop)
            space_left -= space_req

    # If absolutely no crops fit, we might return an empty list
    # or just a message. For simplicity, let's return whatever we got.
    return final_crops


def parse_existing_crops(existing_crops_str):
    """
    Parse a user-supplied string like:
      'Tomatoes:50:4;Lettuce:25:2'
    meaning:
      - Tomatoes occupying 50 sq ft, grown for 4 weeks
      - Lettuce occupying 25 sq ft, grown for 2 weeks

    Returns a list of dicts like:
      [
        {"name": "Tomatoes", "space": 50, "weeks_grown": 4},
        {"name": "Lettuce", "space": 25, "weeks_grown": 2}
      ]
    """
    if not existing_crops_str.strip():
        return []

    crops_data = []
    items = existing_crops_str.split(";")
    for item in items:
        parts = item.split(":")
        if len(parts) == 3:
            crop_name = parts[0].strip()
            try:
                space = float(parts[1].strip())
                weeks = float(parts[2].strip())
            except ValueError:
                # If parsing fails, ignore or handle gracefully
                space = 0
                weeks = 0
            crops_data.append({
                "name": crop_name,
                "space": space,
                "weeks_grown": weeks
            })
    return crops_data


def generate_planting_diagram(existing_crops, recommended_crops, garden_size):
    """
    Returns a textual diagram of how to layout the garden,
    factoring in existing crops and their used space, plus new crops.
    """
    diagram = "Garden Layout Diagram (Text-based)\n\n"
    diagram += f"Total garden size: {garden_size} sq ft\n\n"
    diagram += "Existing Crops:\n"

    row_number = 1

    # List existing crops as "already in the garden"
    for ecrop in existing_crops:
        diagram += f"  Row {row_number} (existing): {ecrop['name']} occupying {ecrop['space']} sq ft\n"
        row_number += 1

    if recommended_crops:
        diagram += "\nNew Crops:\n"
        for crop in recommended_crops:
            diagram += f"  Row {row_number} (new): {crop}\n"
            row_number += 1
    else:
        diagram += "\nNo space left for new crops.\n"

    return diagram


def generate_schedule(existing_crops, recommended_crops):
    """
    Generate a schedule for both existing and new crops.
    - Existing crops have already been grown for some weeks.
    - New crops start from week 0 in this naive example.

    We'll just assign:
     - existing crops: (already grown X weeks) with an assumed total of 10-12 weeks needed
     - new crops: 10 weeks from now
    """
    schedule = []

    # First handle existing crops
    for ecrop in existing_crops:
        # Suppose each crop has a 12-week total cycle in this naive example
        total_weeks = 12
        weeks_remaining = max(0, total_weeks - ecrop["weeks_grown"])

        schedule.append({
            "crop": ecrop["name"] + " (existing)",
            "planting_date": f"~{int(ecrop['weeks_grown'])} weeks ago", 
            "weeks_grown": ecrop["weeks_grown"],
            "watering_instructions": "Continue watering 1 inch/week.",
            "weeding_instructions": "Weed weekly, watch for overgrowth.",
            "harvest_date": f"In about {weeks_remaining} weeks (approx).",
            "notes": "Existing crop already in progress."
        })

    # Next handle new crops
    base_planting_date = pd.Timestamp("2025-03-01")  # arbitrary start
    for i, crop in enumerate(recommended_crops):
        planting_date = base_planting_date + pd.Timedelta(weeks=i)
        harvest_date = planting_date + pd.Timedelta(weeks=10)  # naive assumption
        schedule.append({
            "crop": crop + " (new)",
            "planting_date": str(planting_date.date()),
            "weeks_grown": 0,
            "watering_instructions": "Water 1 inch per week (adjust if no rain).",
            "weeding_instructions": "Weed once a week or as needed.",
            "harvest_date": str(harvest_date.date()),
            "notes": ""
        })

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

        # Parse existing crops
        existing_crops_str = request.form.get("existing_crops", "")
        existing_crops = parse_existing_crops(existing_crops_str)

        # Calculate how much space is already taken by existing crops
        used_space = sum(c["space"] for c in existing_crops)
        free_space = max(0, garden_size - used_space)

        # 1) Recommend new crops that fit into the free space
        recommended_crops = recommend_crops(
            num_people,
            volume_goal,
            calorie_goal,
            additional_needs,
            free_space
        )

        # 2) Generate diagram (existing + new)
        diagram = generate_planting_diagram(existing_crops, recommended_crops, garden_size)

        # 3) Generate schedule (existing + new)
        schedule = generate_schedule(existing_crops, recommended_crops)

        # Return everything to a results page
        return render_template(
            "results.html",
            recommended_crops=recommended_crops,
            diagram=diagram,
            schedule=schedule
        )
    else:
        return render_template("index.html")


@app.route("/results")
def results():
    """ This route is used after POSTing from index. """
    return "Please submit your data via the form on the home page."


if __name__ == "__main__":
    app.run(debug=True)
