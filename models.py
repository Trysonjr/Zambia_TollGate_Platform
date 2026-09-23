import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database import db

class User(db.Model):
    """User model supporting both Motorists and Administrators."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='motorist') # 'motorist' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    toll_account = db.relationship('TollAccount', backref='user', uselist=False, cascade='all, delete-orphan')
    vehicles = db.relationship('Vehicle', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def is_admin(self):
        return self.role == 'admin'
        
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class TollAccount(db.Model):
    """Prepaid toll wallet associated with a motorist."""
    __tablename__ = 'toll_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    account_number = db.Column(db.String(30), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), nullable=False, default=0.00)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    payments = db.relationship('Payment', backref='account', lazy='dynamic', cascade='all, delete-orphan')
    
    def deposit(self, amount):
        self.balance = float(self.balance) + float(amount)
        return self.balance
        
    def deduct(self, amount):
        if float(self.balance) >= float(amount):
            self.balance = float(self.balance) - float(amount)
            return True
        return False
        
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'account_number': self.account_number,
            'balance': float(self.balance),
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Vehicle(db.Model):
    """Vehicle registered under a motorist's toll account."""
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    registration_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    vehicle_type = db.Column(db.String(50), nullable=False, default='Light Vehicle')
    make_model = db.Column(db.String(100), default='Unspecified')
    rfid_tag = db.Column(db.String(50), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'registration_number': self.registration_number,
            'vehicle_type': self.vehicle_type,
            'make_model': self.make_model,
            'rfid_tag': self.rfid_tag,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Tollgate(db.Model):
    """Physical or simulated Zambian national toll plaza."""
    __tablename__ = 'tollgates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    location = db.Column(db.String(150), nullable=False)
    province = db.Column(db.String(50), nullable=False)
    lanes_count = db.Column(db.Integer, nullable=False, default=4)
    status = db.Column(db.String(20), nullable=False, default='OPERATIONAL')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='tollgate', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'location': self.location,
            'province': self.province,
            'lanes_count': self.lanes_count,
            'status': self.status
        }

class Transaction(db.Model):
    """Audit-proof record of every toll crossing."""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_ref = db.Column(db.String(50), unique=True, nullable=False, index=True)
    vehicle_reg = db.Column(db.String(20), nullable=False, index=True)
    vehicle_type = db.Column(db.String(50), nullable=False)
    tollgate_id = db.Column(db.Integer, db.ForeignKey('tollgates.id'), nullable=False)
    lane_number = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=False) # e.g., 'Toll Account / E-Tag', 'Airtel Money', 'MTN MoMo', 'Zamtel Kwacha'
    status = db.Column(db.String(30), nullable=False, default='SUCCESSFUL') # 'SUCCESSFUL', 'INSUFFICIENT_FUNDS', 'FAILED'
    balance_before = db.Column(db.Numeric(10, 2), nullable=True)
    balance_after = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_ref': self.transaction_ref,
            'vehicle_reg': self.vehicle_reg,
            'vehicle_type': self.vehicle_type,
            'tollgate_id': self.tollgate_id,
            'tollgate_name': self.tollgate.name if self.tollgate else 'Unknown Tollgate',
            'lane_number': self.lane_number,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'balance_before': float(self.balance_before) if self.balance_before is not None else None,
            'balance_after': float(self.balance_after) if self.balance_after is not None else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'created_at_human': self.created_at.strftime('%d/%m/%Y %H:%M') if self.created_at else None
        }

class Payment(db.Model):
    """Record of wallet top-up / funding transactions."""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('toll_accounts.id', ondelete='CASCADE'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    provider = db.Column(db.String(50), nullable=False) # e.g. 'Airtel Money', 'MTN MoMo', 'Zamtel Kwacha', 'Debit Card'
    reference = db.Column(db.String(60), unique=True, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='SUCCESSFUL')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'account_id': self.account_id,
            'amount': float(self.amount),
            'provider': self.provider,
            'reference': self.reference,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class AuditLog(db.Model):
    """Central audit log capturing all system activities."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(80), nullable=False, index=True)
    actor_email = db.Column(db.String(120), nullable=False)
    reference_id = db.Column(db.String(60), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), default='127.0.0.1')
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'action': self.action,
            'actor_email': self.actor_email,
            'reference_id': self.reference_id,
            'details': self.details,
            'ip_address': self.ip_address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
