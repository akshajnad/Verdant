import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pandas as pd

app = Flask(__name__)
app.secret_key = os.getenv("verdant157", "override")

# ---- Database: prefer DATABASE_URL (e.g., Render Postgres), else local SQLite ----
basedir = os.path.abspath(os.path.dirname(__file__))
default_sqlite = f"sqlite:///{os.path.join(basedir, 'app.db')}"
db_uri = os.getenv("DATABASE_URL", default_sqlite)

# Render sometimes provides postgres://; SQLAlchemy expects postgresql://
if db_uri.startswith("postgres://"):
    db_uri = db_uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -----------------------------
# DATABASE CONFIG
# -----------------------------
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "app.db")
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Create tables at import time so Gunicorn workers have the schema
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        app.logger.warning(f"DB init skipped/failed: {e}")

# -----------------------------
# MODELS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")

    phone_number = db.Column(db.String(30), default="")
    org_email = db.Column(db.String(100), default="")

class ProduceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    # Fields from shelter
    num_people = db.Column(db.Integer, default=0)
    volume_goal = db.Column(db.Float, default=0.0)
    calorie_goal = db.Column(db.Float, default=0.0)
    additional_needs = db.Column(db.String(200), default="")
    shelter_notes = db.Column(db.Text, default="")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="new")

    # Relationship to the user
    user = db.relationship("User", backref=db.backref("requests", lazy=True))

    # NEW CODE: Urgency field
    urgency = db.Column(db.Integer, default=1)  # Shelter can rank 1=low, 5=high, etc.

class SavedSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    diagram = db.Column(db.Text, default="")
    schedule_json = db.Column(db.Text, default="")
    user = db.relationship("User", backref=db.backref("saved_schedules", lazy=True))
# -----------------------------
# APP CONTEXT & DB CREATION
# -----------------------------
# This will create tables if they don't exist, each time the app starts.

# -----------------------------
# AUTH HELPERS
# -----------------------------
def is_logged_in():
    return "user_id" in session

def current_user():
    if not is_logged_in():
        return None
    return User.query.get(session["user_id"])

