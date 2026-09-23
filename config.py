import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class Config:
    """Application Configuration for Zambia Tollgate Platform."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'nrfa-zambia-tollgate-secret-key-2026')
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'TRYSON')
    MYSQL_DB = os.environ.get('MYSQL_DB', 'zambia_tollgate')
    
    # Preferred SQLAlchemy Database URI
    # Default to MySQL via PyMySQL; can be overridden by DATABASE_URL env var
    MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}?charset=utf8mb4"
    SQLITE_URI = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'tollgate.db')}"
    
    # If DATABASE_URL is set explicitly, use that; otherwise allow dual fallback
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', MYSQL_URI)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Zambian National Toll Fee Tariff (in ZMW / Zambian Kwacha)
    # Based on National Road Fund Agency (NRFA) Standard Toll Rates
    TOLL_RATES = {
        'Light Vehicle': 20.00,    # Saloons, SUVs, Station Wagons, Light 4x4s
        'Medium Vehicle': 50.00,   # Minibuses, Light Delivery Trucks (< 3.5 tonnes)
        'Heavy Vehicle': 100.00,   # Heavy Trucks, Long-distance Coaches (2-3 Axles)
        'Abnormal Load': 250.00    # Multi-Axle articulated trucks, Abnormal Cargo
    }
    
    CURRENCY_CODE = 'ZMW'
    CURRENCY_SYMBOL = 'K'
    SYSTEM_NAME = 'Integrated Automated Self-Service Tollgate & Management Platform'
    COUNTRY = 'Zambia'
    AGENCY = 'National Road Fund Agency (NRFA)'
