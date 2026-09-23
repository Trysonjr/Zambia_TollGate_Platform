import uuid
import datetime
from config import Config
from database import db
from models import Vehicle, TollAccount, Tollgate, Transaction, User
from services.audit_service import log_audit

def normalize_plate(plate):
    """Normalize vehicle registration (uppercase, clean spaces)."""
    if not plate:
        return ""
    return " ".join(plate.strip().upper().split())

def calculate_toll_fee(vehicle_type):
    """Returns the statutory toll fee based on vehicle classification."""
    rates = Config.TOLL_RATES
    return rates.get(vehicle_type, rates['Light Vehicle'])

def lookup_vehicle(registration_number):
    """Finds vehicle, linked owner, and toll account balance."""
    norm_plate = normalize_plate(registration_number)
    vehicle = Vehicle.query.filter(
        db.func.replace(Vehicle.registration_number, ' ', '') == norm_plate.replace(' ', '')
    ).first()
    
    if not vehicle:
        return None
        
    account = TollAccount.query.filter_by(user_id=vehicle.user_id).first()
    owner = db.session.get(User, vehicle.user_id)
    
    return {
        'vehicle': vehicle,
        'owner': owner,
        'account': account,
        'balance': float(account.balance) if account else 0.00
    }

def lookup_by_rfid(rfid_tag):
    """Finds vehicle and toll account by RFID / E-Tag ID."""
    if not rfid_tag:
        return None
    clean_tag = rfid_tag.strip().upper()
    vehicle = Vehicle.query.filter_by(rfid_tag=clean_tag).first()
    if not vehicle:
        return None
    account = TollAccount.query.filter_by(user_id=vehicle.user_id).first()
    owner = db.session.get(User, vehicle.user_id)
    return {
        'vehicle': vehicle,
        'owner': owner,
        'account': account,
        'balance': float(account.balance) if account else 0.00
    }

