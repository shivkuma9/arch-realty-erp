from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Roles
from app.forms import LoginForm, ChangePasswordForm
from app.services.auth_service import log_audit
from app.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.username.data)
        ).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Your account has been deactivated. Please contact Administrator.', 'danger')
                return render_template('auth/login.html', form=form)
                
            user.failed_login_attempts = 0
            user.last_login = datetime.now(timezone.utc)
            db.session.commit()
            
            login_user(user, remember=form.remember_me.data)
            log_audit('LOGIN', 'User', user.id, f"User {user.username} logged in successfully.")
            flash(f"Welcome back, {user.full_name}!", 'success')
            
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard.index')
            return redirect(next_page)
        else:
            if user:
                user.failed_login_attempts += 1
                db.session.commit()
            flash('Invalid username/email or password.', 'danger')
            
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    log_audit('LOGOUT', 'User', current_user.id, f"User {current_user.username} logged out.")
    logout_user()
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            current_user.set_password(form.new_password.data)
            db.session.commit()
            log_audit('PASSWORD_CHANGE', 'User', current_user.id, 'Password updated.')
            flash('Your password has been changed successfully.', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Current password is incorrect.', 'danger')
    return render_template('auth/change_password.html', form=form)
