import streamlit as st
import hashlib
import random
import string
import os

def generate_salt():
    """Generate a random salt for password hashing"""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

def hash_password(password, salt):
    """Hash a password with a salt using SHA-256"""
    return hashlib.sha256((password + salt).encode()).hexdigest()

def verify_password(password, salt, password_hash):
    """Verify a password against its hash"""
    return hash_password(password, salt) == password_hash

def init_auth_state():
    """Initialize authentication state variables in session state"""
    if 'is_authenticated' not in st.session_state:
        st.session_state.is_authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

def register_user(username, password, email=None):
    """Register a new user"""
    salt = generate_salt()
    password_hash = hash_password(password, salt)
    
    # Store user information in session state for demo purposes
    # In a real app, you would save this to a database
    st.session_state.registered_users = st.session_state.get('registered_users', {})
    
    # Check if username already exists
    if username in st.session_state.registered_users:
        return False, "Username already exists"
    
    # Add user to the session state
    st.session_state.registered_users[username] = {
        'salt': salt,
        'password_hash': password_hash,
        'email': email,
        'user_id': len(st.session_state.registered_users) + 1
    }
    
    return True, "Registration successful"

def login_user(username, password):
    """Log in a user"""
    # In a real app, you would validate against a database
    st.session_state.registered_users = st.session_state.get('registered_users', {})
    
    # Create default user if no users exist
    if not st.session_state.registered_users:
        create_default_user()
    
    if username not in st.session_state.registered_users:
        return False, "Invalid username or password"
    
    user_info = st.session_state.registered_users[username]
    if verify_password(password, user_info['salt'], user_info['password_hash']):
        st.session_state.is_authenticated = True
        st.session_state.username = username
        st.session_state.user_id = user_info.get('user_id', 1)
        return True, "Login successful"
    else:
        return False, "Invalid username or password"

def logout_user():
    """Log out a user"""
    st.session_state.is_authenticated = False
    st.session_state.username = None
    st.session_state.user_id = None

def create_default_user():
    """Create a default user for demo purposes"""
    if 'registered_users' not in st.session_state:
        st.session_state.registered_users = {}
    
    if 'demo' not in st.session_state.registered_users:
        salt = generate_salt()
        password_hash = hash_password('demo', salt)
        st.session_state.registered_users['demo'] = {
            'salt': salt,
            'password_hash': password_hash,
            'email': 'demo@example.com',
            'user_id': 1
        }

def require_auth():
    """Require authentication to access a page"""
    if not st.session_state.get('is_authenticated', False):
        st.warning("Please log in to access this page")
        st.stop()

def auth_sidebar():
    """Display authentication sidebar"""
    if st.session_state.is_authenticated:
        st.markdown(f"""
        <div style="padding: 0.5rem; border-radius: 0.5rem; background-color: #F0F7FF; margin-bottom: 1rem;">
            <p style="margin: 0; font-size: 0.9rem;">
                <span style="font-weight: bold;">👤 {st.session_state.username}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔓 Log Out"):
            logout_user()
            st.experimental_rerun()
    else:
        auth_tab = st.radio("Authentication", ["Login", "Register"], horizontal=True)
        
        if auth_tab == "Login":
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("🔐 Log In"):
                if username and password:
                    success, message = login_user(username, password)
                    if success:
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter username and password")
        else:  # Register
            username = st.text_input("Choose Username", key="register_username")
            password = st.text_input("Choose Password", type="password", key="register_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            email = st.text_input("Email (optional)", key="register_email")
            
            if st.button("📝 Register"):
                if username and password:
                    if password != confirm_password:
                        st.error("Passwords do not match")
                    else:
                        success, message = register_user(username, password, email)
                        if success:
                            st.success(message)
                            # Auto login after registration
                            login_user(username, password)
                            st.experimental_rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Please enter username and password")