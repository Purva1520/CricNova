"""
Authentication and User Session Management for CricNova.
Supports SQLite-backed user registration, salted SHA-256 password hashing,
field validation, demo analyst login, and persistent session state.
"""

import hashlib
import os
import re
from datetime import datetime
import streamlit as st
from src.database import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id
)

DEMO_EMAIL = "analyst@cricnova.ai"
DEMO_PASSWORD = "cricnova123"
DEMO_NAME = "Lead IPL Analyst"


def hash_password(password: str, salt: str = None) -> tuple[str, str]:
    """Generates a salted SHA-256 hash for a given password."""
    if salt is None:
        salt = os.urandom(16).hex()
    salted = f"{salt}:{password}".encode("utf-8")
    pwd_hash = hashlib.sha256(salted).hexdigest()
    return pwd_hash, salt


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    """Verifies a plaintext password against stored salt and hash."""
    computed_hash, _ = hash_password(password, salt)
    return computed_hash == password_hash


def ensure_demo_user():
    """Ensures the standard demo analyst account exists in the database."""
    init_db()
    existing = get_user_by_email(DEMO_EMAIL)
    if not existing:
        pwd_hash, salt = hash_password(DEMO_PASSWORD)
        create_user(
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            password_hash=pwd_hash,
            salt=salt,
            role="lead_analyst"
        )


def validate_email_format(email: str) -> bool:
    """Validates email format using standard regex."""
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return bool(re.match(pattern, email.strip()))


def authenticate_user(email: str, password: str) -> tuple[bool, str, dict | None]:
    """
    Validates user credentials against SQLite database.
    Returns: (success: bool, message: str, user_dict: dict or None)
    """
    ensure_demo_user()
    if not email or not email.strip():
        return False, "Please enter your email address.", None
    if not password:
        return False, "Please enter your password.", None

    user = get_user_by_email(email.strip())
    if not user:
        return False, "No account found with this email. Please check your spelling or sign up.", None

    if not verify_password(password, user["salt"], user["password_hash"]):
        return False, "Incorrect password. Please try again.", None

    safe_user = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "analyst"),
        "created_at": user.get("created_at")
    }
    return True, "Login successful! Welcome to CricNova.", safe_user


