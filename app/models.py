from datetime import date
from enum import StrEnum

from sqlmodel import Field, SQLModel


class Status(StrEnum):
    applied = "applied"
    interviewing = "interviewing"
    offer = "offer"
    rejected = "rejected"
    ghosted = "ghosted"


class ApplicationBase(SQLModel):
    company: str = Field(min_length=1, max_length=100)
    role: str = Field(min_length=1, max_length=100)
    status: Status = Status.applied
    applied_on: date = Field(default_factory=date.today)
    follow_up_on: date | None = None
    url: str | None = None
    notes: str | None = None


class Application(ApplicationBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ApplicationCreate(ApplicationBase):
    pass


class ApplicationRead(ApplicationBase):
    id: int


class ApplicationUpdate(SQLModel):
    company: str | None = Field(default=None, min_length=1, max_length=100)
    role: str | None = Field(default=None, min_length=1, max_length=100)
    status: Status | None = None
    applied_on: date | None = None
    follow_up_on: date | None = None
    url: str | None = None
    notes: str | None = None

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    hashed_password: str


class UserCreate(SQLModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)


class UserRead(SQLModel):
    id: int
    username: str


class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"