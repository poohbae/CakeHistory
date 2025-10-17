from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database config
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'mysql+mysqlconnector://poohbae:CakeHistory@poohbae.mysql.pythonanywhere-services.com/poohbae$CakeHistory'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_user_route'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --------------------------
# Public pages
# --------------------------
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/menu')
def menu():
    cakes = [
        {"name": "Chocolate Heaven", "price": 35.00, "img": "choco_cake.jpg"},
        {"name": "Strawberry Dream", "price": 40.00, "img": "strawberry_cake.jpg"},
        {"name": "Vanilla Classic", "price": 30.00, "img": "vanilla_cake.jpg"}
    ]
    return render_template('menu.html', cakes=cakes)

# --------------------------
# Restricted page (Order)
# --------------------------
@app.route('/order')
@login_required
def order():
    return render_template('order.html', user=current_user)

# --------------------------
# Auth routes
# --------------------------
@app.route('/login', methods=['GET', 'POST'])
def login_user_route():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash('Login successful! 🍰', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', show_nav=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('login_user_route'))

        new_user = User(name=name, email=email, password_hash=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login_user_route'))

    return render_template('register.html', show_nav=True)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out successfully.', 'info')
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
