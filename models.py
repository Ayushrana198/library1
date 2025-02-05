from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def get_id(self):
        return str(self.user_id)

class Section(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    sec_id = db.Column(db.Integer, primary_key=True)
    sec_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    sec_image = db.Column(db.String(300), nullable=True)  # Image file path
    books = db.relationship('Book', backref='section', cascade="all, delete")

class Book(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    sec_id = db.Column(db.Integer, db.ForeignKey('section.sec_id'), nullable=False)
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300000000000), nullable=False)
    price = db.Column(db.Float, nullable=False)
    book_image = db.Column(db.String(300), nullable=True)  # Image file path
    request = db.relationship('Request', backref='book', cascade="all, delete", foreign_keys='Request.book_id')
    feedback = db.relationship('Feedback', backref='book', cascade="all, delete", foreign_keys='Feedback.book_id')

class Request(db.Model):
    req_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    title = db.Column(db.String(100), db.ForeignKey('book.title'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    request_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now())
    expiry_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now() + timedelta(days=7))

    user = db.relationship('User', backref='requests')
    

class Feedback(db.Model):
    feed_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    title = db.Column(db.String(100), db.ForeignKey('book.title'), nullable=False)
    feedback = db.Column(db.String(500), nullable=False)

    user = db.relationship('User', backref='feedbacks')
    