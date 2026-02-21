import os

class Config:
    SECRET_KEY = "AIzaSyDQrXOzKtsOuUrzt-Se41FgN8g2Hhe09nY"

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    GEMINI_API_KEY = "AIzaSyDQrXOzKtsOuUrzt-Se41FgN8g2Hhe09nY"