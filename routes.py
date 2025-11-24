import json
from datetime import date, timedelta
from flask import Blueprint, flash, redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user, current_user
from flask_wtf import FlaskForm
from sqlalchemy import func
from wtforms import TextAreaField, PasswordField, StringField, SelectField, BooleanField, SubmitField
from wtforms.validators import Optional, Email, EqualTo, InputRequired, Length, Regexp, DataRequired
from werkzeug.security import generate_password_hash, check_password_hash

from db.database import session_scope
from db.models import User, Order, OrderItem, Book, CartItem, Review

main_blueprint = Blueprint("main", __name__)


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username", validators=[InputRequired(), Length(max=100, min=4)]
    )
    user_phone = StringField('Номер телефона', validators=[
        DataRequired(message='Обязательное поле'),
        Regexp(r'^\+?[1-9]\d{1,14}$', message='Введите корректный номер телефона')
    ])
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=36)]
    )
    confirm_password = PasswordField(
        "Confirm Password", validators=[InputRequired(), EqualTo("password")]
    )


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email()])
    password = PasswordField(
        "Password", validators=[InputRequired(), Length(min=8, max=36)]
    )


class OrderForm(FlaskForm):

    payment_method = SelectField('Способ оплаты', choices=[
        ('card', 'Банковской картой'),
        ('cash', 'Наличными'),
        ('ewallet', 'Электронные кошельки'),
        ('bank_transfer', 'Безналичный расчет')
    ], validators=[DataRequired(message='Выберите способ оплаты')])

    delivery_method = SelectField('Способ доставки', choices=[
        ('courier', 'Курьерская доставка'),
        ('pickup', 'Самовывоз'),
        ('post', 'Почта России'),
        ('transport', 'Транспортные компании')
    ], validators=[DataRequired(message='Выберите способ доставки')])

    address = TextAreaField('Адрес доставки', validators=[
        Optional(),
        Length(max=500, message='Адрес не должен превышать 500 символов')
    ], render_kw={"rows": 3, "placeholder": "Укажите адрес для доставки..."})

    cash_on_delivery = BooleanField('Оплата при получении')

    full_name = StringField('Фамилия Имя', validators=[
        DataRequired(message='Обязательное поле'),
        Length(min=2, max=100, message='ФИО должно быть от 2 до 100 символов')
    ])

    submit = SubmitField('Подтвердить и оформить заказ')


@main_blueprint.route("/")
def home():
    with session_scope() as session:
        week_ago = date.today() - timedelta(days=7)
        top_books = session.query(Book, func.sum(OrderItem.book_count).label('total_sold')) \
            .join(OrderItem, Book.id == OrderItem.book_id) \
            .join(Order, OrderItem.order_id == Order.id) \
            .filter(Order.date >= week_ago) \
            .group_by(Book.id) \
            .order_by(func.sum(OrderItem.book_count).desc()) \
            .limit(3).all()

        books_data = []
        for book, total_sold in top_books:
            books_data.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'price': book.price,
                'cover': book.cover,
                'rating': book.rating,
                'rating_count': book.rating_count,
                'genre': book.genre,
                'description': book.description,
                'year': book.year,
                'total_sold': total_sold
            })
    return render_template("home.html", top_books=books_data)


@main_blueprint.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        with session_scope() as session:
            user = session.query(User).filter_by(username=form.username.data).first()
        if user:
            flash("User with this name already exists!", 'danger')
            return redirect(url_for("main.register", form=form))

        with session_scope() as session:
            user = session.query(User).filter_by(email=form.email.data).first()
        if user:
            flash("User with this email already exists!", 'danger')
            return redirect(url_for("main.register", form=form))

        new_user = User(
            username=form.username.data,
            user_phone=form.user_phone.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data)
        )
        with session_scope() as session:
            session.add(new_user)
        flash("Account has been created successfully!", 'success')
        return redirect(url_for("main.login"))
    elif form.errors:
        flash(form.errors, category='danger')

    return render_template("register.html", form=form)


@main_blueprint.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        with session_scope() as session:
            user = session.query(User).filter_by(email=form.email.data).first()
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                return redirect(url_for('main.home'))
        flash('Login failed', 'danger')
    elif request.method == 'POST':
        flash('Login failed', 'danger')
    return render_template('login.html', form=form)


@main_blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@main_blueprint.route('/catalog')
def catalog():
    category = request.args.get('category')
    subcategory = request.args.get('subcategory')

    with session_scope() as session:
        if category:
            books = session.query(Book).filter_by(category=category).all()
        elif subcategory:
            books = session.query(Book).filter_by(subcategory=subcategory).all()
        else:
            books = session.query(Book).all()

        books_data = []
        for book in books:
            books_data.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'genre': book.genre,
                'rating': book.rating,
                'rating_count': book.rating_count,
                'year': book.year,
                'price': book.price,
                'cover': book.cover,
                'description': book.description
            })

        return render_template('catalog.html', books=books_data, )


@main_blueprint.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    with session_scope() as session:
        cart_items_result = session.query(CartItem, Book).join(Book, CartItem.book_id == Book.id) \
            .filter(CartItem.user_id == current_user.id).all()

        cart_data = []
        for cart_items, books in cart_items_result:
            cart_data.append({
                'cart_item': {
                    'user_id': cart_items.user_id,
                    'book_id': cart_items.book_id,
                    'count': cart_items.count
                },
                'book': {
                    'id': books.id,
                    'title': books.title,
                    'author': books.author,
                    'price': books.price,
                    'genre': books.genre,
                    'cover': books.cover,
                    'description': books.description,
                    'rating': books.rating,
                    'rating_count': books.rating_count,
                    'year': books.year,
                    'category': books.category,
                    'subcategory': books.subcategory
                }
            })

    return render_template('cart.html', cart_items=cart_data)


