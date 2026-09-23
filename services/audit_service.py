import logging
from flask import request
from database import db
from models import AuditLog

logger = logging.getLogger('audit_service')

def log_audit(action, actor_email='system@tollgate.gov.zm', reference_id=None, details=None, ip_address=None):
    """
    Central helper to record audit events across all platform actions.
    Ensures academic demonstration of complete traceability.
    """
    try:
        if ip_address is None:
            try:
                ip_address = request.remote_addr if request else '127.0.0.1'
            except Exception:
                ip_address = '127.0.0.1'
                
        log_entry = AuditLog(
            action=action,
            actor_email=actor_email,
            reference_id=str(reference_id) if reference_id else None,
            details=details,
            ip_address=ip_address or '127.0.0.1'
        )
        db.session.add(log_entry)
        db.session.commit()
        logger.info("[AUDIT] Action: %s | Actor: %s | Ref: %s", action, actor_email, reference_id)
        return log_entry
    except Exception as e:
        db.session.rollback()
        logger.error("Failed to write audit log: %s", str(e))
        return None
