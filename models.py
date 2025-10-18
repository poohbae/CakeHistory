from flask_login import UserMixin
from datetime import datetime, timezone
from __init__ import db

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    subscribed = db.Column(db.Boolean, default=False)

    # Relationship — One user can have many orders
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(120))
    img2 = db.Column(db.String(120))
    img3 = db.Column(db.String(120))
    description = db.Column(db.Text)

    # Relationship — One product can appear in many order items
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

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
    name = db.Column(db.String(120), nullable=False)  # e.g., Celebration Card
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(120))
    description = db.Column(db.Text)
    has_design_choice = db.Column(db.Boolean, default=True)

class Box(db.Model):
    __tablename__ = 'boxes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)  # e.g., Cake Box
    price = db.Column(db.Float, nullable=False)
    img = db.Column(db.String(120))
    description = db.Column(db.Text)
    has_size_option = db.Column(db.Boolean, default=True)

class PaymentMethod(db.Model):
    __tablename__ = 'payment_methods'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    img = db.Column(db.String(150))

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    option_selected = db.Column(db.String(50))

    user = db.relationship('User', backref='cart_items', lazy=True)
    product = db.relationship('Product', backref='cart_entries', lazy=True)

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

    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete")
    payment_method = db.relationship('PaymentMethod', lazy=True)

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_each = db.Column(db.Float, nullable=False)

class OrderAddon(db.Model):
    __tablename__ = 'order_addons'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    addon_type = db.Column(db.Enum('candle', 'card', 'box'), nullable=False)
    addon_id = db.Column(db.Integer, nullable=False)
    option_selected = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=1)
    price_each = db.Column(db.Float, nullable=False)

    # Relationship (optional)
    order = db.relationship('Order', backref=db.backref('addons', cascade='all, delete-orphan', lazy=True))

    def __repr__(self):
        return f"<OrderAddon {self.addon_type} (x{self.quantity}) - {self.option_selected}>"
    
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1–5 stars
    comments = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Relationships
    user = db.relationship('User', backref='feedbacks', lazy=True)
    order = db.relationship('Order', backref='feedbacks', lazy=True)
