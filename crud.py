from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt, JWTError
from datetime import date

import models
import schemas

SECRET_KEY = "secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(email=user.email)
    db_user.set_password(user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not user.check_password(password):
        return False
    return user


def create_access_token(email: str):
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(email: str):
    payload = {
        "sub": email,
        "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise JWTError
        return email
    except JWTError:
        return None


def get_current_user(token: str = None, db: Session = None):
    if not token:
        return None
    email = verify_token(token)
    if not email:
        return None
    user = get_user_by_email(db, email)
    return user


def get_current_user_token(token: str = None):
    if not token:
        return None
    email = verify_token(token)
    if not email:
        return None
    access_token = create_access_token(email)
    return access_token


def get_user_contacts(db: Session, user_id: int):
    return db.query(models.Contact).filter(models.Contact.user_id == user_id).all()


def create_contact(db: Session, contact: schemas.ContactCreate):
    db_contact = models.Contact(
        name=contact.name,
        surname=contact.surname,
        email=contact.email,
        phone=contact.phone,
        birthday=contact.birthday,
        additional_data=contact.additional_data,
    )
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact


def get_contacts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Contact).offset(skip).limit(limit).all()


def get_contact(db: Session, contact_id: int):
    return db.query(models.Contact).get(contact_id)


def update_contact(
    db: Session, db_contact: models.Contact, contact: schemas.ContactUpdate
):
    for field in contact.dict(exclude_unset=True):
        setattr(db_contact, field, contact.dict()[field])
    db.commit()
    db.refresh(db_contact)
    return db_contact


def delete_contact(db: Session, db_contact: models.Contact):
    db.delete(db_contact)
    db.commit()
    return db_contact


def search_contacts(db: Session, query: str):
    return (
        db.query(models.Contact)
        .filter(
            models.Contact.name.ilike(f"%{query}%")
            | models.Contact.surname.ilike(f"%{query}%")
            | models.Contact.email.ilike(f"%{query}%")
        )
        .all()
    )


def birthday_contacts(db: Session):
    today = date.today()
    next_week = today.replace(day=today.day + 7)
    return (
        db.query(models.Contact)
        .filter(models.Contact.birthday >= today, models.Contact.birthday <= next_week)
        .all()
    )
