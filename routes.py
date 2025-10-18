from datetime import datetime, timezone
from flask import flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_user, login_required, logout_user, current_user
from models import db, Cart, Feedback, Order, OrderItem, Product, User
from werkzeug.security import generate_password_hash, check_password_hash

def register_routes(app):
    @app.route('/')
    def home():
        # Load top 3 featured products from the database
        cakes = Product.query.limit(3).all()
        return render_template('home.html', cakes=cakes)

    @app.route('/menu')
    def menu():
        from models import Product, Candle, Card, Box
        cakes = Product.query.all()
        candles = Candle.query.all()
        cards = Card.query.all()
        boxes = Box.query.all()
        return render_template('menu.html', cakes=cakes, candles=candles, cards=cards, boxes=boxes)

    @app.route('/add_to_cart', methods=['POST'])
    @login_required
    def add_to_cart():
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        option_selected = data.get('option_selected', None)

        # Validate product
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Product not found.'}), 404

        # Check if already in cart (same product + same option)
        existing_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            option_selected=option_selected
        ).first()

        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = Cart(
                user_id=current_user.id,
                product_id=product_id,
                quantity=quantity,
                option_selected=option_selected
            )
            db.session.add(new_item)

        try:
            db.session.commit()
            return jsonify({'success': True, 'message': f'{product.name} added to cart!'})
        except Exception as e:
            db.session.rollback()
            print("Error:", e)
            return jsonify({'success': False, 'message': 'Database error. Please try again later.'})

    @app.route('/cart')
    @login_required
    def cart():
        cart_items = Cart.query.filter_by(user_id=current_user.id).all()

        # Separate cakes and add-ons
        cake_items = []
        addon_items = []
        subtotal = 0

        for item in cart_items:
            product = item.product
            if not product:
                continue  # skip broken references

            total_price = product.price * item.quantity
            subtotal += total_price

            # Add-on items (candles, cards, boxes) share same structure
            if "candle" in product.name.lower() or "card" in product.name.lower() or "box" in product.name.lower():
                addon_items.append({
                    'name': product.name,
                    'image': product.img,
                    'price': product.price,
                    'quantity': item.quantity,
                    'total': total_price
                })
            else:
                cake_items.append({
                    'name': product.name,
                    'image': product.img,
                    'price': product.price,
                    'quantity': item.quantity,
                    'total': total_price
                })

        return render_template(
            'cart.html',
            user=current_user,
            cake_items=cake_items,
            addon_items=addon_items,
            subtotal=subtotal
        )

    @app.route('/place_order', methods=['POST'])
    @login_required
    def place_order():
        data = request.get_json()
        method = data.get('method')
        address = data.get('address', None)
        date_time = data.get('datetime')
        payment_method_id = data.get('payment_method_id')

        # Validate datetime
        try:
            selected_dt = datetime.fromisoformat(date_time)
            if selected_dt < datetime.now(timezone.utc):
                return jsonify({'success': False, 'message': 'Please choose a future date/time.'})
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid date/time format.'})

        cart_items = Cart.query.filter_by(user_id=current_user.id).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Cart is empty.'})

        total = sum(item.product.price * item.quantity for item in cart_items)

        # Create order and include datetime
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            payment_method_id=payment_method_id,
            delivery_method=method,
            delivery_address=address if method == 'delivery' else None,
            scheduled_datetime=selected_dt
        )
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
    
    @app.route('/order')
    @login_required
    def order():
        orders = (
            Order.query
            .filter_by(user_id=current_user.id)
            .order_by(Order.order_date.desc())
            .all()
        )
        return render_template('order.html', orders=orders)

    @app.route('/feedback', methods=['GET', 'POST'])
    @login_required
    def feedback():
        if request.method == 'POST':
            order_id = request.form.get('order_id')
            rating = int(request.form.get('rating'))
            comments = request.form.get('comments')

            # Check if order belongs to the user
            order = Order.query.filter_by(id=order_id, user_id=current_user.id).first()
            if not order:
                flash('Invalid order selected.', 'danger')
                return redirect(url_for('feedback'))

            # Save feedback
            new_feedback = Feedback(
                user_id=current_user.id,
                order_id=order_id,
                rating=rating,
                comments=comments
            )
            db.session.add(new_feedback)
            db.session.commit()

            flash('Thank you for your feedback! 💗', 'success')
            return redirect(url_for('feedback'))

        # Load data for the page
        user_orders = Order.query.filter_by(user_id=current_user.id).all()
        previous_feedback = Feedback.query.filter_by(user_id=current_user.id).order_by(Feedback.created_at.desc()).all()

        return render_template('feedback.html', orders=user_orders, feedbacks=previous_feedback)

    @app.route('/login', methods=['GET', 'POST'])
    def login_user_route():
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            user = User.query.filter_by(email=email).first()

            if user and check_password_hash(user.password, password):
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
