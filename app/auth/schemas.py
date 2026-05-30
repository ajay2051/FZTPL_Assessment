from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, constr, field_validator

from app.custom_exceptions import PasswordDidNotMatch
from app.enums import UserRole


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    role: str = UserRole.USER.value
    phone_number: int
    address: constr(max_length=100)

    @field_validator('first_name')
    def validate_first_name(cls, v):
        first_name_str = str(v)
        if len(first_name_str) < 3 or len(first_name_str) > 15:
            raise ValueError('First name must be between 3 and 10 characters')
        return v

    @field_validator('last_name')
    def validate_last_name(cls, v):
        last_name_str = str(v)
        if len(last_name_str) < 3 or len(last_name_str) > 15:
            raise ValueError('Last name must be between 3 and 10 characters')
        return v

    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        phone_str = str(v)
        if not (8 <= len(phone_str) <= 15):
            raise ValueError('Phone number must be between 8 and 15 digits')
        return v

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: constr(max_length=15)

    @field_validator('password')
    def password_must_contain_uppercase_and_symbol(cls, v):
        if len(v) > 15:
            raise ValueError('Password must be 15 characters or less 👎👿⛔')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter 👎👿⛔')
        if not any(char in r'!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError('Password must contain at least one symbol 👎👿⛔')
        return v

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateUserResponseMessage(BaseModel):
    message: str = "Account Created Successfully...!👍👍"
    user: UserResponse


class EmailSchema(BaseModel):
    addresses: List[str]


class Token(BaseModel):
    first_name: str
    last_name: str
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    email: str
    user_role: str


class LoginData(BaseModel):
    email: str
    password: str


class TokenData(BaseModel):
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class PasswordResetRequestModel(BaseModel):
    email: str


class PasswordResetConfirmModel(BaseModel):
    current_password: constr(max_length=15)
    new_password: constr(max_length=15)
    confirm_password: constr(max_length=15)

    @field_validator('new_password')
    def password_validator(cls, password: str) -> str:
        if len(password) > 15:
            raise ValueError('Password must be 15 characters or less 👎👿⛔')
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter 👎👿⛔')
        if not any(char in r'!@#$%^&*(),.?":{}|<>' for char in password):
            raise ValueError('Password must contain at least one symbol 👎👿⛔')
        return password

    @field_validator('confirm_password')
    def passwords_match(cls, confirm_password: str, values: dict) -> str:
        if 'new_password' in values.data and confirm_password != values.data['new_password']:
            raise ValueError('Passwords do not match 👎👿⛔')
        return confirm_password

    @field_validator('new_password')
    def new_password_different(cls, new_password: str, values: dict) -> str:
        if 'current_password' in values.data and new_password == values.data['current_password']:
            raise ValueError('New password must be different from current password 👎👿⛔')
        return new_password


class ForgotPasswordRequestModel(BaseModel):
    email: str


class ForgotPasswordConfirmModel(BaseModel):
    new_password: constr(max_length=15)
    confirm_password: constr(max_length=15)

    @classmethod
    def password_validator(cls, password: str) -> str:
        if len(password) > 15:
            raise ValueError('Password must be 15 characters or less 👎👿⛔')
        if not any(char.isupper() for char in password):
            raise ValueError('Password must contain at least one uppercase letter 👎👿⛔')
        if not any(char in r'!@#$%^&*(),.?":{}|<>' for char in password):
            raise ValueError('Password must contain at least one symbol 👎👿⛔')
        return password

    def validate_passwords_match(self):
        if self.new_password != self.confirm_password:
            raise PasswordDidNotMatch