def requires_login(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            flash("Please log in first.")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

# -----------------------------
# RECOMMENDATION / SCHEDULING LOGIC
# -----------------------------
def parse_existing_crops(existing_crops_str):
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
                space = 0
                weeks = 0
            crops_data.append({
                "name": crop_name,
                "space": space,
                "weeks_grown": weeks
            })
    return crops_data

def recommend_crops(num_people, volume_goal, calorie_goal, additional_needs, free_space):
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

    if calorie_goal > 2000:
        recommended.append("Potatoes")
        recommended.append("Corn")
    if volume_goal > 10:
        recommended.append("Zucchini")
        recommended.append("Tomatoes")
        recommended.append("Bell Peppers")
    if "leafy greens" in additional_needs.lower():
        recommended.append("Lettuce")
        recommended.append("Kale")
    if not recommended:
        recommended = ["Tomatoes", "Carrots", "Onions"]

    final_crops = []
    space_left = free_space
    for crop in recommended:
        req = crop_space_requirements.get(crop, 5)
        if req <= space_left:
            final_crops.append(crop)
            space_left -= req

    return final_crops

def generate_planting_diagram(existing_crops, recommended_crops, garden_size):
    diagram = "Garden Layout Diagram\n\n"
    diagram += f"Total garden size: {garden_size} sq ft\n\n"
    diagram += "Existing Crops:\n"
    row_number = 1
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
    schedule = []
    # existing
    for ecrop in existing_crops:
        total_cycle = 12
        weeks_done = ecrop["weeks_grown"]
        weeks_left = max(0, total_cycle - weeks_done)
        schedule.append({
            "crop": ecrop["name"] + " (existing)",
            "planting_date": f"~{int(weeks_done)} weeks ago",
            "watering_instructions": "Continue watering as normal.",
            "weeding_instructions": "Weed weekly.",
            "harvest_info": f"Ready in about {weeks_left} more weeks",
            "weather_note": ""
        })

    # new
    base_planting_date = pd.Timestamp("2025-03-01")
    for i, crop in enumerate(recommended_crops):
        plant_date = base_planting_date + pd.Timedelta(weeks=i)
        harvest_date = plant_date + pd.Timedelta(weeks=10)
        schedule.append({
            "crop": crop + " (new)",
            "planting_date": str(plant_date.date()),
            "watering_instructions": "Water 1 inch/week (adjust if rainy).",
            "weeding_instructions": "Weed once/week.",
            "harvest_info": f"Estimated harvest around {harvest_date.date()}",
            "weather_note": ""
        })

    return schedule


# -----------------------------
# NEW: HOME PAGE ROUTE
# -----------------------------
@app.route("/")
def home():
    return render_template("home.html")

# -----------------------------
# AUTH ROUTES
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session["user_id"] = user.id
            return redirect(url_for("generate_schedule_view"))
        else:
            flash("Invalid credentials.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        phone_number = request.form.get("phone_number", "")
        org_email = request.form.get("org_email", "")

        existing = User.query.filter_by(username=username).first()
        if existing:
            flash("Username already exists.")
            return redirect(url_for("register"))

        new_user = User(
            username=username,
            password=password,
            phone_number=phone_number,
            org_email=org_email
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created! Please log in.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/generate_schedule", methods=["GET", "POST"])
@requires_login
def generate_schedule_view():
    user = current_user()
    if request.method == "POST":
        num_people = int(request.form.get("num_people", 0))
        volume_goal = float(request.form.get("volume_goal", 0))
        calorie_goal = float(request.form.get("calorie_goal", 0))
        additional_needs = request.form.get("additional_needs", "")
        shelter_notes = request.form.get("shelter_notes", "")
        urgency = int(request.form.get("urgency", 1))
        garden_size = float(request.form.get("garden_size", 0))
        existing_crops_str = request.form.get("existing_crops", "")

        produce_request = ProduceRequest(
            user_id=user.id,
            num_people=num_people,
            volume_goal=volume_goal,
            calorie_goal=calorie_goal,
            additional_needs=additional_needs,
            shelter_notes=shelter_notes,
            urgency=urgency
        )
        db.session.add(produce_request)
        db.session.commit()

        existing_crops = parse_existing_crops(existing_crops_str)
        used_space = sum(ec["space"] for ec in existing_crops)
        free_space = max(0, garden_size - used_space)

        recommended_crops = recommend_crops(
            num_people,
            volume_goal,
            calorie_goal,
            additional_needs,
            free_space
        )

        diagram = generate_planting_diagram(existing_crops, recommended_crops, garden_size)
        schedule = generate_schedule(existing_crops, recommended_crops)

        return render_template(
            "schedule_view.html",
            produce_request=produce_request,
            diagram=diagram,
            schedule=schedule,
            allow_save=True
        )

    return render_template("schedule_form.html")


@app.route("/save_schedule", methods=["POST"])
@requires_login
def save_schedule():
    user = current_user()
    name = request.form.get("name", "Untitled")
    is_favorite = request.form.get("is_favorite") == "1"
    diagram = request.form.get("diagram", "")
    schedule_json = request.form.get("schedule_json", "")
    new_sched = SavedSchedule(
        user_id=user.id,
        name=name,
        is_favorite=is_favorite,
        diagram=diagram,
        schedule_json=schedule_json,
    )
    db.session.add(new_sched)
    db.session.commit()
    flash("Schedule saved.")
    return redirect(url_for("saved_schedules"))


@app.route("/schedules")
@requires_login
def saved_schedules():
    user = current_user()
    schedules = (
        SavedSchedule.query.filter_by(user_id=user.id)
        .order_by(SavedSchedule.created_at.desc())
        .all()
    )
    return render_template("schedules.html", schedules=schedules)


@app.route("/schedules/<int:schedule_id>")
@requires_login
def view_schedule(schedule_id):
    sched = SavedSchedule.query.get_or_404(schedule_id)
    if sched.user_id != current_user().id:
        flash("Unauthorized")
        return redirect(url_for("saved_schedules"))
    try:
        schedule = json.loads(sched.schedule_json) if sched.schedule_json else []
    except Exception:
        schedule = []
    return render_template(
        "schedule_view.html",
        diagram=sched.diagram,
        schedule=schedule,
        allow_save=False,
    )


@app.route("/schedules/<int:schedule_id>/toggle_favorite", methods=["POST"])
@requires_login
def toggle_favorite(schedule_id):
    sched = SavedSchedule.query.get_or_404(schedule_id)
    if sched.user_id != current_user().id:
        flash("Unauthorized")
        return redirect(url_for("saved_schedules"))
    sched.is_favorite = not sched.is_favorite
    db.session.commit()
    return redirect(url_for("saved_schedules"))


@app.route("/schedules/<int:schedule_id>/delete", methods=["POST"])
@requires_login
def delete_schedule(schedule_id):
    sched = SavedSchedule.query.get_or_404(schedule_id)
    if sched.user_id != current_user().id:
        flash("Unauthorized")
        return redirect(url_for("saved_schedules"))
    db.session.delete(sched)
    db.session.commit()
    flash("Schedule deleted.")
    return redirect(url_for("saved_schedules"))

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
