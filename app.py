from flask import Flask
from config import Config
from extensions import db, login_manager
import webbrowser
import threading

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    from models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes.auth import auth_bp
    from routes.meal import meal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(meal_bp)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

def open_browser():
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=True)