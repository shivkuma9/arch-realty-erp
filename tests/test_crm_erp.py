import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from decimal import Decimal
from datetime import date, time
from app import create_app
from app.extensions import db
from app.models import (
    User, Roles, Lead, Client, Property, Owner, Mandate, Requirement,
    SiteVisit, Deal, Brokerage, Payment
)
from app.services.matching_service import score_property_match, detect_duplicate_lead
from app.services.finance_service import calculate_brokerage_for_deal, record_brokerage_payment
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Create standard test users
        admin = User(username='admin', email='admin@test.example', full_name='Admin Test', role=Roles.SUPER_ADMIN)
        admin.set_password('pass123')
        
        director = User(username='director', email='director@test.example', full_name='Director Test', role=Roles.DIRECTOR)
        director.set_password('pass123')

        sales1 = User(username='sales1', email='sales1@test.example', full_name='Sales One', role=Roles.SALES_EXEC)
        sales1.set_password('pass123')

        sales2 = User(username='sales2', email='sales2@test.example', full_name='Sales Two', role=Roles.SALES_EXEC)
        sales2.set_password('pass123')

        accounts = User(username='accounts', email='accounts@test.example', full_name='Accounts Exec', role=Roles.ACCOUNTS_EXEC)
        accounts.set_password('pass123')

        db.session.add_all([admin, director, sales1, sales2, accounts])
        db.session.commit()

        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def login(client, username, password='pass123'):
    return client.post('/auth/login', data={'username': username, 'password': password}, follow_redirects=True)

# 1. Test Authentication
def test_login_success_and_failure(client):
    # Failure
    res_fail = client.post('/auth/login', data={'username': 'director', 'password': 'wrongpassword'}, follow_redirects=True)
    assert b'Invalid username/email or password' in res_fail.data

    # Success
    res_ok = login(client, 'director')
    assert b'Executive Dashboard' in res_ok.data

# 2. Test Authorization & Role Access
def test_role_based_access(client):
    # Unauthenticated redirect to login
    res_unauth = client.get('/finance/', follow_redirects=True)
    assert b'Please log in to access this page' in res_unauth.data

    # Sales executive restricted from financial ledger
    login(client, 'sales1')
    res_forbidden = client.get('/finance/')
    assert res_forbidden.status_code == 403

    # Accounts executive allowed into finance
    client.get('/auth/logout')
    login(client, 'accounts')
    res_acc = client.get('/finance/')
    assert res_acc.status_code == 200
    assert b'Brokerage &amp; Financial Accounting' in res_acc.data or b'Brokerage & Financial Accounting' in res_acc.data

# 3. Test Lead Scoping (Sales rep cannot see another's private leads)
def test_sales_lead_scoping(client, app):
    with app.app_context():
        u1 = User.query.filter_by(username='sales1').first()
        u2 = User.query.filter_by(username='sales2').first()
        
        l1 = Lead(lead_code='LEAD-T-01', full_name='Lead for Sales 1', phone='9999900001', assigned_to_id=u1.id)
        l2 = Lead(lead_code='LEAD-T-02', full_name='Lead for Sales 2', phone='9999900002', assigned_to_id=u2.id)
        db.session.add_all([l1, l2])
        db.session.commit()
        l2_id = l2.id

    # Log in as sales1
    login(client, 'sales1')
    res_list = client.get('/crm/leads')
    assert b'Lead for Sales 1' in res_list.data
    assert b'Lead for Sales 2' not in res_list.data

    # Direct detail access forbidden
    res_detail = client.get(f'/crm/leads/{l2_id}')
    assert res_detail.status_code == 403

# 4. Test Duplicate Lead Detection
def test_duplicate_lead_detection(app):
    with app.app_context():
        l1 = Lead(lead_code='LEAD-T-10', full_name='John Doe', phone='9876543210', email='john@example.com')
        db.session.add(l1)
        db.session.commit()

        is_dup, msg = detect_duplicate_lead(phone='9876543210')
        assert is_dup is True
        assert 'already exists' in msg

        is_dup_em, msg_em = detect_duplicate_lead(phone='9111111111', email='john@example.com')
        assert is_dup_em is True
        assert 'email' in msg_em

        is_not_dup, _ = detect_duplicate_lead(phone='9222222222', email='unique@example.com')
        assert is_not_dup is False

