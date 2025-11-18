import json
from db.database import session_scope
from db.models import Book


def init_books_data():
    with open('scripts/books.json', 'r', encoding='utf-8') as f:
        books = json.load(f)

    with session_scope() as session:
        for book in books:
            in_base = session.query(Book).filter(
                Book.title == book['title'],
                Book.author == book['author']
            ).first()

            if not in_base:
                new_book = Book(
                    title=book['title'],
                    author=book['author'],
                    price=book['price'],
                    genre=book['genre'],
                    cover=book['cover'],
                    description=book['description'],
                    rating=book['rating'],
                    year=book['year'],
                    category=book['category'],
                    subcategory=book['subcategory']
                )

                session.add(new_book)