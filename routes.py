from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Product

def register_routes(app):
    @app.route('/')
    def home():
        cakes = Product.query.all()
        return render_template('home.html', cakes=cakes)

    @app.route('/menu')
    def menu():
        cakes = Product.query.all()
        return render_template('menu.html', cakes=cakes)

    @app.route('/cart')
    @login_required
    def cart():
        from models import Cart
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        subtotal = sum(item.price * item.quantity for item in cart_items)
        delivery = 5.00 if cart_items else 0.00
        grand_total = subtotal + delivery
        return render_template(
            'cart.html',
            user=current_user,
            cart_items=cart_items,
            subtotal=subtotal,
            delivery=delivery,
            grand_total=grand_total
        )

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
        return render_template('login.html')

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
        return render_template('register.html')

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have logged out successfully.', 'info')
        return redirect(url_for('home'))

    @app.errorhandler(401)
    def unauthorized(e):
        flash('Please login to view your cart or place an order.', 'warning')
        return redirect(url_for('login_user_route'))