# 5. Test Property Matching Engine Scoring
def test_property_matching_scoring(app):
    with app.app_context():
        client = Client(client_code='CLI-T-01', name='Test Buyer', phone='9876500000')
        db.session.add(client)
        db.session.commit()

        req = Requirement(
            client_id=client.id,
            category='Commercial',
            transaction_type='Rent',
            budget_max=Decimal('200000.00'),
            preferred_locations='SG Highway, Prahlad Nagar',
            area_min=Decimal('2000.00'),
            status='Active'
        )
        prop_good = Property(
            property_code='PROP-T-01',
            title='SG Highway Office',
            category='Commercial',
            transaction_type='Rent',
            locality='SG Highway',
            address='101 Corporate House',
            rent_price=Decimal('180000.00'),
            carpet_area=Decimal('2200.00')
        )
        prop_bad = Property(
            property_code='PROP-T-02',
            title='Agricultural Land Sanand',
            category='Land',
            transaction_type='Sale',
            locality='Sanand',
            address='Survey No 50',
            sale_price=Decimal('50000000.00'),
            carpet_area=Decimal('50000.00')
        )
        db.session.add_all([req, prop_good, prop_bad])
        db.session.commit()

        score_good, reasons_good, mismatches_good = score_property_match(req, prop_good)
        score_bad, reasons_bad, mismatches_bad = score_property_match(req, prop_bad)

        assert score_good >= 80
        assert any('Category matches' in r for r in reasons_good)
        assert score_bad < 30
        assert any('Category mismatch' in m for m in mismatches_bad)

# 6. Test Brokerage Calculation and Partial Payments
def test_brokerage_and_payment_records(app):
    with app.app_context():
        director = User.query.filter_by(username='director').first()
        client = Client(client_code='CLI-T-02', name='Deals Client', phone='9800000000')
        prop = Property(property_code='PROP-T-03', title='Office Space', category='Commercial', transaction_type='Rent', locality='Bodakdev', address='Test')
        db.session.add_all([client, prop])
        db.session.commit()

        deal = Deal(
            deal_code='DEAL-T-01',
            title='Closed Deal',
            client_id=client.id,
            property_id=prop.id,
            owner_user_id=director.id,
            stage='Closed Won',
            final_value=Decimal('100000.00')
        )
        db.session.add(deal)
        db.session.commit()

        # Rent months rule (1 month client + 1 month owner = 200,000)
        brok = calculate_brokerage_for_deal(deal, client_percent=1.0, owner_percent=1.0, rule_type='RentMonths')
        assert brok.expected_amount == Decimal('200000.00')
        assert brok.outstanding_amount == Decimal('200000.00')
        assert brok.status == 'Pending'

        # Record partial payment of 100,000
        pay = record_brokerage_payment(
            brokerage_id=brok.id,
            amount=Decimal('100000.00'),
            payment_date=date.today(),
            payment_mode='Bank Transfer',
            transaction_ref='TXN-TEST-1234',
            recorded_by_id=director.id
        )
        assert pay.receipt_number.startswith('REC-ARCH-')
        assert brok.received_amount == Decimal('100000.00')
        assert brok.outstanding_amount == Decimal('100000.00')
        assert brok.status == 'Partially Paid'

# 7. Test CSV Exports Respect Permissions
def test_export_leads_csv(client, app):
    with app.app_context():
        u1 = User.query.filter_by(username='sales1').first()
        l = Lead(lead_code='LEAD-EXP-01', full_name='Export Lead Test', phone='9999988888', assigned_to_id=u1.id)
        db.session.add(l)
        db.session.commit()

    login(client, 'sales1')
    res = client.get('/crm/leads/export-csv')
    assert res.status_code == 200
    assert b'Export Lead Test' in res.data
    assert b'LEAD-EXP-01' in res.data
