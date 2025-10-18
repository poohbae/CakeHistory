from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Initialize SQLAlchemy globally (no circular import)
db = SQLAlchemy()

# Factory function
def create_app():
    app = Flask(__name__)
    app.secret_key = '42866344300694f99fd79971e88cbb48'

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'mysql+mysqlconnector://poohbae:cakehistory@poohbae.mysql.pythonanywhere-services.com/poohbae$CakeHistory'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Setup Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login_user_route'

    # Import models here to register them with SQLAlchemy
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Import routes (to register blueprints or normal routes)
    from .routes import register_routes
    register_routes(app)

    return app
