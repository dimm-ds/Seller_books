from flask_login import UserMixin

from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, Date, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base, UserMixin):

    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)

    cart_items = relationship('CartItem', back_populates='user')
    orders = relationship('Order', back_populates='bayer')
    review = relationship('Review', back_populates='user')

class Book(Base):

    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String(50), nullable=False)
    author = Column(String(50), nullable=False)
    price = Column(Float, nullable=False)
    genre = Column(String(50), nullable=False)
    cover = Column(String(50), nullable=False)
    description = Column(String(200), nullable=False)
    rating = Column(Float)
    rating_count = Column(Integer)
    year = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50), nullable=False)

    in_cart = relationship('CartItem', back_populates='book')
    in_order_item = relationship('OrderItem', back_populates='book')
    in_review = relationship('Review', back_populates='book')


class CartItem(Base):

    __tablename__ = 'cart_items'

    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), primary_key=True, nullable=False)
    count = Column(Integer, nullable=False)

    user = relationship('User', back_populates='cart_items')
    book = relationship('Book', back_populates='in_cart')


class Order(Base):

    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(Date, nullable=False)
    status = Column(String(20), nullable=False)
    total_amount = Column(Float, nullable=False)
    user_phone = Column(String(20), nullable=False)
    address = Column(String(200), nullable=False)
    book_list = Column(JSON)
    payment_method = Column(String(50), nullable=False, default='card')
    delivery_method = Column(String(50), nullable=False, default='courier')
    customer_name = Column(String(100), nullable=False)
    cash_on_delivery = Column(Boolean, default=False)
    delivery_date = Column(String(20), nullable=False)

    bayer = relationship('User', back_populates='orders')
    item = relationship('OrderItem', back_populates='order')


class OrderItem(Base):

    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    book_count = Column(Integer)
    cost = Column(Float)

    book = relationship('Book', back_populates='in_order_item')
    order = relationship('Order', back_populates='item')


class Review(Base):

    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    review = Column(String(200))
    parent_review_id = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)

    user = relationship('User', back_populates='review')
    book = relationship('Book', back_populates='in_review')







