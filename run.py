import os
from app import create_app
from app.extensions import db
from app.models import User, Roles

app = create_app()

@app.cli.command("init-db")
def init_db():
    """Create database tables."""
    db.create_all()
    print("Database tables created.")

@app.cli.command("seed-demo")
def seed_demo():
    """Seed sample data for demonstration."""
    from scripts.seed_demo_data import seed
    seed()

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() in ('true', '1', 't')
    app.run(host=host, port=port, debug=debug)
