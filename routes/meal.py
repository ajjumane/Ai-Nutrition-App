from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from utils.ai import (
    generate_meal_plan,
    generate_weekly_plan,
    replace_single_meal
)
from extensions import db
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem
from reportlab.platypus import FrameBreak
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
meal_bp = Blueprint("meal", __name__)




def calculate_bmi(weight, height):
    height_m = float(height) / 100
    bmi = float(weight) / (height_m ** 2)
    return round(bmi, 1)


def bmi_status(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif 18.5 <= bmi < 25:
        return "Normal"
    elif 25 <= bmi < 30:
        return "Overweight"
    else:
        return "Obese"


def calculate_calories(age, gender, height, weight, activity):
    if gender.lower() == "male":
        bmr = 10 * float(weight) + 6.25 * float(height) - 5 * float(age) + 5
    else:
        bmr = 10 * float(weight) + 6.25 * float(height) - 5 * float(age) - 161

    activity_multiplier = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very active": 1.9
    }

    return round(bmr * activity_multiplier.get(activity.lower(), 1.2))


def calculate_water_intake(weight):
    return round((float(weight) * 35) / 1000, 2)


def get_user_profile():
    return (
        current_user.age,
        current_user.gender,
        current_user.height,
        current_user.weight,
        current_user.goal,
        current_user.diet,
        current_user.activity
    )


# -------------------------
# Routes
# -------------------------

@meal_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@meal_bp.route("/generate", methods=["POST"])
@login_required
def generate():

    # Save profile first time
    if not current_user.age:
        current_user.age = request.form["age"]
        current_user.gender = request.form["gender"]
        current_user.height = request.form["height"]
        current_user.weight = request.form["weight"]
        current_user.goal = request.form["goal"]
        current_user.diet = request.form["diet"]
        current_user.activity = request.form["activity"]
        db.session.commit()

    age, gender, height, weight, goal, diet, activity = get_user_profile()

    plan = generate_meal_plan(age, gender, height, weight, goal, diet, activity)

    bmi = calculate_bmi(weight, height)
    bmi_result = bmi_status(bmi)
    calories = calculate_calories(age, gender, height, weight, activity)
    water = calculate_water_intake(weight)

    if goal.lower() == "lose":
        target_calories = calories - 400
    elif goal.lower() == "gain":
        target_calories = calories + 400
    else:
        target_calories = calories

    return render_template(
        "result.html",
        plan=plan,
        weekly=False,
        bmi=bmi,
        bmi_result=bmi_result,
        calories=calories,
        target_calories=target_calories,
        water=water
    )


# --------- WEEKLY PLAN ---------

@meal_bp.route("/generate-weekly")
@login_required
def generate_weekly():

    age, gender, height, weight, goal, diet, activity = get_user_profile()

    weekly_plan = generate_weekly_plan(
        age, gender, height, weight, goal, diet, activity
    )

    bmi = calculate_bmi(weight, height)
    bmi_result = bmi_status(bmi)
    calories = calculate_calories(age, gender, height, weight, activity)
    water = calculate_water_intake(weight)

    return render_template(
        "result.html",
        plan=weekly_plan,
        weekly=True,
        bmi=bmi,
        bmi_result=bmi_result,
        calories=calories,
        target_calories=calories,
        water=water
    )


# --------- REPLACE SINGLE MEAL ---------

@meal_bp.route("/replace-meal", methods=["POST"])
@login_required
def replace_meal():

    meal_type = request.json.get("meal_type")

    age, gender, height, weight, goal, diet, activity = get_user_profile()

    new_meal = replace_single_meal(
        meal_type, age, gender, height, weight, goal, diet, activity
    )

    return jsonify({"new_meal": new_meal})


# --------- RESET ---------

@meal_bp.route("/reset-profile")
@login_required
def reset_profile():
    current_user.age = None
    current_user.gender = None
    current_user.height = None
    current_user.weight = None
    current_user.goal = None
    current_user.diet = None
    current_user.activity = None

    db.session.commit()
    return redirect(url_for("meal.dashboard"))

@meal_bp.route("/download-pdf")
@login_required
def download_pdf():

    age, gender, height, weight, goal, diet, activity = get_user_profile()

    # Generate 7-day plan for PDF
    weekly_plan = generate_weekly_plan(
        age, gender, height, weight, goal, diet, activity
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)

    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("AI Weekly Meal Plan", styles["Title"]))
    elements.append(Spacer(1, 0.3 * inch))

    for day, meals in weekly_plan.items():
        elements.append(Paragraph(day, styles["Heading2"]))
        elements.append(Spacer(1, 0.2 * inch))

        for meal_type, meal_text in meals.items():
            elements.append(Paragraph(f"<b>{meal_type}</b>", styles["Heading3"]))
            elements.append(Spacer(1, 0.1 * inch))

            items = meal_text.strip().split("\n")
            bullet_points = [
                ListItem(Paragraph(item.strip("- "), styles["Normal"]))
                for item in items if item
            ]

            elements.append(ListFlowable(bullet_points, bulletType='bullet'))
            elements.append(Spacer(1, 0.2 * inch))

        elements.append(Spacer(1, 0.5 * inch))

    doc.build(elements)
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name="AI_Weekly_Meal_Plan.pdf",
        mimetype="application/pdf"
    )