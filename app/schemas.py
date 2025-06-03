from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

class BookBase(BaseModel):
    title: str
    author: str
    copies_available: int = 1

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ReaderBase(BaseModel):
    name: str
    email: EmailStr

class ReaderCreate(ReaderBase):
    pass

class Reader(ReaderBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class BorrowedBookBase(BaseModel):
    book_id: int
    reader_id: int

class BorrowedBookCreate(BorrowedBookBase):
    pass

class BorrowedBook(BorrowedBookBase):
    id: int
    borrow_date: datetime
    return_date: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True) 