import os
from flask import Flask, render_template
from config import Config
from app.extensions import db, login_manager, csrf, migrate

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure required instance folders exist
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'instance/uploads'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, '..', 'instance'), exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.crm import crm_bp
    from app.routes.properties import properties_bp
    from app.routes.deals import deals_bp
    from app.routes.finance import finance_bp
    from app.routes.field import field_bp
    from app.routes.hr import hr_bp
    from app.routes.reports import reports_bp
    from app.routes.settings import settings_bp
    from app.routes.documents import documents_bp
    from app.routes.marketing import marketing_bp
    from app.routes.it import it_bp
    from app.routes.sourcing import sourcing_bp
    from app.routes.shortlisting import shortlisting_bp
    from app.routes.gps import gps_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(crm_bp, url_prefix='/crm')
    app.register_blueprint(properties_bp, url_prefix='/properties')
    app.register_blueprint(deals_bp, url_prefix='/deals')
    app.register_blueprint(finance_bp, url_prefix='/finance')
    app.register_blueprint(field_bp, url_prefix='/field')
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(settings_bp, url_prefix='/settings')
    app.register_blueprint(documents_bp, url_prefix='/documents')
    app.register_blueprint(marketing_bp, url_prefix='/marketing')
    app.register_blueprint(it_bp, url_prefix='/it')
    app.register_blueprint(sourcing_bp, url_prefix='/sourcing')
    app.register_blueprint(shortlisting_bp, url_prefix='/shortlisting')
    app.register_blueprint(gps_bp, url_prefix='/gps')

    # Root and Admin redirects
    @app.route('/')
    def index():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))

    @app.route('/admin')
    @app.route('/admin/')
    def admin_redirect():
        from flask import redirect, url_for
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login', next=url_for('dashboard.index')))

    # Jinja Context Processors
    @app.context_processor
    def inject_globals():
        from app.models import Roles, Notification, Attendance
        from flask_login import current_user
        from datetime import date
        unread_notifications = 0
        my_today_punch = None
        if current_user.is_authenticated:
            unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            my_today_punch = Attendance.query.filter_by(user_id=current_user.id, attendance_date=date.today()).first()
        return {
            'Roles': Roles,
            'unread_notifications_count': unread_notifications,
            'my_today_punch': my_today_punch,
            'app_name': 'ARCH Realty',
            'app_tagline': 'Real Estate Consulting • Ahmedabad, Gujarat',
            'currency_symbol': '₹'
        }

    # Custom template filters
    @app.template_filter('inr')
    def inr_format(value):
        if value is None:
            return '₹ 0.00'
        try:
            val = float(value)
            # Indian numbering system formatting
            s = f"{val:,.2f}"
            return f"₹ {s}"
        except Exception:
            return f"₹ {value}"

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    # Auto-initialize database tables and seed if brand new
    with app.app_context():
        try:
            db.create_all()
            from app.models import User
            if not User.query.first():
                from scripts.seed_demo_data import seed
                seed(app)
        except Exception as e:
            app.logger.warning(f"Database auto-init notice: {e}")

    return app
