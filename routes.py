from datetime import datetime, timezone
from flask import flash, jsonify, redirect, render_template, request, session, url_for
from flask_login import login_user, login_required, logout_user, current_user
from models import db, Box, Candle, Card, Cart, Feedback, Order, OrderItem, PaymentMethod, Product, User
from werkzeug.security import generate_password_hash, check_password_hash

def register_routes(app):
    @app.route('/')
    def home():
        # Load top 3 featured products from the database
        cakes = Product.query.limit(3).all()
        return render_template('home.html', cakes=cakes)
    
    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/menu')
    def menu():
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
        special_request = data.get('special_request', None)
        item_type = data.get('item_type', 'product')

        # Select correct model based on item_type
        if item_type == 'product':
            product = Product.query.get(product_id)
        elif item_type == 'candle':
            product = Candle.query.get(product_id)
        elif item_type == 'card':
            product = Card.query.get(product_id)
        elif item_type == 'box':
            product = Box.query.get(product_id)
        else:
            return jsonify({'success': False, 'message': 'Invalid item type.'}), 400

        if not product:
            return jsonify({'success': False, 'message': 'Item not found.'}), 404

        # Check if already in cart (same product + same option + same note)
        existing_item = Cart.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            option_selected=option_selected,
            special_request=special_request,
            item_type=item_type
        ).first()

        if existing_item:
            existing_item.quantity += quantity
        else:
            new_item = Cart(
                user_id=current_user.id,
                product_id=product_id,
                item_type=item_type,
                quantity=quantity,
                option_selected=option_selected,
                special_request=special_request
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
        cake_items, addon_items = [], []
        subtotal = 0

        for item in cart_items:
            # get the correct item object
            if item.item_type == 'product':
                product = Product.query.get(item.product_id)
            elif item.item_type == 'candle':
                product = Candle.query.get(item.product_id)
            elif item.item_type == 'card':
                product = Card.query.get(item.product_id)
            elif item.item_type == 'box':
                product = Box.query.get(item.product_id)
            else:
                continue  # skip unknown

            if not product:
                continue

            total_price = product.price * item.quantity
            subtotal += total_price

            # group accordingly
            if item.item_type == 'product':
                cake_items.append({
                    'name': product.name,
                    'image': product.img,
                    'price': product.price,
                    'quantity': item.quantity,
                    'total': total_price,
                    'special_request': item.special_request
                })
            else:
                addon_items.append({
                    'name': product.name,
                    'image': product.img,
                    'price': product.price,
                    'quantity': item.quantity,
                    'total': total_price,
                    'special_request': item.special_request,
                    'option_selected': item.option_selected
                })

        payment_methods = PaymentMethod.query.all()

        return render_template(
            'cart.html',
            user=current_user,
            cake_items=cake_items,
            addon_items=addon_items,
            subtotal=subtotal,
            payment_methods=payment_methods
        )

    @app.route('/place_order', methods=['POST'])
    @login_required
    def place_order():
        data = request.get_json()
        method = data.get('method')
        address_data = data.get('address', None)
        date_time = data.get('datetime')
        payment_method_id = data.get('payment_method_id')
        delivery_fee = float(data.get('delivery_fee', 0))

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

        # Calculate total
        total = 0
        for item in cart_items:
            # Find correct product object by type
            if item.item_type == 'product':
                product = Product.query.get(item.product_id)
            elif item.item_type == 'candle':
                product = Candle.query.get(item.product_id)
            elif item.item_type == 'card':
                product = Card.query.get(item.product_id)
            elif item.item_type == 'box':
                product = Box.query.get(item.product_id)
            else:
                continue

            if product:
                total += product.price * item.quantity

        total += delivery_fee

        # Parse delivery address
        delivery_address = None
        if method == 'delivery' and address_data:
            try:
                area, _ = address_data.split('|')
                delivery_address = area.strip()
            except ValueError:
                delivery_address = address_data

        # 🧾 Create the order
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            payment_method_id=payment_method_id,
            delivery_method=method,
            delivery_address=delivery_address,
            scheduled_datetime=selected_dt
        )
        db.session.add(order)
        db.session.commit()

        # 🧁 Transfer cart items
        for item in cart_items:
            # Handle cakes
            if item.item_type == 'product':
                product = Product.query.get(item.product_id)
                if not product:
                    continue
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    price_each=product.price,
                    special_request=item.special_request
                )
                db.session.add(order_item)

            # Handle add-ons (candles/cards/boxes)
            elif item.item_type in ['candle', 'card', 'box']:
                # find product to get price
                model = {'candle': Candle, 'card': Card, 'box': Box}[item.item_type]
                product = model.query.get(item.product_id)
                if not product:
                    continue
                addon = OrderAddon(
                    order_id=order.id,
                    addon_type=item.item_type,
                    addon_id=item.product_id,
                    option_selected=item.option_selected,  # ✅ Save the selected option
                    quantity=item.quantity,
                    price_each=product.price
                )
                db.session.add(addon)

            # remove from cart
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
        session.clear()  # clears flash messages and session data
        return redirect(url_for('login_user_route'))

    @app.errorhandler(401)
    def unauthorized(e):
        flash('Please login to view your cart or place an order.', 'warning')
        return redirect(url_for('login_user_route'))
