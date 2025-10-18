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
    total_amount = db.Column(db.Float, nullable=False)
    order_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default='Pending')

    # Relationship — one order has many items
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete")

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price_each = db.Column(db.Float, nullable=False)
