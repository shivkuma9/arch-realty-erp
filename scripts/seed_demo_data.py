import os
import sys
from datetime import datetime, date, time, timedelta, timezone
from decimal import Decimal

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions import db
from app.models import (
    User, Roles, Lead, Client, Property, Owner, Mandate, Requirement,
    SiteVisit, Deal, DealStageHistory, Brokerage, Invoice, Payment, Expense,
    Task, FollowUp, Activity, Notification, Setting, AuditLog,
    Attendance, LeaveRequest, EmployeeTarget, Payroll, Recruitment, Asset, Document
)

def seed(app=None):
    if app is None:
        app = create_app()
    with app.app_context():
        print("Initializing database tables...")
        db.create_all()

        # Check if already seeded
        if User.query.filter_by(username='admin').first():
            print("Database already contains users. Skipping.")
            return

        print("Seeding demo users across all roles and departments...")
        users_data = [
            ('director', 'director@archrealty.example', 'Bhavin Patel', Roles.DIRECTOR, 'Management', 'Managing Director', 'EMP-001', Decimal('150000.00'), 'Office'),
            ('admin', 'admin@archrealty.example', 'System Administrator', Roles.SUPER_ADMIN, 'Management', 'System Administrator', 'EMP-002', Decimal('80000.00'), 'Office'),
            ('manager', 'manager@archrealty.example', 'Rajesh Joshi', Roles.MANAGER, 'Sales', 'Senior Branch Manager', 'EMP-003', Decimal('75000.00'), 'Office'),
            ('sales_rahul', 'rahul@archrealty.example', 'Rahul Sharma', Roles.SALES_EXEC, 'Sales', 'Senior Sales Executive', 'EMP-004', Decimal('45000.00'), 'Office'),
            ('sales_priya', 'priya@archrealty.example', 'Priya Desai', Roles.SALES_EXEC, 'Sales', 'Sales Executive', 'EMP-005', Decimal('40000.00'), 'Office'),
            ('field_amit', 'amit@archrealty.example', 'Amit Varma', Roles.FIELD_EXEC, 'Field Operations', 'Field Executive', 'EMP-006', Decimal('32000.00'), 'Field'),
            ('accounts_neha', 'neha@archrealty.example', 'Neha Shah', Roles.ACCOUNTS_EXEC, 'Finance', 'Accounts Officer', 'EMP-007', Decimal('42000.00'), 'Office'),
            ('hr_anita', 'anita@archrealty.example', 'Anita Mehta', Roles.HR_OPS, 'Human Resources', 'HR Operations Manager', 'EMP-008', Decimal('50000.00'), 'Office')
        ]

        user_objs = {}
        for uname, email, fname, role, dept, desig, emp_code, salary, mode in users_data:
            u = User(
                username=uname,
                email=email,
                full_name=fname,
                role=role,
                department=dept,
                designation=desig,
                employee_code=emp_code,
                monthly_salary=salary,
                work_mode=mode,
                employment_type='Full-Time',
                joining_date=date.today() - timedelta(days=365),
                is_active=True
            )
            u.set_password(os.environ.get('DEMO_PASSWORD', 'admin123'))
            db.session.add(u)
            user_objs[uname] = u

        db.session.commit()

        print("Seeding property owners & mandates...")
        owner1 = Owner(
            owner_code="OWN-AHM-0001",
            name="Mr. Dilipbhai Shah",
            phone="+91 98250 11223",
            email="dilip.shah@example.com",
            address="Near Iscon Cross Road, SG Highway, Ahmedabad",
            preferred_contact_method="Phone",
            pan_or_id="ABCPS1234F",
            notes="DEMO DATA: High net worth landlord owning multiple corporate floors on SG Highway."
        )
        owner2 = Owner(
            owner_code="OWN-AHM-0002",
            name="Panchratna Builders LLP",
            phone="+91 98980 99887",
            email="panchratna.builders@example.com",
            address="Prahlad Nagar Corporate Road, Ahmedabad",
            preferred_contact_method="WhatsApp",
            pan_or_id="AAACP9988Q",
            notes="DEMO DATA: Prominent developer of retail spaces and residential towers in Western Ahmedabad."
        )
        db.session.add_all([owner1, owner2])
        db.session.commit()

        print("Seeding Ahmedabad property listings...")
        p1 = Property(
            property_code="PROP-AHM-00001",
            title="Grade-A Furnished Corporate Office - Mondeal Heights",
            category="Commercial",
            transaction_type="Rent",
            locality="SG Highway",
            address="11th Floor, Tower B, Mondeal Heights, SG Highway, Ahmedabad",
            city="Ahmedabad",
            latitude=23.0298,
            longitude=72.5076,
            carpet_area=Decimal('2850.00'),
            builtup_area=Decimal('3900.00'),
            rent_price=Decimal('185000.00'),
            security_deposit=Decimal('555000.00'),
            brokerage_terms="1 Month Rent",
            furnishing="Fully Furnished",
            amenities="Central AC, 4 Car Parks, Cafeteria, High-speed Elevators, 100% DG Backup",
            floors="11th Floor / 17 Floors",
            availability_status="Available",
            owner_id=owner1.id,
            assigned_to_id=user_objs['sales_rahul'].id,
            description="DEMO DATA: Premium plug-and-play corporate office space overlooking SG Highway. 45 workstations, 3 manager cabins, 1 conference room."
        )

        p2 = Property(
            property_code="PROP-AHM-00002",
            title="Prime High-Street Retail Showroom - Sindhu Bhavan Road",
            category="Commercial",
            transaction_type="Sale",
            locality="Sindhu Bhavan Road",
            address="Ground Floor, Titanium Business Park, Sindhu Bhavan Road, Bodakdev",
            city="Ahmedabad",
            latitude=23.0421,
            longitude=72.5115,
            carpet_area=Decimal('4200.00'),
            builtup_area=Decimal('5800.00'),
            sale_price=Decimal('75000000.00'),
            brokerage_terms="2% Sale Consideration",
            furnishing="Bare Shell",
            amenities="Main Road Facing, 60 Ft Frontage, Dedicated Parking",
            floors="Ground & Mezzanine",
            availability_status="Available",
            owner_id=owner2.id,
            assigned_to_id=user_objs['sales_rahul'].id,
            description="DEMO DATA: Iconic retail frontage on Ahmedabad's most prestigious commercial avenue. Ideal for luxury automotive, jewelry or flagship bank branch."
        )

        p3 = Property(
            property_code="PROP-AHM-00003",
            title="4 BHK Luxury Penthouse - Prahlad Nagar",
            category="Residential",
            transaction_type="Sale",
            locality="Prahlad Nagar",
            address="14th Floor, Riviera Elegance, Prahlad Nagar Garden Road, Ahmedabad",
            city="Ahmedabad",
            latitude=23.0135,
            longitude=72.5122,
            carpet_area=Decimal('3400.00'),
            builtup_area=Decimal('4600.00'),
            sale_price=Decimal('38500000.00'),
            brokerage_terms="2% Consideration",
            furnishing="Semi-Furnished",
            amenities="Private Terrace, Swimming Pool, Clubhouse, 3 Covered Car Parks",
            floors="14th & 15th Duplex",
            availability_status="Under Offer",
            owner_id=owner1.id,
            assigned_to_id=user_objs['sales_priya'].id,
            description="DEMO DATA: Ultra-luxury penthouse with panoramic skyline view of Prahlad Nagar garden."
        )
        db.session.add_all([p1, p2, p3])
        db.session.commit()

        # Mandates
        m1 = Mandate(
            mandate_code="MAN-AHM-0001",
            owner_id=owner1.id,
            property_id=p1.id,
            mandate_type="Exclusive",
            asking_rent=Decimal('185000.00'),
            start_date=date.today() - timedelta(days=30),
            expiry_date=date.today() + timedelta(days=150),
            terms="Exclusive marketing authorization for 6 months.",
            status="Active"
        )
        db.session.add(m1)
        db.session.commit()

        print("Seeding CRM Leads & Clients...")
        lead1 = Lead(
            lead_code="LEAD-AHM-00001",
            full_name="Mr. Vikram Singhania",
            company_name="Apex Logistics India Pvt Ltd",
            phone="+91 98240 55443",
            email="vikram@apexlogistics.example",
            source="Referral",
            property_category="Commercial",
            transaction_type="Rent",
            preferred_locations="SG Highway, Prahlad Nagar",
            budget_min=Decimal('150000.00'),
            budget_max=Decimal('220000.00'),
            area_min_sqft=Decimal('2500.00'),
            area_max_sqft=Decimal('3500.00'),
            assigned_to_id=user_objs['sales_rahul'].id,
            priority="High",
            status="Negotiation",
            notes="DEMO DATA: Expanding corporate branch from Mumbai. Urgent requirement by end of month."
        )

        lead2 = Lead(
            lead_code="LEAD-AHM-00002",
            full_name="Dr. Snehal Trivedi",
            phone="+91 98790 33221",
            email="dr.snehal@example.com",
            source="Website",
            property_category="Residential",
            transaction_type="Buy",
            preferred_locations="Prahlad Nagar, Bodakdev",
            budget_min=Decimal('30000000.00'),
            budget_max=Decimal('42000000.00'),
            area_min_sqft=Decimal('3000.00'),
            area_max_sqft=Decimal('4000.00'),
            assigned_to_id=user_objs['sales_priya'].id,
            priority="Medium",
            status="Site Visit",
            notes="DEMO DATA: High-end medical practitioner seeking ready luxury flat."
        )
        db.session.add_all([lead1, lead2])
        db.session.commit()

        # Clients
        client1 = Client(
            client_code="CLI-AHM-00001",
            name="Zydex Chemicals Corp",
            client_type="Corporate",
            company_name="Zydex Chemicals Corporation",
            gst_number="24AAACZ1122K1Z9",
            pan_number="AAACZ1122K",
            phone="+91 79 2685 1100",
            email="procurement@zydexcorp.example",
            address="Zydex House, Near Sola Bridge, SG Highway, Ahmedabad",
            preferred_locations="SG Highway, Sindhu Bhavan Road",
            budget_range="₹ 5 Cr - ₹ 10 Cr",
            assigned_rm_id=user_objs['sales_rahul'].id,
            notes="DEMO DATA: Longstanding corporate relationship client."
        )
        db.session.add(client1)
        db.session.commit()

        # Client Requirement
        req1 = Requirement(
            client_id=client1.id,
            category="Commercial",
            transaction_type="Sale",
            budget_min=Decimal('60000000.00'),
            budget_max=Decimal('85000000.00'),
            area_min=Decimal('3500.00'),
            area_max=Decimal('5000.00'),
            preferred_locations="Sindhu Bhavan Road, Bodakdev",
            furnishing="Bare Shell",
            possession_timeline="Within 60 Days",
            status="Active",
            notes="DEMO DATA: Looking to acquire flagship commercial retail showroom."
        )
        db.session.add(req1)
        db.session.commit()

        print("Seeding Deals, Brokerage & Collections...")
        deal1 = Deal(
            deal_code="DEAL-AHM-00001",
            title="Commercial Lease - Mondeal Heights Office",
            client_id=client1.id,
            property_id=p1.id,
            lead_id=lead1.id,
            owner_user_id=user_objs['sales_rahul'].id,
            stage="Closed Won",
            expected_value=Decimal('185000.00'),
            final_value=Decimal('180000.00'),
            expected_closing_date=date.today() - timedelta(days=10),
            actual_closing_date=date.today() - timedelta(days=5),
            agreement_status="Signed",
            notes="DEMO DATA: Successfully finalized 3-year commercial lease agreement."
        )
        db.session.add(deal1)
        db.session.commit()

        # Deal Stage History
        sh1 = DealStageHistory(deal_id=deal1.id, previous_stage="Agreement", new_stage="Closed Won", changed_by_id=user_objs['sales_rahul'].id, comments="Agreements executed by all parties.")
        db.session.add(sh1)

        # Brokerage calculation (1 month rent from client, 1 month rent from owner = ₹ 3,60,000)
        brok1 = Brokerage(
            deal_id=deal1.id,
            rule_type="RentMonths",
            client_percentage=Decimal('1.00'),
            owner_percentage=Decimal('1.00'),
            expected_amount=Decimal('360000.00'),
            invoiced_amount=Decimal('360000.00'),
            received_amount=Decimal('180000.00'),
            outstanding_amount=Decimal('180000.00'),
            status="Partially Paid"
        )
        db.session.add(brok1)
        db.session.commit()

        # Invoice
        inv1 = Invoice(
            invoice_number="INV-ARCH-2026-0001",
            brokerage_id=brok1.id,
            party_type="Client",
            amount=Decimal('180000.00'),
            tax_amount=Decimal('32400.00'),
            total_amount=Decimal('212400.00'),
            invoice_date=date.today() - timedelta(days=4),
            due_date=date.today() + timedelta(days=10),
            status="Paid",
            notes="DEMO DATA: Client side brokerage fee."
        )
        db.session.add(inv1)

        # Payment
        pay1 = Payment(
            receipt_number="REC-ARCH-00001",
            brokerage_id=brok1.id,
            invoice_id=inv1.id,
            amount=Decimal('180000.00'),
            payment_date=date.today() - timedelta(days=2),
            payment_mode="Bank Transfer",
            transaction_ref="HDFC202604018899",
            recorded_by_id=user_objs['accounts_neha'].id,
            notes="DEMO DATA: Received via RTGS from Zydex Chemicals."
        )
        db.session.add(pay1)

        # Operating Expense
        exp1 = Expense(
            title="Digital Portal Listings & Hoarding at Sindhu Bhavan",
            category="Marketing",
            amount=Decimal('35000.00'),
            expense_date=date.today() - timedelta(days=15),
            paid_to="Apex Media Ahmedabad",
            payment_mode="Bank Transfer",
            recorded_by_id=user_objs['accounts_neha'].id,
            notes="DEMO DATA: Monthly promotional marketing campaign."
        )
        db.session.add(exp1)

        print("Seeding Site Visits & Tasks...")
        visit1 = SiteVisit(
            visit_code="VIS-AHM-00001",
            property_id=p2.id,
            client_id=client1.id,
            assigned_employee_id=user_objs['field_amit'].id,
            visit_date=date.today() + timedelta(days=2),
            visit_time=time(11, 30),
            status="Confirmed",
            executive_notes="DEMO DATA: Client technical team visiting for showroom measurements."
        )
        db.session.add(visit1)

        task1 = Task(
            title="Collect NOC from Society Office for Mondeal Heights",
            description="DEMO DATA: Collect maintenance clear NOC and parking allocation letters.",
            assigned_to_id=user_objs['field_amit'].id,
            created_by_id=user_objs['manager'].id,
            priority="High",
            due_date=date.today() + timedelta(days=1),
            status="Pending",
            property_id=p1.id,
            deal_id=deal1.id
        )
        db.session.add(task1)

        # In-app notification
        notif1 = Notification(
            user_id=user_objs['director'].id,
            title="Deal Closed Won: Mondeal Heights Office",
            message="Sales Exec Rahul closed commercial deal DEAL-AHM-00001 for ₹ 1.80L/mo.",
            link=f"/deals/{deal1.id}",
            category="Deal"
        )
        db.session.add(notif1)

        print("Seeding HR records (Attendance, Leaves, Targets, Payroll, Recruitment, Assets)...")
        # Attendance records
        today = date.today()
        for idx, u in enumerate([user_objs['sales_rahul'], user_objs['sales_priya'], user_objs['field_amit'], user_objs['accounts_neha']]):
            att = Attendance(
                user_id=u.id,
                attendance_date=today,
                check_in_time=time(9, 30),
                check_out_time=time(18, 30),
                working_hours=Decimal('9.00'),
                work_mode=u.work_mode,
                status='Present',
                notes='Normal punch-in'
            )
            db.session.add(att)

        # Leave Request
        lr1 = LeaveRequest(
            user_id=user_objs['sales_priya'].id,
            leave_type='Casual Leave',
            start_date=today + timedelta(days=7),
            end_date=today + timedelta(days=8),
            reason='Family celebration in Surat',
            status='Approved',
            reviewed_by_id=user_objs['director'].id,
            review_remarks='Approved. Ensure follow-ups are reassigned.'
        )
        db.session.add(lr1)

        # Employee Target / KPI
        et1 = EmployeeTarget(
            user_id=user_objs['sales_rahul'].id,
            month_year=today.strftime('%B %Y'),
            working_days=25,
            call_target=500,
            actual_calls=320,
            lead_target=20,
            actual_leads=14,
            site_visit_target=12,
            actual_site_visits=8,
            revenue_target=Decimal('500000.00'),
            actual_revenue=Decimal('360000.00'),
            notes='On track to exceed target this month.'
        )
        db.session.add(et1)

        # Payroll Register
        pay_reg = Payroll(
            payroll_code=f"PAY-{today.strftime('%Y%m')}-001",
            payroll_month=today.strftime('%B %Y'),
            user_id=user_objs['sales_rahul'].id,
            basic_salary=Decimal('45000.00'),
            allowances=Decimal('5000.00'),
            incentives=Decimal('15000.00'),
            deductions=Decimal('2500.00'),
            net_salary=Decimal('62500.00'),
            status='Approved',
            payment_date=today,
            payment_mode='Bank Transfer'
        )
        db.session.add(pay_reg)

        # Recruitment Candidate
        rec1 = Recruitment(
            recruitment_code='REC-2026-001',
            candidate_name='Hardik Dave',
            position='Business Development Executive',
            department='Business Development',
            phone='+91 97230 44556',
            email='hardik.dave@example.com',
            source='LinkedIn',
            stage='Technical Interview',
            interview_date=datetime.now(timezone.utc) + timedelta(days=3),
            hiring_manager_id=user_objs['manager'].id,
            status='Active',
            notes='Strong 3-year background in commercial leasing in Western Ahmedabad.'
        )
        db.session.add(rec1)

        # Office Asset
        ast1 = Asset(
            asset_code='AST-AHM-001',
            asset_name='Laser Distance Measurer (Bosch GLM 50C)',
            category='Field Equipment',
            serial_number='BOSCH-GLM-99881',
            allocated_to_id=user_objs['field_amit'].id,
            allocation_date=today - timedelta(days=60),
            purchase_date=today - timedelta(days=90),
            purchase_cost=Decimal('8500.00'),
            status='Allocated',
            notes='Issued for on-site measurement & carpet verification.'
        )
        ast2 = Asset(
            asset_code='AST-AHM-002',
            asset_name='ThinkPad E14 Gen 5 Laptop',
            category='IT Hardware',
            serial_number='PF-38827-IND',
            allocated_to_id=user_objs['sales_rahul'].id,
            allocation_date=today - timedelta(days=120),
            purchase_date=today - timedelta(days=150),
            purchase_cost=Decimal('62000.00'),
            status='Allocated',
            notes='Sales workstation laptop with ERP access.'
        )
        db.session.add_all([ast1, ast2])

        # Document
        doc1 = Document(
            title='ARCH Realty Standard Commercial Lease Agreement Template',
            category='Agreement',
            filename='ARCH_Standard_Lease_Template_2026.pdf',
            file_size_bytes=425000,
            mime_type='application/pdf',
            uploaded_by_id=user_objs['admin'].id,
            property_id=p1.id,
            deal_id=deal1.id,
            client_id=client1.id
        )
        db.session.add(doc1)

        # Audit Log
        audit1 = AuditLog(
            user_id=user_objs['admin'].id,
            action='SYSTEM_INIT',
            entity_type='System',
            entity_id=1,
            ip_address='127.0.0.1',
            details='Initial ERP database created and demo dataset seeded successfully.'
        )
        db.session.add(audit1)

        db.session.commit()
        print("Demo seed data completed successfully across ALL departments!")

if __name__ == '__main__':
    seed()