@main_blueprint.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    book_id = request.form.get('book_id')
    with session_scope() as session:
        item = session.query(CartItem).filter(CartItem.book_id == book_id,
                                              CartItem.user_id == current_user.id).first()
        if not item:
            new_item = CartItem(
                user_id=current_user.id,
                book_id=book_id,
                count=1
            )
            session.add(new_item)
        else:
            item.count += 1

    return redirect(request.referrer or url_for('main.catalog'))


@main_blueprint.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    book_id = request.form.get('book_id')
    with session_scope() as session:
        item = session.query(CartItem).filter(CartItem.book_id == book_id,
                                              CartItem.user_id == current_user.id).first()
        session.delete(item)

    return redirect(request.referrer or url_for('main.cart'))


@main_blueprint.route('/decrease_from_cart', methods=['POST'])
@login_required
def decrease_from_cart():
    book_id = request.form.get('book_id')
    with session_scope() as session:
        item = session.query(CartItem).filter(CartItem.book_id == book_id,
                                              CartItem.user_id == current_user.id).first()
        if item.count > 1:
            item.count -= 1
        else:
            session.delete(item)

    return redirect(request.referrer or url_for('main.cart'))


@main_blueprint.route('/making_an_order', methods=['GET', 'POST'])
@login_required
def making_an_order():
    with session_scope() as session:
        cart_items_result = session.query(CartItem, Book).join(Book, CartItem.book_id == Book.id) \
            .filter(CartItem.user_id == current_user.id).all()

        if not cart_items_result:
            flash('Ваша корзина пуста', 'warning')
            return redirect(url_for('main.cart'))

        cart_data = []
        total_price = 0
        for cart_items, books in cart_items_result:
            item_data = {
                'cart_item': {
                    'count': cart_items.count,
                    'book_id': cart_items.book_id
                },
                'book': {
                    'id': books.id,
                    'title': books.title,
                    'price': books.price,
                    'author': books.author,
                    'cover': books.cover
                }
            }
            cart_data.append(item_data)
            total_price += cart_items.count * books.price

    delivery_date = date.today() + timedelta(days=3)
    formatted_delivery_date = delivery_date.strftime('%d.%m.%Y')

    form = OrderForm()

    if form.validate_on_submit():
        with session_scope() as session:
            delivery_address = form.address.data if form.delivery_method.data != 'pickup' else 'Самовывоз'
            new_order = Order(
                user_id=current_user.id,
                date=date.today(),
                status='Оформлен',
                total_amount=total_price,
                address=delivery_address,
                payment_method=form.payment_method.data,
                delivery_method=form.delivery_method.data,
                customer_name=form.full_name.data,
                cash_on_delivery=form.cash_on_delivery.data,
                delivery_date=formatted_delivery_date
            )
            session.add(new_order)
            session.flush()

            new_order_id = new_order.id
            for item in cart_data:
                order_item = OrderItem(
                    order_id=new_order_id,
                    book_id=item['book']['id'],
                    book_count=item['cart_item']['count'],
                    cost=item['cart_item']['count'] * item['book']['price']
                )
                session.add(order_item)

            session.query(CartItem).filter(CartItem.user_id == current_user.id).delete()

        flash('Заказ успешно оформлен!', 'success')
        return redirect(url_for('main.orders'))

    return render_template('making_an_order.html',
                           form=form,
                           total_price=total_price,
                           delivery_date=formatted_delivery_date,
                           cart_items=cart_data)


@main_blueprint.route('/orders', methods=['GET'])
@login_required
def orders():
    with session_scope() as session:
        orders = session.query(Order).filter_by(user_id=current_user.id).all()
        orders_data = []
        for order in orders:
            orders_data.append({
                'id': order.id,
                'date': order.delivery_date,
                'status': order.status,
                'total_amount': order.total_amount,
                'book_list': order.book_list,
                'total_books': len(order.book_list)
            })
        return render_template('orders.html', orders_data=orders_data)


@main_blueprint.route('/order_items', methods=['POST'])
@login_required
def order_items():
    book_list_json = request.form.get('book_list')
    book_list = json.loads(book_list_json)
    with session_scope() as session:
        books = session.query(Book).filter(Book.id.in_(book_list)).all()
        books_data = []
        for book in books:
            books_data.append({
                'id': book.id,
                'title': book.title,
                'author': book.author,
                'cover': book.cover,
                'rating': book.rating,
                'rating_count': book.rating_count,
                'genre': book.genre,
                'description': book.description,
                'year': book.year
            })
        return render_template('order_items.html', books_data=books_data)


@main_blueprint.route('/submit_review', methods=['POST'])
@login_required
def submit_review():
    book_id = request.form.get('book_id')
    rating = request.form.get('rating')
    review_text = request.form.get('review_text', '')
    with session_scope() as session:
        new_review = Review(
            review=review_text,
            user_id=current_user.id,
            book_id=book_id
        )
        session.add(new_review)

        book = session.query(Book).filter_by(id=book_id).first()
        if not book.rating:
            book.rating = int(rating)
            book.rating_count = 1
        else:
            book.rating = (book.rating + int(rating)) / (book.rating_count + 1)
            book.rating_count += 1

    return redirect(url_for('main.orders'))
