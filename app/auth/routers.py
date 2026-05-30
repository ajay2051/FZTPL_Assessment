import os
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models
from app.auth import jwt_token, schemas
from app.auth.dependencies import AllowedUsers
from app.auth.get_create_user import create_user, get_user_by_email, get_user_by_number
from app.auth.jwt_token import blacklist_token
from app.auth.schemas import CreateUserResponseMessage, LoginData
from app.custom_exceptions import IncorrectEmailPassword, UserAlreadyExists, UserNotFound
from app.db_connection import get_db
from app.enums import UserRole

auth_router = APIRouter(tags=["auth"])

UI_DOMAIN = os.environ.get('UI_DOMAIN')
ui_redirect_link = f"https://{UI_DOMAIN}/login"


@auth_router.post("/create_users/", response_model=schemas.CreateUserResponseMessage)
async def create_users(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account and send a verification email.

    This endpoint creates a new user in the system and sends a verification
    email to the provided email address. The user will need to verify their
    account by clicking the link in the email before they can log in.

    Args:
        user: User data including email, password, address, phone_number, and role
        db: Database session dependency

    Returns:
        CreateUserResponseMessage: Object containing the newly created user information

    Raises:
        UserAlreadyExists: If a user with the provided email or phone number already exists
    """
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise UserAlreadyExists
    user_by_number = get_user_by_number(db, user.phone_number)
    if user_by_number:
        raise UserAlreadyExists
    new_user = create_user(db, user)

    return CreateUserResponseMessage(user=new_user)


@auth_router.post('/create_admin_users/', response_model=schemas.CreateUserResponseMessage)
def create_admin_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new admin user account and send a verification email.

    This endpoint creates a new user with admin privileges and sends a verification
    email to the provided email address. The admin role is automatically assigned
    regardless of what role was provided in the request.

    Args:
        user: User data including email, password, address, phone_number
        db: Database session dependency

    Returns:
        CreateUserResponseMessage: Object containing the newly created admin user information

    Raises:
        UserAlreadyExists: If a user with the provided email already exists
    """
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise UserAlreadyExists
    user.role = UserRole.ADMIN.value
    new_admin_user = create_user(db, user)
    return CreateUserResponseMessage(user=new_admin_user)


@auth_router.post("/token/refresh/", response_model=schemas.TokenResponse)
async def refresh_access_token(token: str, db: Session = Depends(get_db)):
    """
    Generate a new access token using a valid refresh token.

    This endpoint allows users to obtain a new access token without
    having to log in again by providing a valid refresh token.

    Args:
        token: The refresh token string
        db: Database session dependency

    Returns:
        TokenResponse: Object containing the new access token, refresh token, and token type

    Raises:
        UserNotFound: If the user associated with the token doesn't exist
        HTTPException: If the refresh token is invalid or expired
    """
    token_data = jwt_token.verify_refresh_token(token)
    user = get_user_by_email(db, token_data.get('email'))
    if not user:
        raise UserNotFound
    access_token_expires = timedelta(minutes=jwt_token.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt_token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = jwt_token.create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "Bearer"}


@auth_router.post("/token/", response_model=schemas.Token)
async def login_for_access_token(form_data: LoginData, db: Session = Depends(get_db)):
    """
    Authenticate a user and generate access and refresh tokens.

    This endpoint verifies the user's credentials and, if valid, provides
    access and refresh tokens for authenticated API access. The user must
    have a verified account to log in.

    Args:
        form_data: User credentials containing email and password
        db: Database session dependency

    Returns:
        Token: Object containing access token, refresh token, token type, user ID, email, and role

    Raises:
        UserNotFound: If the user with the provided email doesn't exist
        UserNotVerified: If the user account has not been verified
        IncorrectEmailPassword: If the provided password is incorrect
    """
    email_user = get_user_by_email(db, form_data.email)
    if not email_user:
        raise UserNotFound
    user = jwt_token.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise IncorrectEmailPassword
    access_token_expires = timedelta(minutes=jwt_token.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt_token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = jwt_token.create_refresh_token(data={"sub": user.email})
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer", "user_id": user.id, "email": user.email,
            "user_role": user.role, "first_name": user.first_name, "last_name": user.last_name}


@auth_router.get('/all_users/', response_model=List[schemas.UserResponse])
async def read_all_users(db: Session = Depends(get_db), _: bool = Depends(AllowedUsers(['admin']))):
    """
    Retrieve a list of all verified users in the system.

    This endpoint returns information about all verified users.
    Only users with admin role can access this endpoint.

    Args:
        db: Database session dependency
        _: Admin permission check dependency

    Returns:
        List[UserResponse]: List of objects containing user information

    Raises:
        UserNotFound: If no verified users exist in the system
    """
    all_users = db.query(models.User).all()
    if not all_users:
        raise UserNotFound
    return all_users


@auth_router.post("/logout/")
async def logout(current_user: schemas.UserResponse = Depends(jwt_token.get_current_user), token: str = Depends(jwt_token.oauth2_scheme),
                 db: Session = Depends(get_db)):
    """
        Log out the current user by blacklisting their access token.

        This endpoint invalidates the current access token by adding it to a blacklist,
        effectively logging the user out from the current session.

        Args:
            current_user: The authenticated user object from the token dependency
            token: The access token from the authorization header
            db: Database session dependency

        Returns:
            dict: Success message indicating the user was logged out
    """
    blacklist_token(db, token)
    return {"message": "Successfully logged out 👍🙂"}
