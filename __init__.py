from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.secret_key = '42866344300694f99fd79971e88cbb48'
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        'mysql+mysqlconnector://poohbae:cakehistory@poohbae.mysql.pythonanywhere-services.com/poohbae$CakeHistory'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 280,   # reconnect after 280s (before 300s timeout)
        'pool_pre_ping': True  # check if connection is alive before query
    }

    db.init_app(app)

    from models import User
    login_manager = LoginManager(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from routes import register_routes
    register_routes(app)

    return app
