from flask import Flask

from config import settings
from db.database import init_db
from scripts.init_data import init_books_data
from routes import main_blueprint, login_manager

app = Flask(__name__)
app.config['SECRET_KEY'] = settings.SECRET_KEY

login_manager.init_app(app)

app.register_blueprint(main_blueprint)

if __name__ == '__main__':
    init_db()
    init_books_data()
    app.run(port=settings.APP_PORT, debug=settings.DEBUG)
