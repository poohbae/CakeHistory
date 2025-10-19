from flask_login import UserMixin
from datetime import datetime, timezone
from __init__ import db

# ============================================================
# USER MODEL
# ============================================================
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    subscribed = db.Column(db.Boolean, default=False)

    # One-to-many → a user can have multiple orders and feedbacks
    orders = db.relationship('Order', backref='user', lazy=True)
    cart_items = db.relationship('Cart', backref='user', lazy=True)
    feedbacks = db.relationship('Feedback', backref='user', lazy=True)

    def __repr__(self):
        return f"<User {self.email}>"

# ============================================================
# CAKE MODEL
# ============================================================
class Cake(db.Model):
    __tablename__ = 'cakes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    indi_price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(120))
    img2 = db.Column(db.String(120))
    img3 = db.Column(db.String(120))
    description = db.Column(db.Text)

    order_items = db.relationship('OrderItem', backref='cake', lazy=True)

# ============================================================
# CANDLE, CARD, BOX MODELS
# ============================================================
class Candle(db.Model):
    __tablename__ = 'candles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(120))
    description = db.Column(db.Text)
    type = db.Column(db.String(50), nullable=False)

class Card(db.Model):
    __tablename__ = 'cards'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(120))
    description = db.Column(db.Text)
    has_design_choice = db.Column(db.Boolean, default=True)

class Box(db.Model):
    __tablename__ = 'boxes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(120))
    description = db.Column(db.Text)

# ============================================================
# PAYMENT METHOD MODEL
# ============================================================
class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    img = db.Column(db.String(150))

# ============================================================
# CART MODEL
# ============================================================
class Cart(db.Model):
    __tablename__ = 'cart'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    item_type = db.Column(db.String(50), nullable=False, default='product')
    quantity = db.Column(db.Integer, nullable=False, default=1)
    option_selected = db.Column(db.String(50))
    special_request = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False, default=0.0)

# ============================================================
# ORDER MODEL
# ============================================================
class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_methods.id'))
    total_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default='Pending')
    delivery_method = db.Column(db.String(20))  # 'pickup' or 'delivery'
    delivery_address = db.Column(db.String(255), nullable=True)
    scheduled_datetime = db.Column(db.DateTime, nullable=False)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='subquery', cascade='all, delete-orphan')
    addons = db.relationship('OrderAddon', backref='order', lazy='subquery', cascade='all, delete-orphan')
    payment_method = db.relationship('PaymentMethod', lazy='joined')

    feedbacks = db.relationship('Feedback', backref='order', lazy=True)

    def __repr__(self):
        return f"<Order #{self.id} - User {self.user_id}>"

# ============================================================
# ORDER ITEM MODEL
# ============================================================
class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('cakes.id'), nullable=False)  # ✅ FIXED
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_each = db.Column(db.Float, nullable=False)
    special_request = db.Column(db.String(255))

    product = db.relationship('Cake', lazy='joined')

    def __repr__(self):
        return f"<OrderItem {self.product.name if self.product else 'Unknown'} × {self.quantity}>"

# ============================================================
# ORDER ADDON MODEL
# ============================================================
class OrderAddon(db.Model):
    __tablename__ = 'order_addons'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    addon_id = db.Column(db.Integer, nullable=False)
    addon_name = db.Column(db.String(100), nullable=False)
    addon_type = db.Column(db.Enum('candle', 'card', 'box'), nullable=False)
    option_selected = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)
    price_each = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"<OrderAddon {self.addon_name} × {self.quantity}>"

# ============================================================
# FEEDBACK MODEL
# ============================================================
class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5 stars
    comments = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f"<Feedback Order={self.order_id} Rating={self.rating}>"
