import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, text
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('tollgate_db')

db = SQLAlchemy()

def init_app_db(app):
    """
    Initializes the database connection with automatic fallback.
    Tries MySQL first as required by project specification.
    If MySQL server or credentials are not yet ready, falls back to SQLite
    to guarantee zero-crash execution during academic demonstrations.
    """
    mysql_uri = Config.MYSQL_URI
    use_mysql = False
    
    # Only test MySQL if explicitly not forced to sqlite
    if not app.config.get('FORCE_SQLITE', False):
        try:
            # Test MySQL connection with 2-second timeout
            test_engine = create_engine(mysql_uri, connect_args={'connect_timeout': 2})
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            use_mysql = True
            logger.info("Successfully connected to MySQL database: %s", Config.MYSQL_DB)
        except Exception as e:
            logger.warning(
                "MySQL connection could not be established (%s). "
                "Falling back to local SQLite engine to guarantee uninterrupted prototype demonstration. "
                "To connect to MySQL, provide your password in .env or config.py.",
                str(e)
            )
            use_mysql = False

    if use_mysql:
        app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
        app.config['ACTIVE_DB_ENGINE'] = 'MySQL 9.0'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLITE_URI
        app.config['ACTIVE_DB_ENGINE'] = 'SQLite (Academic Fallback Mode)'

    db.init_app(app)
    return db
