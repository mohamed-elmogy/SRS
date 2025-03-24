from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin
import uuid


@login_manager.user_loader
def load_user(user_id):
    if User.query.get(user_id):
        return User.query.get(user_id)
    else:
        return Seller.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: f'b{uuid.uuid4()}')
    username = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    last_searched = db.Column(db.String(60))
    buy_history = db.relationship('Order', backref='buyer', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    category = db.Column(db.String(20))
    selling = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    discount = db.Column(db.Float, default=0)
    rating = db.Column(db.Float, default=0)
    raters = db.Column(db.Integer, default=0)


class Seller(db.Model, UserMixin):
    id = db.Column(db.String(36), primary_key=True, default=lambda: f's{uuid.uuid4()}')
    seller_name = db.Column(db.String(20), unique=True, nullable=False)
    phone = db.Column(db.String(12), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    products = db.relationship('Product', backref='seller', lazy=True)
    orders = db.relationship('Order', backref='seller', lazy=True)


class Cart(db.Model):
    buyer_id = db.Column(db.String, primary_key=True)
    product_id = db.Column(db.Integer, primary_key=True)
    price = db.Column(db.Float, nullable=False)


class PurchaseHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    buyer_address = db.Column(db.String(120), nullable=False)
    date_of_delivery = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    product_id = db.Column(db.Integer)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    buyer_address = db.Column(db.String(120), nullable=False)
    statue = db.Column(db.String(10), nullable=False, default='shipping')
    price = db.Column(db.Float, nullable=False)
    product_id = db.Column(db.Integer)


class Rated(db.Model):
    rater_id = db.Column(db.String, primary_key=True)
    product_id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.String(100))
    rate = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Vouchers(db.Model):
    voucher = db.Column(db.String, primary_key=True)
    seller_id = db.Column(db.Integer, primary_key=True)
    sale = db.Column(db.Float, nullable=False)
