from fastapi import Depends
from sqlalchemy.orm import Session
from core.database import get_db


def get_current_user():
    """Placeholder for authentication"""
    return {"user_id": "demo_user", "role": "credit_officer"}


def require_auth(current_user: dict = Depends(get_current_user)):
    """Dependency for protected routes"""
    return current_user
