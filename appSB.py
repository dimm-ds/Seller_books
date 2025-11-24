from flask import Flask
from flask_login import LoginManager
from sqlalchemy import inspect

from config import settings
from db.models import User
from db.database import init_db, engine
from scripts.init_data import init_books_data
from routes import main_blueprint
from db.database import session_scope

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY

login_manager = LoginManager(app)
login_manager.login_view = 'main.login'


@login_manager.user_loader
def load_user(user_id):
    with session_scope() as session:
        user = session.query(User).get(user_id)
        if user:
            session.expunge(user)

        return user


app.register_blueprint(main_blueprint)


def check_and_init_db():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    if not existing_tables:
        init_db()
        init_books_data()


if __name__ == '__main__':
    check_and_init_db()  # ← Только при первом запуске
    app.run(port=settings.APP_PORT, debug=settings.DEBUG)
