import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Book, Reader, BorrowedBook

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_register_user():
    response = client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data

def test_login_user():
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_create_book():
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/books/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Book",
            "author": "Test Author",
            "publication_year": 2024,
            "isbn": "1234567890",
            "copies_available": 1
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"

def test_borrow_book():
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    book_response = client.post(
        "/books/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Book",
            "author": "Test Author",
            "copies_available": 1
        }
    )
    book_id = book_response.json()["id"]
    
    reader_response = client.post(
        "/readers/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Reader",
            "email": "reader@example.com"
        }
    )
    reader_id = reader_response.json()["id"]
    
    borrow_response = client.post(
        "/borrow/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "book_id": book_id,
            "reader_id": reader_id
        }
    )
    assert borrow_response.status_code == 200
    data = borrow_response.json()
    assert data["book_id"] == book_id
    assert data["reader_id"] == reader_id

def test_max_books_limit():
    client.post(
        "/register",
        json={"email": "test@example.com", "password": "testpassword"}
    )
    login_response = client.post(
        "/token",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    token = login_response.json()["access_token"]
    
    reader_response = client.post(
        "/readers/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Test Reader",
            "email": "reader@example.com"
        }
    )
    reader_id = reader_response.json()["id"]
    
    for i in range(3):
        book_response = client.post(
            "/books/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": f"Test Book {i}",
                "author": "Test Author",
                "copies_available": 1
            }
        )
        book_id = book_response.json()["id"]
        client.post(
            "/borrow/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "book_id": book_id,
                "reader_id": reader_id
            }
        )
    
    book_response = client.post(
        "/books/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test Book 4",
            "author": "Test Author",
            "copies_available": 1
        }
    )
    book_id = book_response.json()["id"]
    
    response = client.post(
        "/borrow/",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "book_id": book_id,
            "reader_id": reader_id
        }
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Reader has reached maximum number of borrowed books" 