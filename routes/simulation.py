import datetime
from flask import Blueprint, render_template, request, jsonify, session
from config import Config
from models import Tollgate, Vehicle, TollAccount, Transaction
from services.toll_service import (
    calculate_toll_fee, lookup_vehicle, lookup_by_rfid, 
    process_toll_payment, normalize_plate
)
from services.audit_service import log_audit

simulation_bp = Blueprint('simulation', __name__)

@simulation_bp.route('/simulation')
def simulation_page():
    tollgates = Tollgate.query.filter_by(status='OPERATIONAL').all()
    if not tollgates:
        tollgates = Tollgate.query.all()
        
    rates = Config.TOLL_RATES
    recent_txns = Transaction.query.order_by(Transaction.created_at.desc()).limit(5).all()
    sample_vehicles = Vehicle.query.limit(6).all()
    
    return render_template(
        'simulation.html',
        tollgates=tollgates,
        rates=rates,
        recent_txns=recent_txns,
        sample_vehicles=sample_vehicles,
        currency=Config.CURRENCY_SYMBOL
    )

@simulation_bp.route('/api/simulation/detect', methods=['POST'])
def detect_vehicle():
    """
    Simulates ANPR camera recognition upon vehicle arrival at tollgate.
    """
    data = request.get_json() or {}
    plate = normalize_plate(data.get('registration_number', ''))
    vehicle_type = data.get('vehicle_type', 'Light Vehicle')
    tollgate_id = data.get('tollgate_id')
    lane_number = data.get('lane_number', 'Lane 1')
    
    if not plate:
        return jsonify({'error': 'Vehicle registration number is required'}), 400
        
    fee = calculate_toll_fee(vehicle_type)
    lookup = lookup_vehicle(plate)
    
    # Simulate high ANPR optical recognition confidence
    confidence = 98.4
    
    response_data = {
        'detected': True,
        'registration_number': plate,
        'vehicle_type': vehicle_type,
        'toll_fee': fee,
        'lane_number': lane_number,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'anpr_confidence': f"{confidence}%",
        'is_registered': lookup is not None,
    }
    
    if lookup:
        response_data.update({
            'owner_name': lookup['owner'].full_name if lookup.get('owner') else 'Registered Motorist',
            'account_number': lookup['account'].account_number if lookup.get('account') else 'N/A',
            'balance': lookup['balance'],
            'rfid_tag': lookup['vehicle'].rfid_tag,
            'make_model': lookup['vehicle'].make_model,
            'has_sufficient_balance': lookup['balance'] >= fee
        })
    else:
        response_data.update({
            'owner_name': 'Unregistered Motorist',
            'account_number': 'None',
            'balance': 0.00,
            'rfid_tag': 'NO-TAG-DETECTED',
            'make_model': 'Standard Vehicle',
            'has_sufficient_balance': False
        })
        
    return jsonify(response_data)

@simulation_bp.route('/api/simulation/rfid-scan', methods=['POST'])
def scan_rfid():
    """
    Simulates RFID/E-Tag sensor reading on vehicle windshield.
    """
    data = request.get_json() or {}
    rfid_tag = data.get('rfid_tag', '').strip()
    plate = normalize_plate(data.get('registration_number', ''))
    vehicle_type = data.get('vehicle_type', 'Light Vehicle')
    
    lookup = None
    if rfid_tag:
        lookup = lookup_by_rfid(rfid_tag)
    elif plate:
        lookup = lookup_vehicle(plate)
        
    fee = calculate_toll_fee(vehicle_type)
    
    if lookup and lookup.get('vehicle'):
        vehicle = lookup['vehicle']
        account = lookup.get('account')
        balance = lookup.get('balance', 0.00)
        
        return jsonify({
            'success': True,
            'rfid_tag': vehicle.rfid_tag,
            'registration_number': vehicle.registration_number,
            'vehicle_type': vehicle.vehicle_type,
            'account_number': account.account_number if account else 'N/A',
            'balance': balance,
            'toll_fee': fee,
            'has_sufficient_balance': balance >= fee,
            'message': f"RFID Tag [{vehicle.rfid_tag}] scanned successfully."
        })
    else:
        return jsonify({
            'success': False,
            'rfid_tag': rfid_tag or 'UNKNOWN',
            'balance': 0.00,
            'toll_fee': fee,
            'has_sufficient_balance': False,
            'message': "No active E-Tag detected for this vehicle."
        }), 404

@simulation_bp.route('/api/simulation/process-payment', methods=['POST'])
def process_payment_api():
    """
    Processes simulated toll payment (E-Tag deduction or Mobile Money).
    """
    data = request.get_json() or {}
    plate = data.get('registration_number')
    vehicle_type = data.get('vehicle_type', 'Light Vehicle')
    tollgate_id = data.get('tollgate_id', 1)
    lane_number = data.get('lane_number', 'Lane 1')
    payment_method = data.get('payment_method', 'Toll Account / E-Tag')
    actor_email = session.get('user_email', 'operator@tollgate.gov.zm')
    
    if not plate:
        return jsonify({'error': 'Registration number is missing'}), 400
        
    result = process_toll_payment(
        vehicle_reg=plate,
        vehicle_type=vehicle_type,
        tollgate_id=tollgate_id,
        lane_number=lane_number,
        payment_method=payment_method,
        actor_email=actor_email
    )
    
    return jsonify(result)

@simulation_bp.route('/api/simulation/barrier-trigger', methods=['POST'])
def barrier_trigger():
    """
    Software simulation of physical boom barrier microcontroller/relay.
    """
    data = request.get_json() or {}
    state = data.get('state', 'OPEN')
    lane = data.get('lane_number', 'Lane 1')
    tollgate_id = data.get('tollgate_id', 1)
    
    if state == 'OPEN':
        log_audit(
            action='BARRIER_OPENED',
            actor_email=session.get('user_email', 'system@tollgate.gov.zm'),
            details=f"Automated boom barrier triggered OPEN at {lane}"
        )
    elif state == 'CLOSED':
        log_audit(
            action='BARRIER_CLOSED',
            actor_email=session.get('user_email', 'system@tollgate.gov.zm'),
            details=f"Automated boom barrier reset to CLOSED at {lane}"
        )
        
    return jsonify({
        'barrier_state': state,
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'message': f"Barrier status: {state}"
    })
