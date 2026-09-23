import random
import uuid
import datetime
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database import db
from models import User, TollAccount, Vehicle, Transaction, Payment
from routes.auth import login_required
from services.audit_service import log_audit
from services.toll_service import normalize_plate
from config import Config

motorist_bp = Blueprint('motorist', __name__)

@motorist_bp.route('/motorist/dashboard')
@login_required
def dashboard():
    user = db.session.get(User, session['user_id'])
    if not user:
        return redirect(url_for('auth.login'))
        
    account = TollAccount.query.filter_by(user_id=user.id).first()
    if not account:
        # Auto-create if not existing
        account = TollAccount(
            user_id=user.id,
            account_number=f"NRFA-ACC-{random.randint(1000, 9999)}",
            balance=100.00,
            status='ACTIVE'
        )
        db.session.add(account)
        db.session.commit()
        
    vehicles = Vehicle.query.filter_by(user_id=user.id).all()
    vehicle_plates = [v.registration_number for v in vehicles]
    
    # Fetch transactions matching any of motorist's vehicles
    if vehicle_plates:
        transactions = Transaction.query.filter(
            Transaction.vehicle_reg.in_(vehicle_plates)
        ).order_by(Transaction.created_at.desc()).limit(10).all()
    else:
        transactions = []
        
    recent_payments = Payment.query.filter_by(account_id=account.id).order_by(Payment.created_at.desc()).limit(5).all()
    
    return render_template(
        'motorist_dashboard.html',
        user=user,
        account=account,
        vehicles=vehicles,
        transactions=transactions,
        payments=recent_payments,
        currency=Config.CURRENCY_SYMBOL
    )

@motorist_bp.route('/vehicles')
@login_required
def vehicles_page():
    user_id = session['user_id']
    vehicles = Vehicle.query.filter_by(user_id=user_id).all()
    rates = Config.TOLL_RATES
    return render_template('vehicles.html', vehicles=vehicles, rates=rates, currency=Config.CURRENCY_SYMBOL)

@motorist_bp.route('/vehicles/add', methods=['POST'])
@login_required
def add_vehicle():
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    
    raw_plate = request.form.get('registration_number', '')
    vehicle_type = request.form.get('vehicle_type', 'Light Vehicle')
    make_model = request.form.get('make_model', 'Standard Vehicle').strip()
    rfid_tag = request.form.get('rfid_tag', '').strip().upper()
    
    plate = normalize_plate(raw_plate)
    if not plate:
        flash('Vehicle registration plate is required.', 'danger')
        return redirect(url_for('motorist.vehicles_page'))
        
    # Check if plate already registered
    existing_plate = Vehicle.query.filter_by(registration_number=plate).first()
    if existing_plate:
        flash(f'Vehicle with registration {plate} is already registered in the system.', 'warning')
        return redirect(url_for('motorist.vehicles_page'))
        
    # Auto-generate RFID if left blank
    if not rfid_tag:
        rfid_tag = f"TAG-{random.randint(100, 999)}"
        
    # Check if RFID tag unique
    existing_tag = Vehicle.query.filter_by(rfid_tag=rfid_tag).first()
    if existing_tag:
        rfid_tag = f"TAG-{random.randint(1000, 9999)}"
        
    vehicle = Vehicle(
        user_id=user_id,
        registration_number=plate,
        vehicle_type=vehicle_type,
        make_model=make_model or 'Unspecified',
        rfid_tag=rfid_tag,
        status='ACTIVE'
    )
    db.session.add(vehicle)
    db.session.commit()
    
    log_audit(
        action='VEHICLE_REGISTERED',
        actor_email=user.email,
        reference_id=vehicle.registration_number,
        details=f"Registered vehicle {vehicle.registration_number} ({vehicle.vehicle_type}) with E-Tag {vehicle.rfid_tag}"
    )
    
    flash(f'Vehicle {plate} registered successfully and linked to E-Tag {rfid_tag}!', 'success')
    return redirect(url_for('motorist.vehicles_page'))

@motorist_bp.route('/account/fund', methods=['POST'])
@login_required
def fund_account():
    user_id = session['user_id']
    user = db.session.get(User, user_id)
    account = TollAccount.query.filter_by(user_id=user_id).first()
    
    try:
        amount = float(request.form.get('amount', 0))
    except (ValueError, TypeError):
        amount = 0.0
        
    provider = request.form.get('provider', 'Airtel Money')
    phone = request.form.get('phone', user.phone)
    
    if amount <= 0:
        flash('Please enter a valid top-up amount greater than K0.00.', 'danger')
        return redirect(url_for('motorist.dashboard'))
        
    # Process simulated wallet deposit
    old_balance = float(account.balance)
    new_balance = account.deposit(amount)
    
    pay_ref = f"MOMO-ZM-{uuid.uuid4().hex[:6].upper()}"
    payment = Payment(
        account_id=account.id,
        amount=amount,
        provider=provider,
        reference=pay_ref,
        status='SUCCESSFUL'
    )
    db.session.add(payment)
    db.session.commit()
    
    log_audit(
        action='ACCOUNT_FUNDED',
        actor_email=user.email,
        reference_id=pay_ref,
        details=f"Funded K{amount:.2f} via {provider} ({phone}). Balance: K{old_balance:.2f} -> K{new_balance:.2f}"
    )
    
    flash(f'Toll Account successfully funded with K{amount:.2f} via {provider}! New balance is K{new_balance:.2f}.', 'success')
    return redirect(url_for('motorist.dashboard'))
