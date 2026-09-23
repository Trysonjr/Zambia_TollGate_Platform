import random
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import db
from models import User, TollAccount
from services.audit_service import log_audit

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this portal.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Administrator authentication required.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        if session.get('user_role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('motorist.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['user_name'] = user.full_name
            session['user_email'] = user.email
            session['user_role'] = user.role
            
            log_audit(
                action='USER_LOGIN',
                actor_email=user.email,
                details=f"User {user.email} logged in with role: {user.role}"
            )
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('motorist.dashboard'))
        else:
            flash('Invalid email address or password. Please verify credentials.', 'danger')
            
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        initial_deposit = float(request.form.get('initial_deposit', 50.00))
        
        if not full_name or not email or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('register.html')
            
        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email address already exists.', 'warning')
            return render_template('register.html')
            
        # Create user
        user = User(
            full_name=full_name,
            email=email,
            phone=phone or '+260977000000',
            role='motorist'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush() # get user.id
        
        # Create linked toll account
        acc_num = f"NRFA-ACC-{random.randint(1000, 9999)}"
        account = TollAccount(
            user_id=user.id,
            account_number=acc_num,
            balance=initial_deposit,
            status='ACTIVE'
        )
        db.session.add(account)
        db.session.commit()
        
        log_audit(
            action='USER_REGISTERED',
            actor_email=user.email,
            reference_id=acc_num,
            details=f"New motorist registered: {full_name} with toll account {acc_num} (Initial deposit: K{initial_deposit:.2f})"
        )
        
        # Log the user in
        session['user_id'] = user.id
        session['user_name'] = user.full_name
        session['user_email'] = user.email
        session['user_role'] = user.role
        
        flash(f'Account created successfully! Your Toll Account {acc_num} has been initialized with K{initial_deposit:.2f}.', 'success')
        return redirect(url_for('motorist.dashboard'))
        
    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    user_email = session.get('user_email', 'unknown')
    log_audit(action='USER_LOGOUT', actor_email=user_email, details='User logged out')
    session.clear()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))