def process_toll_payment(vehicle_reg, vehicle_type, tollgate_id, lane_number='Lane 1', 
                         payment_method='Toll Account / E-Tag', actor_email=None):
    """
    Core toll payment verification and transaction recording engine.
    - If payment_method is 'Toll Account / E-Tag':
        Checks balance. If sufficient -> Deducts fee, creates TXN, logs audit.
        If insufficient -> Creates failed/flagged TXN record, logs audit, returns insufficient status.
    - If payment_method is Mobile Money (Airtel, MTN, Zamtel):
        Simulates successful payment, creates TXN, logs audit.
    """
    fee = calculate_toll_fee(vehicle_type)
    norm_plate = normalize_plate(vehicle_reg)
    
    # Verify tollgate exists
    tollgate = db.session.get(Tollgate, tollgate_id)
    if not tollgate:
        tollgate = Tollgate.query.first()
        if not tollgate:
            # Fallback mock tollgate if DB not yet seeded
            tollgate_name = "Lusaka East Toll Plaza"
            tollgate_id = 1
        else:
            tollgate_name = tollgate.name
            tollgate_id = tollgate.id
    else:
        tollgate_name = tollgate.name

    txn_ref = f"TXN-ZM-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:4].upper()}"
    lookup = lookup_vehicle(norm_plate)
    
    # 1. Processing via Toll Account / E-Tag
    if 'Toll Account' in payment_method or 'E-Tag' in payment_method:
        if not lookup or not lookup.get('account'):
            # Unregistered vehicle attempting E-Tag deduction
            log_audit(
                action='TOLL_PAYMENT_UNREGISTERED',
                actor_email=actor_email or 'operator@tollgate.gov.zm',
                reference_id=txn_ref,
                details=f"Unregistered vehicle {norm_plate} arrived at {tollgate_name} ({lane_number})"
            )
            return {
                'success': False,
                'status': 'UNREGISTERED_VEHICLE',
                'fee': fee,
                'vehicle_reg': norm_plate,
                'vehicle_type': vehicle_type,
                'message': f"Vehicle {norm_plate} has no registered NRFA Toll Account. Please use Mobile Money.",
                'can_use_mobile_money': True
            }
            
        account = lookup['account']
        balance_before = float(account.balance)
        
        if balance_before < fee:
            # Insufficient funds
            txn = Transaction(
                transaction_ref=txn_ref,
                vehicle_reg=norm_plate,
                vehicle_type=vehicle_type,
                tollgate_id=tollgate_id,
                lane_number=lane_number,
                amount=fee,
                payment_method='Toll Account / E-Tag',
                status='INSUFFICIENT_FUNDS',
                balance_before=balance_before,
                balance_after=balance_before
            )
            db.session.add(txn)
            db.session.commit()
            
            log_audit(
                action='TOLL_PAYMENT_FAILED_BALANCE',
                actor_email=actor_email or lookup['owner'].email,
                reference_id=txn_ref,
                details=f"Insufficient balance for {norm_plate}: Required K{fee:.2f}, Available K{balance_before:.2f}"
            )
            
            return {
                'success': False,
                'status': 'INSUFFICIENT_FUNDS',
                'fee': fee,
                'current_balance': balance_before,
                'vehicle_reg': norm_plate,
                'vehicle_type': vehicle_type,
                'message': f"Insufficient Balance! Toll fee is K{fee:.2f}, but current balance is K{balance_before:.2f}.",
                'can_use_mobile_money': True
            }
            
        # Deduct toll fee from account balance
        account.deduct(fee)
        balance_after = float(account.balance)
        
        txn = Transaction(
            transaction_ref=txn_ref,
            vehicle_reg=norm_plate,
            vehicle_type=vehicle_type,
            tollgate_id=tollgate_id,
            lane_number=lane_number,
            amount=fee,
            payment_method='Toll Account / E-Tag',
            status='SUCCESSFUL',
            balance_before=balance_before,
            balance_after=balance_after
        )
        db.session.add(txn)
        db.session.commit()
        
        log_audit(
            action='TOLL_PAYMENT_SUCCESS',
            actor_email=actor_email or lookup['owner'].email,
            reference_id=txn_ref,
            details=f"Paid K{fee:.2f} via E-Tag at {tollgate_name} {lane_number}. Balance: K{balance_before:.2f} -> K{balance_after:.2f}"
        )
        
        return {
            'success': True,
            'status': 'SUCCESSFUL',
            'transaction_ref': txn_ref,
            'fee': fee,
            'balance_before': balance_before,
            'balance_after': balance_after,
            'vehicle_reg': norm_plate,
            'vehicle_type': vehicle_type,
            'tollgate_name': tollgate_name,
            'lane_number': lane_number,
            'payment_method': 'Toll Account / E-Tag',
            'message': 'Payment Successful! Barrier opening...',
            'barrier_action': 'OPEN'
        }

    # 2. Processing via Mobile Money Simulation (Airtel, MTN, Zamtel)
    else:
        balance_before = float(lookup['balance']) if lookup and lookup.get('account') else None
        
        txn = Transaction(
            transaction_ref=txn_ref,
            vehicle_reg=norm_plate,
            vehicle_type=vehicle_type,
            tollgate_id=tollgate_id,
            lane_number=lane_number,
            amount=fee,
            payment_method=payment_method,
            status='SUCCESSFUL',
            balance_before=balance_before,
            balance_after=balance_before
        )
        db.session.add(txn)
        db.session.commit()
        
        actor = lookup['owner'].email if lookup and lookup.get('owner') else (actor_email or 'operator@tollgate.gov.zm')
        log_audit(
            action='TOLL_PAYMENT_MOBILE_MONEY',
            actor_email=actor,
            reference_id=txn_ref,
            details=f"Paid K{fee:.2f} via {payment_method} at {tollgate_name} {lane_number} for {norm_plate}"
        )
        
        return {
            'success': True,
            'status': 'SUCCESSFUL',
            'transaction_ref': txn_ref,
            'fee': fee,
            'vehicle_reg': norm_plate,
            'vehicle_type': vehicle_type,
            'tollgate_name': tollgate_name,
            'lane_number': lane_number,
            'payment_method': payment_method,
            'balance_before': balance_before,
            'balance_after': balance_before,
            'message': f"Payment Successful via {payment_method}! Barrier opening...",
            'barrier_action': 'OPEN'
        }
