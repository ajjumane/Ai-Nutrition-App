from google import genai
from config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)


# -----------------------------
# Helpers
# -----------------------------

def parse_plan(text):
    data = {
        "Breakfast": "",
        "Lunch": "",
        "Dinner": "",
        "Snacks": "",
        "Tips": ""
    }

    current_key = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        for key in data:
            if line.lower().startswith(key.lower()):
                current_key = key
                data[key] = ""
                break
        else:
            if current_key:
                data[current_key] += line + "\n"

    return data


def parse_weekly_plan(text):
    weekly = {}
    current_day = None
    buffer = ""

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        if line.lower().startswith("day"):
            if current_day and buffer:
                weekly[current_day] = parse_plan(buffer)
                buffer = ""
            current_day = line
        else:
            buffer += line + "\n"

    if current_day and buffer:
        weekly[current_day] = parse_plan(buffer)

    return weekly


# -----------------------------
# 1-DAY PLAN
# -----------------------------

def generate_meal_plan(age, gender, height, weight, goal, diet, activity):

    prompt = f"""
Return a 1-day meal plan in EXACTLY this format:

Breakfast:
- item 1
- item 2

Lunch:
- item 1
- item 2

Dinner:
- item 1
- item 2

Snacks:
- item 1
- item 2

Tips:
- tip 1
- tip 2

For:
Age: {age}
Gender: {gender}
Height: {height} cm
Weight: {weight} kg
Goal: {goal}
Diet: {diet}
Activity: {activity}

ONLY the structured plan.
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )

        return parse_plan(response.text.strip())

    except Exception:
        return {
            "Breakfast": "- Oats\n- Fruit",
            "Lunch": "- Rice\n- Dal",
            "Dinner": "- Roti\n- Sabzi",
            "Snacks": "- Fruits\n- Nuts",
            "Tips": "- Drink water"
        }


# -----------------------------
# REAL 7-DAY PLAN (UPGRADED)
# -----------------------------

def generate_weekly_plan(age, gender, height, weight, goal, diet, activity):

    prompt = f"""
Generate a COMPLETE 7-day meal plan.

STRICT FORMAT:

Day 1
Breakfast:
- item
Lunch:
- item
Dinner:
- item
Snacks:
- item
Tips:
- tip

Day 2
...

Continue until Day 7.

Ensure:
- No repetition across days
- Meals align with user's goal
- Meals match diet type

User:
Age: {age}
Gender: {gender}
Height: {height}
Weight: {weight}
Goal: {goal}
Diet: {diet}
Activity: {activity}

ONLY structured output.
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )

        return parse_weekly_plan(response.text.strip())

    except Exception:
        fallback = {}
        for i in range(1, 8):
            fallback[f"Day {i}"] = generate_meal_plan(
                age, gender, height, weight, goal, diet, activity
            )
        return fallback


# -----------------------------
# REPLACE SINGLE MEAL
# -----------------------------

def replace_single_meal(meal_type, age, gender, height, weight, goal, diet, activity):

    prompt = f"""
Generate ONLY a new {meal_type}.

Return EXACT format:
- item 1
- item 2

Match user profile.

User:
Age: {age}
Gender: {gender}
Height: {height}
Weight: {weight}
Goal: {goal}
Diet: {diet}
Activity: {activity}

NO explanations.
"""

    try:
        response = client.models.generate_content(
            model="models/gemini-flash-latest",
            contents=prompt
        )

        return response.text.strip()

    except Exception:
        return "- Healthy option 1\n- Healthy option 2"