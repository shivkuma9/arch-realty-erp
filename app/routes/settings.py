import os
import shutil
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from app.models import User, Setting, AuditLog, Roles
from app.forms import UserForm
from app.services.auth_service import role_required, log_audit
from app.extensions import db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
@role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR)
def index():
    users = User.query.order_by(User.id.asc()).all()
    audit_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(50).all()
    settings = {s.key: s.value for s in Setting.query.all()}
    return render_template('settings/settings_index.html', users=users, audit_logs=audit_logs, settings=settings)

@settings_bp.route('/users/new', methods=['GET', 'POST'])
@settings_bp.route('/users/create', methods=['GET', 'POST'], endpoint='user_create')
@login_required
@role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR)
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter((User.username == form.username.data) | (User.email == form.email.data)).first():
            flash('Username or Email already registered.', 'danger')
            return render_template('settings/user_form.html', form=form, title="Create System User")

        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role=form.role.data,
            department=form.department.data,
            designation=form.designation.data,
            is_active=form.is_active.data
        )
        user.set_password(form.password.data or 'arch1234')
        db.session.add(user)
        db.session.commit()
        log_audit('CREATE_USER', 'User', user.id, f"Created user {user.username} ({user.role})")
        flash(f"User {user.username} created successfully!", 'success')
        return redirect(url_for('settings.index'))

    return render_template('settings/user_form.html', form=form, title="Create System User")

@settings_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR)
def toggle_user_status(user_id):
    if user_id == current_user.id:
        flash("You cannot deactivate your own administrative account.", 'warning')
        return redirect(url_for('settings.index'))

    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    status_str = "activated" if user.is_active else "deactivated"
    log_audit('STATUS_CHANGE', 'User', user.id, f"User {user.username} {status_str}")
    flash(f"User {user.username} has been {status_str}.", 'info')
    return redirect(url_for('settings.index'))

@settings_bp.route('/backup', methods=['POST'])
@login_required
@role_required(Roles.SUPER_ADMIN, Roles.DIRECTOR)
def backup_database():
    """Create a point-in-time snapshot backup of the SQLite database."""
    db_uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    if 'sqlite:///' in db_uri:
        db_path = db_uri.replace('sqlite:///', '')
        if os.path.exists(db_path):
            backup_dir = os.path.join(current_app.root_path, '..', 'instance', 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dest = os.path.join(backup_dir, f"arch_realty_backup_{ts}.db")
            shutil.copy2(db_path, backup_dest)
            log_audit('BACKUP', 'Database', None, f"Created backup: {backup_dest}")
            flash(f"Database backup created: {os.path.basename(backup_dest)}", 'success')
            return redirect(url_for('settings.index'))

    flash("Database backup is only supported for local SQLite instances.", 'info')
    return redirect(url_for('settings.index'))
