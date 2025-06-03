from datetime import datetime, timedelta, UTC
from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Library Management System",
    description="A RESTful API for managing a library catalog",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Library Management System API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }

@app.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/books/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_book = models.Book(**book.model_dump())
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.get("/books/", response_model=List[schemas.Book])
def read_books(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    books = db.query(models.Book).offset(skip).limit(limit).all()
    return books

@app.get("/books/{book_id}", response_model=schemas.Book)
def read_book(book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@app.put("/books/{book_id}", response_model=schemas.Book)
def update_book(book_id: int, book: schemas.BookCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    for key, value in book.model_dump().items():
        setattr(db_book, key, value)
    db.commit()
    db.refresh(db_book)
    return db_book

@app.delete("/books/{book_id}")
def delete_book(book_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if db_book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    db.delete(db_book)
    db.commit()
    return {"message": "Book deleted successfully"}

@app.post("/readers/", response_model=schemas.Reader)
def create_reader(reader: schemas.ReaderCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_reader = db.query(models.Reader).filter(models.Reader.email == reader.email).first()
    if db_reader:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_reader = models.Reader(**reader.model_dump())
    db.add(db_reader)
    db.commit()
    db.refresh(db_reader)
    return db_reader

@app.get("/readers/", response_model=List[schemas.Reader])
def read_readers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    readers = db.query(models.Reader).offset(skip).limit(limit).all()
    return readers

@app.get("/readers/{reader_id}", response_model=schemas.Reader)
def read_reader(reader_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    reader = db.query(models.Reader).filter(models.Reader.id == reader_id).first()
    if reader is None:
        raise HTTPException(status_code=404, detail="Reader not found")
    return reader

@app.put("/readers/{reader_id}", response_model=schemas.Reader)
def update_reader(reader_id: int, reader: schemas.ReaderCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_reader = db.query(models.Reader).filter(models.Reader.id == reader_id).first()
    if db_reader is None:
        raise HTTPException(status_code=404, detail="Reader not found")
    for key, value in reader.model_dump().items():
        setattr(db_reader, key, value)
    db.commit()
    db.refresh(db_reader)
    return db_reader

@app.delete("/readers/{reader_id}")
def delete_reader(reader_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_reader = db.query(models.Reader).filter(models.Reader.id == reader_id).first()
    if db_reader is None:
        raise HTTPException(status_code=404, detail="Reader not found")
    db.delete(db_reader)
    db.commit()
    return {"message": "Reader deleted successfully"}

@app.post("/borrow/", response_model=schemas.BorrowedBook)
def borrow_book(borrow: schemas.BorrowedBookCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    book = db.query(models.Book).filter(models.Book.id == borrow.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if book.copies_available <= 0:
        raise HTTPException(status_code=400, detail="No copies available")
    
    active_borrows = db.query(models.BorrowedBook).filter(
        models.BorrowedBook.reader_id == borrow.reader_id,
        models.BorrowedBook.return_date == None
    ).count()
    if active_borrows >= 3:
        raise HTTPException(status_code=400, detail="Reader has reached maximum number of borrowed books")
    
    book.copies_available -= 1
    db_borrow = models.BorrowedBook(
        **borrow.model_dump(),
        borrow_date=datetime.now(UTC)
    )
    db.add(db_borrow)
    db.commit()
    db.refresh(db_borrow)
    return db_borrow

@app.post("/return/{borrow_id}")
def return_book(borrow_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    db_borrow = db.query(models.BorrowedBook).filter(models.BorrowedBook.id == borrow_id).first()
    if not db_borrow:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    if db_borrow.return_date:
        raise HTTPException(status_code=400, detail="Book already returned")
    
    book = db.query(models.Book).filter(models.Book.id == db_borrow.book_id).first()
    book.copies_available += 1
    db_borrow.return_date = datetime.now(UTC)
    db.commit()
    return {"message": "Book returned successfully"}

@app.get("/readers/{reader_id}/borrowed", response_model=List[schemas.BorrowedBook])
def get_reader_borrowed_books(reader_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(auth.get_current_user)):
    borrowed_books = db.query(models.BorrowedBook).filter(
        models.BorrowedBook.reader_id == reader_id,
        models.BorrowedBook.return_date == None
    ).all()
    return borrowed_books 