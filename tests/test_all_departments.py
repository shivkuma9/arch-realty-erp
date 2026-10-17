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

        accounts = User(username='accounts', email='accounts@test.local', full_name='Accounts Officer', role=Roles.ACCOUNTS_EXEC, department='Finance')
        accounts.set_password('pass123')

        hr = User(username='hr', email='hr@test.local', full_name='HR Manager', role=Roles.HR_OPS, department='Human Resources')
        hr.set_password('pass123')

        field = User(username='field', email='field@test.local', full_name='Field Agent', role=Roles.FIELD_EXEC, department='Field Operations')
        field.set_password('pass123')

        marketing = User(username='marketing', email='marketing@test.local', full_name='Marketing Lead', role=Roles.DIGITAL_MKT, department='Marketing')
        marketing.set_password('pass123')

        it = User(username='it', email='it@test.local', full_name='IT Admin', role=Roles.IT_ADMIN, department='Information Technology')
        it.set_password('pass123')

        db.session.add_all([admin, director, sales, accounts, hr, field, marketing, it])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def login(client, username, password='pass123'):
    return client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)

def test_all_department_routes_as_admin(client):
    # Log in as admin
    login(client, 'admin')

    routes_to_test = [
        # Dashboard
        '/',
        # CRM
        '/crm/leads',
        '/crm/leads/new',
        '/crm/clients',
        '/crm/clients/new',
        # Properties
        '/properties/',
        '/properties/new',
        '/properties/owners',
        '/properties/matching',
        '/properties/map',
        # Deals
        '/deals/',
        '/deals/new',
        # Finance
        '/finance/',
        '/finance/commissions/new',
        '/finance/expenses/new',
        # Field
        '/field/visits',
        '/field/visits/new',
        # HR
        '/hr/attendance',
        '/hr/tasks',
        '/hr/targets',
        '/hr/recruitments',
        '/hr/assets',
        '/hr/payrolls',
        '/hr/employees',
        # Documents
        '/documents/',
        # Reports
        '/reports/',
        # Settings
        '/settings/',
        '/settings/users/new',
        # Digital Marketing
        '/marketing/',
        '/marketing/campaigns',
        '/marketing/campaigns/create',
        '/marketing/attribution',
        # IT Department
        '/it/',
        '/it/assets',
        '/it/assets/create',
        '/it/tickets',
        '/it/tickets/create',
        '/it/infrastructure',
        # Sourcing & Acquisitions
        '/sourcing/',
        '/sourcing/assign',
        '/sourcing/my-sourcing',
        # Client Shortlisting Kanban
        '/shortlisting/',
        # GPS Tracking & Field Travel History
        '/gps/',
        # Property Approvals & Submissions
        '/properties/approvals',
        '/properties/submit',
        # Visits Calendar
        '/field/calendar',
        # CRM Reports & Exports
        '/reports/crm',
        '/reports/export/inquiry',
        '/reports/export/sourcing',
        '/reports/export/attendance',
    ]

    for route in routes_to_test:
        res = client.get(route, follow_redirects=True)
        assert res.status_code == 200, f"Route {route} failed with status {res.status_code}"


def test_hr_routes_as_hr_user(client):
    login(client, 'hr')
    hr_routes = [
        '/',
        '/hr/dashboard',
        '/hr/attendance',
        '/hr/tasks',
        '/hr/employees',
        '/hr/employees/1',
        '/hr/documents',
        '/hr/onboarding',
        '/hr/leaves',
        '/hr/exits',
        '/hr/requests',
        '/hr/performance',
        '/hr/payrolls',
        '/hr/recruitments',
        '/hr/assets',
    ]
    for route in hr_routes:
        res = client.get(route, follow_redirects=True)
        assert res.status_code == 200, f"HR route {route} failed with status {res.status_code}"

def test_finance_routes_as_accounts_user(client):
    login(client, 'accounts')
    fin_routes = [
        '/',
        '/finance/',
        '/finance/commissions/new',
        '/finance/expenses/new',
    ]
    for route in fin_routes:
        res = client.get(route, follow_redirects=True)
        assert res.status_code == 200, f"Finance route {route} failed with status {res.status_code}"

def test_marketing_routes_as_marketing_user(client):
    login(client, 'marketing')
    mkt_routes = [
        '/',
        '/marketing/',
        '/marketing/campaigns',
        '/marketing/campaigns/create',
        '/marketing/attribution',
    ]
    for route in mkt_routes:
        res = client.get(route, follow_redirects=True)
        assert res.status_code == 200, f"Marketing route {route} failed with status {res.status_code}"

