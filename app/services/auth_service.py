from functools import wraps
from flask import abort, flash, redirect, url_for, request
from flask_login import current_user
from app.models import Roles, AuditLog
from app.extensions import db

def role_required(*roles):
    """Ensure user has at least one of the specified roles or is Super Admin."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login', next=request.url))
            if not current_user.has_role(*roles):
                flash('You do not have permission to access this resource.', 'danger')
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def management_required(f):
    """Restricted to Super Admin, Director / Owner, and Manager."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER)(f)

def accounts_required(f):
    """Restricted to Super Admin, Director / Owner, and Accounts Executive."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.ACCOUNTS_EXEC)(f)

def hr_required(f):
    """Restricted to Super Admin, Director / Owner, and HR / Operations."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.HR_OPS)(f)

def crm_required(f):
    """Restricted to Sales Executives, BDEs, Managers, Directors, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.SALES_EXEC, Roles.BDE)(f)

def inventory_required(f):
    """Restricted to Sales, Field Executives, Managers, Directors, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.SALES_EXEC, Roles.BDE, Roles.FIELD_EXEC)(f)

def deals_required(f):
    """Restricted to Sales, Accounts, Managers, Directors, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.SALES_EXEC, Roles.BDE, Roles.ACCOUNTS_EXEC)(f)

def field_required(f):
    """Restricted to Field Executives, Sales, Managers, Directors, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.FIELD_EXEC, Roles.SALES_EXEC, Roles.BDE)(f)

def reports_required(f):
    """Restricted to Directors, Managers, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER)(f)

def marketing_required(f):
    """Restricted to Digital Marketing & IT Executives, Managers, Directors, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.DIGITAL_MKT, Roles.IT_ADMIN)(f)

def it_required(f):
    """Restricted to IT Support & Systems, Digital Marketing Executives, Directors, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.IT_ADMIN, Roles.DIGITAL_MKT)(f)

def tech_marketing_required(f):
    """Restricted to Merged Tech & Digital Marketing department, Managers, Directors, and Super Admin."""
    return role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR, Roles.MANAGER, Roles.DIGITAL_MKT, Roles.IT_ADMIN)(f)



def log_audit(action, entity_type, entity_id=None, details=None):
    """Helper to record audit logs."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        ip_address = request.remote_addr if request else None
        log_entry = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None,
            details=details,
            ip_address=ip_address
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception:
        db.session.rollback()
