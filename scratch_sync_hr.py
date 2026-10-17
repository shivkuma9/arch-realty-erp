import os
import sys
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    db.create_all()
    conn = db.engine.raw_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    existing_cols = [row[1] for row in cursor.fetchall()]
    new_cols = [
        ("emp_status", "VARCHAR(32) DEFAULT 'Active'"),
        ("dob", "DATE"),
        ("gender", "VARCHAR(16) DEFAULT 'Male'"),
        ("location", "VARCHAR(128) DEFAULT 'HQ - Office'"),
        ("reporting_manager", "VARCHAR(128)"),
        ("emergency_contact", "VARCHAR(128)"),
        ("permanent_address", "VARCHAR(256)")
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name} to users")
    conn.commit()
    conn.close()
    print("Database schema synced successfully for HR models.")
