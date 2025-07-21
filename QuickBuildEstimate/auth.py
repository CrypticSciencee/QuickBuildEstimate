import os
from functools import wraps
from flask import session, redirect, url_for, flash

def is_authenticated():
    """Check if user is authenticated"""
    return session.get('authenticated', False)

def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
