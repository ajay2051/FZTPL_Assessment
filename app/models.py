import datetime

from sqlalchemy import Column, Integer, String, BigInteger, TIMESTAMP, func, DateTime

from app.db_connection import Base
from app.enums import UserRole


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone_number = Column(BigInteger, unique=True)
    address = Column(String)
    role = Column(String, default=UserRole.USER.value)
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"{self.email}"


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    blacklisted_on = Column(DateTime, default=datetime.datetime.utcnow)