def register_user(name: str, email: str, password: str, confirm_password: str) -> tuple[bool, str, dict | None]:
    """
    Registers a new user after comprehensive validation.
    Returns: (success: bool, message: str, user_dict: dict or None)
    """
    init_db()
    name = name.strip()
    email = email.strip().lower()

    if not name or len(name) < 2:
        return False, "Please provide your full name (minimum 2 characters).", None

    if not email or not validate_email_format(email):
        return False, "Please provide a valid email address (e.g. user@domain.com).", None

    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long.", None

    if password != confirm_password:
        return False, "Passwords do not match. Please re-enter identical passwords.", None

    existing = get_user_by_email(email)
    if existing:
        return False, f"An account with email '{email}' already exists. Please sign in instead.", None

    pwd_hash, salt = hash_password(password)
    user_id = create_user(name=name, email=email, password_hash=pwd_hash, salt=salt, role="analyst")

    new_user = {
        "id": user_id,
        "name": name,
        "email": email,
        "role": "analyst",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return True, "Account created successfully! Welcome aboard.", new_user


def is_authenticated() -> bool:
    """Checks if the user has an active authenticated session."""
    return bool(st.session_state.get("authenticated", False) and st.session_state.get("current_user"))


def get_current_user() -> dict | None:
    """Returns the current logged-in user dict from session state."""
    return st.session_state.get("current_user")


def login_session(user_dict: dict):
    """Sets session state to logged-in for the given user."""
    st.session_state["authenticated"] = True
    st.session_state["current_user"] = user_dict


def logout_user():
    """Clears user session and logs out."""
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None
    st.rerun()


def render_sidebar_user_profile():
    """Renders active user identity badge and logout button in Streamlit sidebar."""
    user = get_current_user()
    if not user:
        return

    st.sidebar.markdown(
        f"""
        <div style="background: rgba(19, 27, 46, 0.9); border: 1px solid #212e4d; border-radius: 10px; padding: 12px; margin-bottom: 14px;">
            <div style="display: flex; align-items: center;">
                <div style="width: 38px; height: 38px; border-radius: 50%; background: linear-gradient(135deg, #00f2fe 0%, #0284c7 100%); display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 1.1rem; color: #0b0f19; margin-right: 10px;">
                    {user['name'][0].upper()}
                </div>
                <div style="overflow: hidden;">
                    <div style="color: #f8fafc; font-weight: 700; font-size: 0.95rem; white-space: nowrap; text-overflow: ellipsis; overflow: hidden;">{user['name']}</div>
                    <div style="color: #00f2fe; font-size: 0.76rem; font-weight: 600;">ACTIVE ANALYST</div>
                </div>
            </div>
            <div style="color: #64748b; font-size: 0.75rem; margin-top: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                {user['email']}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.sidebar.button("🚪 Sign Out", key="sidebar_btn_logout", use_container_width=True):
        logout_user()


def render_auth_screen():
    """
    Renders a premier dark stadium Login / Signup authentication portal.
    Fully validates inputs, provides instant error feedback, and persists sessions.
    """
    ensure_demo_user()

    col_pad_l, col_center, col_pad_r = st.columns([1, 2, 1])

    with col_center:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="font-size: 3.2rem; filter: drop-shadow(0 0 16px rgba(0, 242, 254, 0.7));">⚡🏏</div>
                <h1 style="margin: 8px 0 4px 0; font-weight: 800; font-size: 2.2rem; letter-spacing: -0.02em; color: #f8fafc;">
                    CRIC<span style="color: #00f2fe;">NOVA</span>
                </h1>
                <p style="color: #94a3b8; font-size: 1rem; margin: 0;">IPL AI Prediction & Analytics Suite</p>
                <div style="margin-top: 10px;">
                    <span class="metric-pill" style="color: #10b981; border-color: #10b981;">SECURE AUTHENTICATION GATE</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Create Account"])

        # ======================================================================
        # TAB 1: SIGN IN
        # ======================================================================
        with auth_tab1:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            with st.form("form_login"):
                st.markdown("#### Access Your Analyst Workspace")
                login_email = st.text_input("Email / Username", placeholder="e.g. analyst@cricnova.ai", key="input_login_email")
                login_password = st.text_input("Password", type="password", placeholder="••••••••", key="input_login_password")
                
                submitted = st.form_submit_button("🚀 Sign In to CricNova", use_container_width=True)

                if submitted:
                    with st.spinner("Authenticating credentials..."):
                        success, msg, user_obj = authenticate_user(login_email, login_password)
                        if success:
                            st.success(msg)
                            login_session(user_obj)
                            st.rerun()
                        else:
                            st.error(msg)

            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div style="text-align: center; color: #64748b; font-size: 0.85rem; margin-bottom: 8px;">
                    — OR USE PRE-CONFIGURED EVALUATION CREDENTIALS —
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button("⚡ One-Click Demo Analyst Login", key="btn_quick_demo_login", use_container_width=True):
                success, msg, user_obj = authenticate_user(DEMO_EMAIL, DEMO_PASSWORD)
                if success:
                    st.success("Signed in as Lead IPL Analyst!")
                    login_session(user_obj)
                    st.rerun()
                else:
                    st.error(msg)

        # ======================================================================
        # TAB 2: SIGN UP
        # ======================================================================
        with auth_tab2:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            with st.form("form_signup"):
                st.markdown("#### Register New Analyst Account")
                signup_name = st.text_input("Full Name", placeholder="e.g. Rahul Dravid", key="input_signup_name")
                signup_email = st.text_input("Email Address", placeholder="e.g. rahul@cricket.org", key="input_signup_email")
                signup_password = st.text_input("Create Password", type="password", placeholder="Min 6 characters", key="input_signup_password")
                signup_confirm = st.text_input("Confirm Password", type="password", placeholder="Repeat password", key="input_signup_confirm")

                registered = st.form_submit_button("✨ Create Analyst Account", use_container_width=True)

                if registered:
                    with st.spinner("Creating your analyst account..."):
                        success, msg, user_obj = register_user(
                            name=signup_name,
                            email=signup_email,
                            password=signup_password,
                            confirm_password=signup_confirm
                        )
                        if success:
                            st.success(msg)
                            login_session(user_obj)
                            st.rerun()
                        else:
                            st.error(msg)
