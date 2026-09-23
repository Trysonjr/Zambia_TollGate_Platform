from flask import Blueprint, jsonify, request, session
from config import Config
from models import Tollgate, Vehicle, TollAccount, Transaction, User
from services.toll_service import calculate_toll_fee, lookup_vehicle

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/tollgates', methods=['GET'])
def get_tollgates():
    gates = Tollgate.query.all()
    return jsonify([g.to_dict() for g in gates])

@api_bp.route('/rates', methods=['GET'])
def get_rates():
    return jsonify({
        'currency': Config.CURRENCY_SYMBOL,
        'currency_code': Config.CURRENCY_CODE,
        'tariffs': Config.TOLL_RATES
    })

@api_bp.route('/vehicles', methods=['GET'])
def get_vehicles():
    if session.get('user_role') == 'admin':
        vehicles = Vehicle.query.all()
    elif 'user_id' in session:
        vehicles = Vehicle.query.filter_by(user_id=session['user_id']).all()
    else:
        vehicles = Vehicle.query.limit(10).all()
    return jsonify([v.to_dict() for v in vehicles])

@api_bp.route('/vehicles/lookup/<plate>', methods=['GET'])
def api_lookup_vehicle(plate):
    res = lookup_vehicle(plate)
    if not res:
        return jsonify({'found': False, 'message': 'Vehicle not found'}), 404
        
    return jsonify({
        'found': True,
        'vehicle': res['vehicle'].to_dict(),
        'owner': res['owner'].full_name if res.get('owner') else 'Unknown',
        'account_number': res['account'].account_number if res.get('account') else None,
        'balance': res['balance']
    })

@api_bp.route('/transactions', methods=['GET'])
def get_transactions():
    limit = min(int(request.args.get('limit', 20)), 100)
    txns = Transaction.query.order_by(Transaction.created_at.desc()).limit(limit).all()
    return jsonify([t.to_dict() for t in txns])
