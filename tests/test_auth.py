"""
Unit tests for CricNova authentication: password hashing, validation, registration, and login.
"""

import pytest
from src.database import init_db, get_user_by_email
from src.auth import (
    hash_password,
    verify_password,
    authenticate_user,
    register_user,
    DEMO_EMAIL,
    DEMO_PASSWORD
)


def test_password_hashing():
    pwd = "secret_password_123"
    pwd_hash, salt = hash_password(pwd)
    assert pwd_hash is not None
    assert len(salt) > 0
    assert verify_password(pwd, salt, pwd_hash) is True
    assert verify_password("wrong_password", salt, pwd_hash) is False


def test_demo_user_authentication():
    init_db()
    success, msg, user = authenticate_user(DEMO_EMAIL, DEMO_PASSWORD)
    assert success is True
    assert user is not None
    assert user["email"] == DEMO_EMAIL


def test_failed_authentication():
    init_db()
    # Wrong password
    success, msg, user = authenticate_user(DEMO_EMAIL, "wrong_password_999")
    assert success is False
    assert user is None
    assert "Incorrect password" in msg

    # Non-existent user
    success, msg, user = authenticate_user("nonexistent_user_9999@test.com", "any_password")
    assert success is False
    assert user is None
    assert "No account found" in msg


def test_user_registration_and_validation():
    init_db()
    import time
    unique_email = f"test_user_{int(time.time())}@cricnova.ai"

    # Test password mismatch
    success, msg, _ = register_user("Test User", unique_email, "password123", "password456")
    assert success is False
    assert "do not match" in msg

    # Test short password
    success, msg, _ = register_user("Test User", unique_email, "123", "123")
    assert success is False
    assert "at least 6 characters" in msg

    # Test invalid email
    success, msg, _ = register_user("Test User", "not-an-email", "password123", "password123")
    assert success is False
    assert "valid email" in msg

    # Test valid registration
    success, msg, new_user = register_user("Valid User", unique_email, "validpass123", "validpass123")
    assert success is True
    assert new_user is not None
    assert new_user["email"] == unique_email

    # Test duplicate registration
    dup_success, dup_msg, _ = register_user("Valid User", unique_email, "validpass123", "validpass123")
    assert dup_success is False
    assert "already exists" in dup_msg

    # Test authenticating with newly registered user
    login_success, _, user_obj = authenticate_user(unique_email, "validpass123")
    assert login_success is True
    assert user_obj["name"] == "Valid User"