def test_it_routes_as_it_user(client):
    login(client, 'it')
    it_routes = [
        '/',
        '/it/',
        '/it/assets',
        '/it/assets/create',
        '/it/tickets',
        '/it/tickets/create',
        '/it/infrastructure',
    ]
    for route in it_routes:
        res = client.get(route, follow_redirects=True)
        assert res.status_code == 200, f"IT route {route} failed with status {res.status_code}"

    # Test registering real estate IT equipment
    asset_res = client.post('/it/assets/create', data={
        'asset_name': 'Bosch GLM 50 C Bluetooth Laser Distance Meter',
        'category': 'Field Survey (Laser Disto Meter)',
        'serial_number': 'BSH-GLM-9912',
        'allocated_to_id': '',
        'purchase_cost': '8500',
        'notes': 'Allocated for site carpet area verification'
    }, follow_redirects=True)
    assert asset_res.status_code == 200
    assert b"AST-IT-" in asset_res.data
    assert b"Bosch GLM 50 C" in asset_res.data

    # Test logging real estate IT support ticket
    tkt_res = client.post('/it/tickets/create', data={
        'title': '99acres webhook sync delayed by 15 mins',
        'category': 'Portal Lead Sync',
        'priority': 'High',
        'requested_by_id': '1',
        'description': 'Leads coming from 99acres campaign are taking 15 minutes to reflect in CRM'
    }, follow_redirects=True)
    assert tkt_res.status_code == 200
    assert b"TKT-" in tkt_res.data
    assert b"99acres webhook sync delayed" in tkt_res.data

def test_sourcing_and_shortlisting_workflows(client):
    login(client, 'admin')

    # Test create sourcing assignment
    res = client.post('/sourcing/assign', data={
        'title': 'Test Sourcing Office SG Highway',
        'sourcing_type': 'Targeted Area',
        'locality': 'SG Highway',
        'category': 'Commercial',
        'min_area_sqft': '1000',
        'max_area_sqft': '3000',
        'target_budget': '50000',
        'assigned_to_id': '1',
        'priority': 'High',
        'instructions': 'Need corner unit'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Test Sourcing Office SG Highway" in res.data or b"SRC-" in res.data

    # Test GPS Ping
    gps_res = client.post('/gps/ping', data={
        'latitude': '23.0300',
        'longitude': '72.5800',
        'location_name': 'Ahmedabad Test Point',
        'tracking_type': 'Travel Ping'
    }, follow_redirects=True)
    assert gps_res.status_code == 200

def test_hr_workflows_and_verification(client):
    login(client, 'hr')

    # 1. Upload employee document
    doc_res = client.post('/hr/documents/upload', data={
        'user_id': '1',
        'category': 'Identity Proof',
        'document_name': 'Test Passport Document',
        'notes': 'Test passport copy for verification'
    }, follow_redirects=True)
    assert doc_res.status_code == 200
    assert b"Test Passport Document" in doc_res.data or b"recorded" in doc_res.data

    # 2. Check document verification action
    from app.models import EmployeeDocument
    doc = EmployeeDocument.query.filter_by(document_name='Test Passport Document').first()
    assert doc is not None

    v_res = client.post(f'/hr/documents/{doc.id}/verify', follow_redirects=True)
    assert v_res.status_code == 200
    assert b"verified successfully" in v_res.data or doc.status == 'Verified'

    # 3. Raise HR Service Request
    req_res = client.post('/hr/requests/new', data={
        'request_type': 'Bonafide Certificate',
        'details': 'Need bank proof certificate'
    }, follow_redirects=True)
    assert req_res.status_code == 200
    assert b"Bonafide Certificate" in req_res.data or b"submitted" in req_res.data

def test_department_gps_checkin_and_authorized_access(client):
    from app.models import Attendance, GPSTrackingLog
    from datetime import date

    # 1. Sales employee checks in with GPS coordinates
    login(client, 'sales')
    res_in = client.post('/hr/attendance/check-in', data={
        'latitude': '23.0338',
        'longitude': '72.5850',
        'location_name': 'S.G. Highway Commercial Complex',
        'work_mode': 'Office',
        'notes': 'Sales morning check-in'
    }, follow_redirects=True)
    assert res_in.status_code == 200

    # Verify Attendance record has location and coordinates
    sales_att = Attendance.query.filter_by(attendance_date=date.today()).first()
    assert sales_att is not None
    assert sales_att.latitude == pytest.approx(23.0338, 0.001)
    assert sales_att.longitude == pytest.approx(72.5850, 0.001)
    assert "S.G. Highway" in sales_att.check_in_location

    # Verify GPS Tracking Log was automatically recorded
    gps_log = GPSTrackingLog.query.filter_by(location_name='S.G. Highway Commercial Complex').first()
    assert gps_log is not None
    assert "Check-In" in gps_log.tracking_type

    # 2. Field Agent checks in with field coordinates
    login(client, 'field')
    res_field = client.post('/hr/attendance/check-in', data={
        'latitude': '23.0450',
        'longitude': '72.5120',
        'location_name': 'Bodakdev Inspection Site',
        'work_mode': 'Field',
        'notes': 'Site inspection'
    }, follow_redirects=True)
    assert res_field.status_code == 200

    # 3. Sales employee checks out
    login(client, 'sales')
    res_out = client.post('/hr/attendance/check-out', data={
        'latitude': '23.0339',
        'longitude': '72.5852',
        'location_name': 'S.G. Highway Complex Exit'
    }, follow_redirects=True)
    assert res_out.status_code == 200

    # 4. Authorized Admin / HR views departmental check-ins and GPS radar
    login(client, 'admin')
    res_hr = client.get('/hr/attendance?department=Sales')
    assert res_hr.status_code == 200
    assert b"S.G. Highway" in res_hr.data

    res_gps = client.get('/gps/?department=Sales')
    assert res_gps.status_code == 200
    assert b"S.G. Highway" in res_gps.data


