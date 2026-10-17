import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from app import create_app
from app.extensions import db
from app.models import User, Roles
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed users for each role
        admin = User(username='admin', email='admin@test.local', full_name='System Admin', role=Roles.SUPER_ADMIN, department='Management')
        admin.set_password('pass123')

        director = User(username='director', email='director@test.local', full_name='Director Patel', role=Roles.DIRECTOR, department='Management')
        director.set_password('pass123')

        sales = User(username='sales', email='sales@test.local', full_name='Sales Exec', role=Roles.SALES_EXEC, department='Sales')
        sales.set_password('pass123')

        field = User(username='field', email='field@test.local', full_name='Field Agent', role=Roles.FIELD_EXEC, department='Field Operations')
        field.set_password('pass123')

        accounts = User(username='accounts', email='accounts@test.local', full_name='Accounts Officer', role=Roles.ACCOUNTS_EXEC, department='Finance')
        accounts.set_password('pass123')

        hr = User(username='hr', email='hr@test.local', full_name='HR Manager', role=Roles.HR_OPS, department='Human Resources')
        hr.set_password('pass123')

        marketing = User(username='marketing', email='marketing@test.local', full_name='Marketing Lead', role=Roles.DIGITAL_MKT, department='Marketing')
        marketing.set_password('pass123')

        it = User(username='it', email='it@test.local', full_name='IT Admin', role=Roles.IT_ADMIN, department='Information Technology')
        it.set_password('pass123')

        db.session.add_all([admin, director, sales, field, accounts, hr, marketing, it])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def login(client, username, password='pass123'):
    return client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)

# 1. Sales Executive Isolation
def test_sales_cannot_access_other_departments(client):
    login(client, 'sales')

    # CAN access sales & CRM
    assert client.get('/crm/leads').status_code == 200
    assert client.get('/properties/').status_code == 200
    assert client.get('/deals/').status_code == 200

    # CANNOT access Finance, Settings, HR Management
    assert client.get('/finance/').status_code == 403
    assert client.get('/settings/').status_code == 403
    assert client.get('/hr/recruitments').status_code == 403
    assert client.get('/hr/assets').status_code == 403
    assert client.get('/hr/payrolls').status_code == 403

    # Sidebar verification: Finance & Settings NOT visible
    dash_res = client.get('/', follow_redirects=True)
    assert b'Brokerage Receivables' not in dash_res.data
    assert b'Settings & Users' not in dash_res.data
    assert b'Recruitment Pipeline' not in dash_res.data

# 2. Field Executive Isolation
def test_field_cannot_access_other_departments(client):
    login(client, 'field')

    # CAN access Field visits & Property inventory
    assert client.get('/field/visits').status_code == 200
    assert client.get('/properties/').status_code == 200

    # CANNOT access CRM Leads, Deals, Finance, Settings, HR Management
    assert client.get('/crm/leads').status_code == 403
    assert client.get('/deals/').status_code == 403
    assert client.get('/finance/').status_code == 403
    assert client.get('/settings/').status_code == 403
    assert client.get('/hr/recruitments').status_code == 403

    # Sidebar verification
    dash_res = client.get('/', follow_redirects=True)
    assert b'CRM & Inquiries' not in dash_res.data
    assert b'Deals & Pipeline' not in dash_res.data
    assert b'Brokerage Receivables' not in dash_res.data

# 3. Accounts Executive Isolation
def test_accounts_cannot_access_other_departments(client):
    login(client, 'accounts')

    # CAN access Finance & Payroll
    assert client.get('/finance/').status_code == 200
    assert client.get('/hr/payrolls').status_code == 200
    assert client.get('/deals/').status_code == 200 # Read-only view for billing

    # CANNOT access CRM Leads, Field Visits, HR Recruitment, Settings
    assert client.get('/crm/leads').status_code == 403
    assert client.get('/field/visits').status_code == 403
    assert client.get('/hr/recruitments').status_code == 403
    assert client.get('/settings/').status_code == 403

    # Sidebar verification
    dash_res = client.get('/', follow_redirects=True)
    assert b'CRM & Inquiries' not in dash_res.data
    assert b'Site Visits' not in dash_res.data
    assert b'Recruitment Pipeline' not in dash_res.data

# 4. HR Operations Isolation
def test_hr_cannot_access_other_departments(client):
    login(client, 'hr')

    # CAN access HR Management & Attendance
    assert client.get('/hr/attendance').status_code == 200
    assert client.get('/hr/recruitments').status_code == 200
    assert client.get('/hr/assets').status_code == 200
    assert client.get('/hr/payrolls').status_code == 200

    # CANNOT access CRM Leads, Properties, Deals, Field Visits, Finance, Settings
    assert client.get('/crm/leads').status_code == 403
    assert client.get('/properties/').status_code == 403
    assert client.get('/deals/').status_code == 403
    assert client.get('/field/visits').status_code == 403
    assert client.get('/finance/').status_code == 403
    assert client.get('/settings/').status_code == 403

    # Sidebar verification
    dash_res = client.get('/', follow_redirects=True)
    assert b'CRM & Inquiries' not in dash_res.data
    assert b'Property Inventory' not in dash_res.data
    assert b'Deals & Pipeline' not in dash_res.data
    assert b'Site Visits' not in dash_res.data
    assert b'Brokerage Receivables' not in dash_res.data

# 5. Digital Marketing Executive (Merged Tech & Growth) Isolation
def test_marketing_cannot_access_other_departments(client):
    login(client, 'marketing')

    # CAN access Digital Marketing & IT (Merged)
    assert client.get('/marketing/').status_code == 200
    assert client.get('/marketing/campaigns').status_code == 200
    assert client.get('/marketing/attribution').status_code == 200
    assert client.get('/it/').status_code == 200 # Merged with IT for real estate operations
    assert client.get('/it/tickets').status_code == 200

    # CANNOT access Finance, HR Management, Settings, CRM Leads
    assert client.get('/finance/').status_code == 403
    assert client.get('/settings/').status_code == 403
    assert client.get('/hr/payrolls').status_code == 403
    assert client.get('/crm/leads').status_code == 403

    # Sidebar verification
    dash_res = client.get('/', follow_redirects=True)
    assert b'Brokerage Receivables' not in dash_res.data
    assert b'Settings & Users' not in dash_res.data
    assert b'Digital Marketing & IT' in dash_res.data

# 6. IT Support & Systems (Merged Tech & Growth) Isolation
def test_it_cannot_access_other_departments(client):
    login(client, 'it')

    # CAN access IT Department & Digital Marketing (Merged)
    assert client.get('/it/').status_code == 200
    assert client.get('/it/assets').status_code == 200
    assert client.get('/it/tickets').status_code == 200
    assert client.get('/it/infrastructure').status_code == 200
    assert client.get('/marketing/').status_code == 200 # Merged with Marketing for real estate operations

    # CANNOT access Finance, Deals, HR Payroll, Settings
    assert client.get('/finance/').status_code == 403
    assert client.get('/deals/').status_code == 403
    assert client.get('/hr/payrolls').status_code == 403
    assert client.get('/settings/').status_code == 403

    # Sidebar verification
    dash_res = client.get('/', follow_redirects=True)
    assert b'Brokerage Receivables' not in dash_res.data
    assert b'Settings & Users' not in dash_res.data
    assert b'Digital Marketing & IT' in dash_res.data
