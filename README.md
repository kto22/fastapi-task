# Library Management System API

A RESTful API for managing a library catalog, built with FastAPI and SQLite.

## Features

- JWT-based authentication for librarians
- CRUD operations for books and readers
- Book borrowing and returning functionality
- Business logic enforcement (max books per reader, available copies)
- Database migrations with Alembic

## Requirements

- Python 3.8+
- FastAPI
- SQLAlchemy
- SQLite
- JWT for authentication
- Pydantic for data validation
- Alembic for database migrations
- Pytest for testing

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate d
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- Interactive API documentation (Swagger UI): `http://localhost:8000/docs`
- Alternative API documentation (ReDoc): `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- POST `/register` - Register a new librarian
- POST `/token` - Login and get JWT token

### Books (Protected)
- GET `/books/` - List all books
- POST `/books/` - Create a new book
- GET `/books/{book_id}` - Get book details
- PUT `/books/{book_id}` - Update a book
- DELETE `/books/{book_id}` - Delete a book

### Readers (Protected)
- GET `/readers/` - List all readers
- POST `/readers/` - Create a new reader
- GET `/readers/{reader_id}` - Get reader details
- PUT `/readers/{reader_id}` - Update a reader
- DELETE `/readers/{reader_id}` - Delete a reader

### Book Operations (Protected)
- POST `/borrow/` - Borrow a book
- POST `/return/{borrow_id}` - Return a book
- GET `/readers/{reader_id}/borrowed` - Get reader's borrowed books

## Business Rules

1. A reader cannot borrow more than 3 books at a time
2. A book can only be borrowed if copies are available
3. A book cannot be returned if it wasn't borrowed or was already returned
4. All operations (except registration and login) require JWT authentication

## Testing

Run the tests with:
```bash
pytest
```

## Database Migrations

The project uses Alembic for database migrations. The initial migration creates all necessary tables, and the second migration adds a description field to books.

To create a new migration:
```bash
alembic revision --autogenerate -m "description"
```

To apply migrations:
```bash
alembic upgrade head
```

To rollback migrations:
```bash
alembic downgrade -1
``` 