import datetime
from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from sqlalchemy import func
from database import db
from models import User, Vehicle, TollAccount, Tollgate, Transaction, AuditLog
from routes.auth import admin_required, login_required
from config import Config

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/dashboard')
@admin_required
def dashboard():
    today_start = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    total_vehicles = Vehicle.query.count()
    total_txns = Transaction.query.count()
    txns_today = Transaction.query.filter(Transaction.created_at >= today_start).count()
    
    total_revenue_result = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.status == 'SUCCESSFUL'
    ).scalar()
    total_revenue = float(total_revenue_result or 0.0)
    
    active_accounts = TollAccount.query.filter_by(status='ACTIVE').count()
    failed_txns = Transaction.query.filter(Transaction.status != 'SUCCESSFUL').count()
    
    # Revenue breakdown by toll plaza
    plaza_stats = db.session.query(
        Tollgate.name,
        func.count(Transaction.id).label('tx_count'),
        func.coalesce(func.sum(Transaction.amount), 0).label('revenue')
    ).outerjoin(Transaction, (Transaction.tollgate_id == Tollgate.id) & (Transaction.status == 'SUCCESSFUL')
    ).group_by(Tollgate.id).all()
    
    # Vehicle type classification distribution
    type_stats = db.session.query(
        Transaction.vehicle_type,
        func.count(Transaction.id).label('count')
    ).group_by(Transaction.vehicle_type).all()
    
    # Recent audit activities
    recent_audits = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(8).all()
    
    # Recent transactions
    recent_transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(8).all()
    
    return render_template(
        'admin_dashboard.html',
        total_vehicles=total_vehicles,
        total_txns=total_txns,
        txns_today=txns_today,
        total_revenue=total_revenue,
        active_accounts=active_accounts,
        failed_txns=failed_txns,
        plaza_stats=plaza_stats,
        type_stats=type_stats,
        recent_audits=recent_audits,
        recent_transactions=recent_transactions,
        currency=Config.CURRENCY_SYMBOL
    )

@admin_bp.route('/admin/audit-logs')
@admin_required
def audit_logs():
    action_filter = request.args.get('action', '').strip()
    search = request.args.get('q', '').strip()
    
    query = AuditLog.query
    if action_filter:
        query = query.filter_by(action=action_filter)
    if search:
        query = query.filter(
            (AuditLog.actor_email.ilike(f'%{search}%')) |
            (AuditLog.reference_id.ilike(f'%{search}%')) |
            (AuditLog.details.ilike(f'%{search}%'))
        )
        
    logs = query.order_by(AuditLog.created_at.desc()).limit(100).all()
    
    # Unique actions for filtering dropdown
    distinct_actions = [a[0] for a in db.session.query(AuditLog.action).distinct().all()]
    
    return render_template('audit_logs.html', logs=logs, distinct_actions=distinct_actions, current_action=action_filter)

@admin_bp.route('/transactions')
def transactions():
    """Universal transactions view with search and filters."""
    plate_search = request.args.get('plate', '').strip()
    tollgate_id = request.args.get('tollgate_id', '')
    status = request.args.get('status', '')
    
    query = Transaction.query
    
    # If motorist is logged in and not admin, restrict to their vehicles unless admin view requested
    if session.get('user_role') == 'motorist' and not session.get('view_all'):
        user_id = session['user_id']
        vehicles = Vehicle.query.filter_by(user_id=user_id).all()
        plates = [v.registration_number for v in vehicles]
        query = query.filter(Transaction.vehicle_reg.in_(plates))
    
    if plate_search:
        query = query.filter(Transaction.vehicle_reg.ilike(f'%{plate_search}%'))
    if tollgate_id and tollgate_id.isdigit():
        query = query.filter_by(tollgate_id=int(tollgate_id))
    if status:
        query = query.filter_by(status=status)
        
    transactions_list = query.order_by(Transaction.created_at.desc()).limit(100).all()
    tollgates = Tollgate.query.all()
    
    return render_template(
        'transactions.html',
        transactions=transactions_list,
        tollgates=tollgates,
        current_plate=plate_search,
        current_tollgate=tollgate_id,
        current_status=status,
        currency=Config.CURRENCY_SYMBOL
    )
