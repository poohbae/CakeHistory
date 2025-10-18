from datetime import datetime, timezone
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Cart, Order, OrderItem, Product, User

def register_routes(app):
    @app.route('/')
    def home():
        # Load top 3 featured products from the database
        cakes = Product.query.limit(3).all()
        return render_template('home.html', cakes=cakes)

    @app.route('/menu')
    def menu():
        cakes = Product.query.all()
        return render_template('menu.html', cakes=cakes)
    
    @app.route('/add_to_cart', methods=['POST'])
    @login_required
    def add_to_cart():
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))

        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found.'}), 404

        existing_item = Cart.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = Cart(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(new_item)

        db.session.commit()
        return jsonify({'success': True, 'message': f'{product.name} added to cart!'})

    @app.route('/cart')
    @login_required
    def cart():
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

    @app.route('/place_order', methods=['POST'])
    @login_required
    def place_order():
        data = request.get_json()
        method = data.get('method')         # pickup or delivery
        address = data.get('address', None)
        date_time = data.get('datetime')
        payment = data.get('payment')

        # validate datetime
        try:
            selected_dt = datetime.fromisoformat(date_time)
            if selected_dt < datetime.now(timezone.utc):
                return jsonify({'success': False, 'message': 'Please choose a future date/time.'})
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid date/time format.'})

        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty.'})

        total = 0
        for item in cart_items:
            total += item.product.price * item.quantity

        order = Order(user_id=current_user.id, total_amount=total)
        db.session.add(order)
        db.session.commit()

        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_each=item.product.price
            )
            db.session.add(order_item)
            db.session.delete(item)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Order placed successfully!'})

    @app.route('/login', methods=['GET', 'POST'])
    def login_user_route():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash('Login successful!', 'success')
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
            confirm_password = request.form['confirm_password']
            subscribed = True if request.form.get('subscribed') == 'yes' else False

            # Server-side password check
            if password != confirm_password:
                flash('Passwords do not match. Please try again.', 'danger')
                return redirect(url_for('register'))

            if User.query.filter_by(email=email).first():
                flash('Email already registered. Please login.', 'danger')
                return redirect(url_for('login_user_route'))

            new_user = User(
                name=name,
                email=email,
                password=generate_password_hash(password),
                subscribed=subscribed
            )
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

    @app.errorhandler(401)
    def unauthorized(e):
        flash('Please login to view your cart or place an order.', 'warning')
        return redirect(url_for('login_user_route'))
