from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.auth import jwt_token, schemas


def get_user_by_id(db: Session, user_id):
    """
    Retrieve a user from the database by their ID.

    This function queries the database for a user with the specified ID
    and returns the user object if found, or None if no user exists with
    that ID.

    Args:
        db (Session): SQLAlchemy database session
        user_id: The unique identifier of the user to retrieve

    Returns:
        models.User: The user object if found, None otherwise

    """
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    """
        Retrieve a user from the database by their email address.

        This function queries the database for a user with the specified email
        address and returns the user object if found, or None if no user exists
        with that email. The email parameter is converted to string to ensure
        proper comparison.

        Args:
            db (Session): SQLAlchemy database session
            email (str): The email address of the user to retrieve

        Returns:
            models.User: The user object if found, None otherwise

    """
    return db.query(models.User).filter(models.User.email == str(email)).first()


def get_user_by_number(db: Session, phone_number: int):
    """
        Retrieve a user from the database by their phone number.

        This function queries the database for a user with the specified phone
        number and returns the user object if found, or None if no user exists
        with that phone number.

        Args:
            db (Session): SQLAlchemy database session
            phone_number (int): The phone number of the user to retrieve

        Returns:
            models.User: The user object if found, None otherwise

    """
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()


def create_user(db: Session, user: schemas.UserCreate):
    """
        Create a new user in the database.

        This function creates a new user record in the database using the provided
        user data. The password is hashed before storage for security. The user is
        initially set as not verified, and timestamps are set to the current UTC time.

        Args:
            db (Session): SQLAlchemy database session
            user (schemas.UserCreate): User data including first_name, last_name, email,
                                      password, phone_number, address, and role

        Returns:
            models.User: The newly created user object with database ID assigned

        Note:
            This function commits the transaction to the database.

    """
    hashed_password = jwt_token.get_password_hash(user.password)
    # db_user = User(**user.model_dump())
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed_password,
        phone_number=user.phone_number,
        address=user.address,
        role=user.role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def update_user(db: Session, user: models.User, user_data: dict):
    """
        Update an existing user's information in the database.

        This asynchronous function updates one or more attributes of an existing user
        record in the database based on the provided dictionary of field-value pairs.
        Common use cases include setting the is_verified flag to True after email
        verification or updating user profile information.

        Args:
            db (Session): SQLAlchemy database session
            user (models.User): The user object to update
            user_data (dict): Dictionary containing field names and their new values
                             e.g., {'is_verified': True, 'address': '123 New St'}

        Returns:
            models.User: The updated user object

        Note:
            This function commits the transaction to the database.

    """
    for key, value in user_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
