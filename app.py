import os
from flask import Flask, render_template, session
from config import Config
from database import init_app_db, db
from models import Tollgate, Vehicle, Transaction, TollAccount

def create_app(force_sqlite=False):
    app = Flask(__name__)
    app.config.from_object(Config)
    if force_sqlite:
        app.config['FORCE_SQLITE'] = True
        
    # Initialize database with dual-mode support (MySQL preferred, SQLite fallback)
    init_app_db(app)
    
    # Register Blueprints
    from routes.auth import auth_bp
    from routes.simulation import simulation_bp
    from routes.motorist import motorist_bp
    from routes.admin import admin_bp
    from routes.modules import modules_bp
    from routes.api import api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(simulation_bp)
    app.register_blueprint(motorist_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(modules_bp)
    app.register_blueprint(api_bp)
    
    # Jinja filters and context processors
    @app.template_filter('currency')
    def currency_filter(value):
        try:
            return f"K{float(value):,.2f}"
        except (ValueError, TypeError):
            return "K0.00"
            
    @app.context_processor
    def inject_global_vars():
        return {
            'system_name': Config.SYSTEM_NAME,
            'agency': Config.AGENCY,
            'currency_symbol': Config.CURRENCY_SYMBOL,
            'active_db_engine': app.config.get('ACTIVE_DB_ENGINE', 'MySQL 9.0'),
            'current_user_name': session.get('user_name'),
            'current_user_role': session.get('user_role'),
            'current_user_email': session.get('user_email'),
            'is_authenticated': 'user_id' in session
        }
        
    @app.route('/')
    def index():
        total_vehicles = Vehicle.query.count()
        total_txns = Transaction.query.count()
        operational_gates = Tollgate.query.filter_by(status='OPERATIONAL').count()
        return render_template(
            'index.html',
            total_vehicles=total_vehicles,
            total_txns=total_txns,
            operational_gates=operational_gates
        )
        
    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404
        
    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
        
    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 70)
    print(" INTEGRATED AUTOMATED SELF-SERVICE TOLLGATE & MANAGEMENT PLATFORM")
    print(" Republic of Zambia — National Road Fund Agency (NRFA)")
    print(" Academic Prototype — 30% Functional Implementation")
    print(" Active Database:", app.config.get('ACTIVE_DB_ENGINE'))
    print(" Server URL: http://127.0.0.1:5000")
    print("=" * 70)
    app.run(debug=True, host='0.0.0.0', port=5000)
