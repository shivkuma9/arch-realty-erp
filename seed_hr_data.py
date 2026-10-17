import os
from datetime import datetime, date, timedelta, time, timezone
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import (
    User, Attendance, LeaveRequest, EmployeeDocument,
    EmployeeOnboarding, HRRequest, ExitClearance, PerformanceReview
)

app = create_app()

with app.app_context():
    print("Seeding rich HR data based on reference dashboard...")
    users = User.query.all()
    user_map = {u.full_name: u for u in users}

    # 1. Update User HR fields
    details_map = {
        'Bhavin Patel': {
            'emp_status': 'Active', 'dob': date(1982, 4, 15), 'gender': 'Male',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Board of Directors',
            'emergency_contact': '+91 98250 11000', 'permanent_address': 'B-402, Satellite Towers, Satellite, Ahmedabad'
        },
        'System Administrator': {
            'emp_status': 'Active', 'dob': date(1990, 8, 20), 'gender': 'Male',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Bhavin Patel',
            'emergency_contact': '+91 98250 11001', 'permanent_address': 'A-12, Prahaladnagar, Ahmedabad'
        },
        'Rajesh Joshi': {
            'emp_status': 'Active', 'dob': date(1986, 11, 5), 'gender': 'Male',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Bhavin Patel',
            'emergency_contact': '+91 98250 22001', 'permanent_address': '45, Shivalik Villa, Bodakdev, Ahmedabad'
        },
        'Rahul Sharma': {
            'emp_status': 'Active', 'dob': date(1993, 2, 14), 'gender': 'Male',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Rajesh Joshi',
            'emergency_contact': '+91 98250 22002', 'permanent_address': '72, Goyal Intercity, Drive-In Road, Ahmedabad'
        },
        'Priya Desai': {
            'emp_status': 'Active', 'dob': date(1995, 6, 28), 'gender': 'Female',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Rajesh Joshi',
            'emergency_contact': '+91 98250 22003', 'permanent_address': 'C-103, Safal Parivesh, Prahladnagar, Ahmedabad'
        },
        'Amit Varma': {
            'emp_status': 'Notice Period', 'dob': date(1994, 9, 10), 'gender': 'Male',
            'location': 'SG Highway Hub', 'reporting_manager': 'Rajesh Joshi',
            'emergency_contact': '+91 98250 33001', 'permanent_address': '14, Swagat Residency, Thaltej, Ahmedabad'
        },
        'Neha Shah': {
            'emp_status': 'Active', 'dob': date(1991, 1, 18), 'gender': 'Female',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Bhavin Patel',
            'emergency_contact': '+91 98250 44001', 'permanent_address': '502, Venus Atlantis, Anandnagar, Ahmedabad'
        },
        'Anita Mehta': {
            'emp_status': 'Active', 'dob': date(1989, 7, 23), 'gender': 'Female',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Bhavin Patel',
            'emergency_contact': '+91 98250 55001', 'permanent_address': '301, Gala Empire, Drive-In, Ahmedabad'
        },
        'Rahul Verma (Accounts)': {
            'emp_status': 'Active', 'dob': date(1994, 12, 1), 'gender': 'Male',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Neha Shah',
            'emergency_contact': '+91 98250 44002', 'permanent_address': '804, Titanium City Center, Satellite, Ahmedabad'
        },
        'Neha Sharma (HR)': {
            'emp_status': 'Active', 'dob': date(1996, 3, 30), 'gender': 'Female',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Anita Mehta',
            'emergency_contact': '+91 98250 55002', 'permanent_address': '102, Orchid Elegance, South Bopal, Ahmedabad'
        },
        'Rohit Verma': {
            'emp_status': 'Probation', 'dob': date(1997, 5, 12), 'gender': 'Male',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Bhavin Patel',
            'emergency_contact': '+91 98250 66001', 'permanent_address': '201, Maple County, Thaltej, Ahmedabad'
        },
        'Suresh Mehta': {
            'emp_status': 'Active', 'dob': date(1992, 10, 8), 'gender': 'Male',
            'location': 'Ahmedabad HQ', 'reporting_manager': 'Bhavin Patel',
            'emergency_contact': '+91 98250 77001', 'permanent_address': '403, Sun Westbank, Ashram Road, Ahmedabad'
        }
    }

    for name, data in details_map.items():
        user = user_map.get(name)
        if user:
            for k, v in data.items():
                setattr(user, k, v)
    db.session.commit()
    print("Updated employee profile attributes.")

    # 2. Seed Today's Attendance snapshot
    today = date.today()
    for user in users:
        att = Attendance.query.filter_by(user_id=user.id, attendance_date=today).first()
        if not att:
            if user.full_name in ['Amit Varma']:
                # On field
                att = Attendance(
                    user_id=user.id,
                    attendance_date=today,
                    check_in_time=time(9, 15),
                    check_out_time=None,
                    working_hours=Decimal('4.5'),
                    work_mode='Field',
                    status='Field Duty',
                    notes='Client property site inspection at SG Highway'
                )
            elif user.full_name in ['Rohit Verma']:
                # On leave
                att = Attendance(
                    user_id=user.id,
                    attendance_date=today,
                    check_in_time=None,
                    check_out_time=None,
                    working_hours=Decimal('0.0'),
                    work_mode='Office',
                    status='On Leave',
                    notes='Medical / Sick Leave'
                )
            else:
                att = Attendance(
                    user_id=user.id,
                    attendance_date=today,
                    check_in_time=time(9, 10 + (user.id % 20)),
                    check_out_time=None,
                    working_hours=Decimal('5.5'),
                    work_mode='Office',
                    status='Present',
                    notes='HQ biometric check-in'
                )
            db.session.add(att)
    db.session.commit()
    print("Attendance snapshot seeded for today.")

    # 3. Seed Compliance Documents
    if EmployeeDocument.query.count() == 0:
        docs = [
            {
                'doc_code': 'DOC-801',
                'user': user_map.get('Rahul Sharma'),
                'category': 'Identity Proof',
                'document_name': 'Aadhar & PAN Card Bundle',
                'status': 'Verified',
                'notes': 'Verified with DigiLocker QR'
            },
            {
                'doc_code': 'DOC-802',
                'user': user_map.get('Priya Desai'),
                'category': 'Address Proof',
                'document_name': 'Passport Copy',
                'status': 'Verified',
                'notes': 'Address confirmed in Satellite area'
            },
            {
                'doc_code': 'DOC-803',
                'user': user_map.get('Rohit Verma'),
                'category': 'Education Certificate',
                'document_name': 'MBA Degree in Digital Media',
                'status': 'Pending Review',
                'notes': 'Submitted during onboarding probation'
            },
            {
                'doc_code': 'DOC-804',
                'user': user_map.get('Suresh Mehta'),
                'category': 'Experience Letter',
                'document_name': 'Relieving Letter - Previous IT Firm',
                'status': 'Pending Review',
                'notes': 'HR verification email sent to previous employer'
            },
            {
                'doc_code': 'DOC-805',
                'user': user_map.get('Amit Varma'),
                'category': 'Bank Details',
                'document_name': 'Cancelled Cheque & Bank Statement',
                'status': 'Verified',
                'notes': 'HDFC Bank salary account verified'
            },
            {
                'doc_code': 'DOC-806',
                'user': user_map.get('Rahul Verma (Accounts)'),
                'category': 'Education Certificate',
                'document_name': 'CA Inter Marksheet & Certificates',
                'status': 'Pending Review',
                'notes': 'Original physical copies to be inspected'
            }
        ]
        for d in docs:
            if d['user']:
                emp_doc = EmployeeDocument(
                    doc_code=d['doc_code'],
                    user_id=d['user'].id,
                    category=d['category'],
                    document_name=d['document_name'],
                    upload_date=today - timedelta(days=2),
                    status=d['status'],
                    notes=d['notes']
                )
                db.session.add(emp_doc)
        db.session.commit()
        print("Employee compliance documents seeded.")

    # 4. Seed Onboarding Records
    if EmployeeOnboarding.query.count() == 0:
        onboardings = [
            {
                'user': user_map.get('Rohit Verma'),
                'role_title': 'Digital Marketing Executive',
                'joined_date': today - timedelta(days=15),
                'checklist_completed': 4,
                'total_checklist_items': 6,
                'status': 'In Progress',
                'notes': 'Email setup done, Biometric registered, Workstation assigned. Pending: Final HR orientation & KYC.'
            },
            {
                'user': user_map.get('Suresh Mehta'),
                'role_title': 'IT Support & Systems',
                'joined_date': today - timedelta(days=45),
                'checklist_completed': 6,
                'total_checklist_items': 6,
                'status': 'Completed',
                'notes': 'All onboarding checkpoints completed successfully.'
            }
        ]
        for o in onboardings:
            if o['user']:
                ob = EmployeeOnboarding(
                    user_id=o['user'].id,
                    role_title=o['role_title'],
                    joined_date=o['joined_date'],
                    checklist_completed=o['checklist_completed'],
                    total_checklist_items=o['total_checklist_items'],
                    status=o['status'],
                    notes=o['notes']
                )
                db.session.add(ob)
        db.session.commit()
        print("Employee onboarding records seeded.")

    # 5. Seed Exit Clearances
    if ExitClearance.query.count() == 0:
        exits = [
            {
                'user': user_map.get('Amit Varma'),
                'resignation_date': today - timedelta(days=10),
                'last_working_day': today + timedelta(days=20),
                'clearance_progress': '3 / 7 Handover Steps Done',
                'status': 'Notice Period',
                'notes': 'Knowledge transfer on SG Highway client portfolio in progress with Rajesh Joshi.'
            }
        ]
        for e in exits:
            if e['user']:
                ex = ExitClearance(
                    user_id=e['user'].id,
                    resignation_date=e['resignation_date'],
                    last_working_day=e['last_working_day'],
                    clearance_progress=e['clearance_progress'],
                    status=e['status'],
                    notes=e['notes']
                )
                db.session.add(ex)
        db.session.commit()
        print("Exit clearance records seeded.")

    # 6. Seed Internal HR Requests
    if HRRequest.query.count() == 0:
        hr_reqs = [
            {
                'request_code': 'REQ-HR-101',
                'user': user_map.get('Rahul Sharma'),
                'request_type': 'Address Update Request',
                'details': 'Relocated to Drive-In Road, updated electricity bill submitted for HR records.',
                'status': 'Pending'
            },
            {
                'request_code': 'REQ-HR-102',
                'user': user_map.get('Priya Desai'),
                'request_type': 'Bonafide Certificate',
                'details': 'Requires employment bonafide certificate for bank home loan verification.',
                'status': 'Pending'
            },
            {
                'request_code': 'REQ-HR-103',
                'user': user_map.get('Neha Shah'),
                'request_type': 'Salary Slip Request',
                'details': 'Requested signed 3-month salary slips for tax filing.',
                'status': 'Completed'
            }
        ]
        for r in hr_reqs:
            if r['user']:
                hr_req = HRRequest(
                    request_code=r['request_code'],
                    user_id=r['user'].id,
                    request_type=r['request_type'],
                    details=r['details'],
                    status=r['status']
                )
                db.session.add(hr_req)
        db.session.commit()
        print("HR internal requests seeded.")

    # 7. Seed Performance Reviews
    if PerformanceReview.query.count() == 0:
        reviews = [
            {
                'user': user_map.get('Rahul Sharma'),
                'reviewer': user_map.get('Rajesh Joshi'),
                'quarter': 'Q1 2026 Appraisal',
                'rating': '4.8 / 5.0',
                'status': 'Completed',
                'feedback': 'Exceeded mandate closure target by 125%. Exceptional client management in commercial segment.'
            },
            {
                'user': user_map.get('Priya Desai'),
                'reviewer': user_map.get('Rajesh Joshi'),
                'quarter': 'Q1 2026 Appraisal',
                'rating': '4.6 / 5.0',
                'status': 'Completed',
                'feedback': 'Consistent performance in retail leasing. High lead conversion ratio.'
            },
            {
                'user': user_map.get('Rohit Verma'),
                'reviewer': user_map.get('Bhavin Patel'),
                'quarter': 'Probation Review (Mid-Quarter)',
                'rating': '4.2 / 5.0',
                'status': 'In Review',
                'feedback': 'Good initiative on social media campaigns and lead generation via Google Ads.'
            }
        ]
        for rv in reviews:
            if rv['user'] and rv['reviewer']:
                p_rev = PerformanceReview(
                    user_id=rv['user'].id,
                    reviewer_id=rv['reviewer'].id,
                    quarter=rv['quarter'],
                    rating=rv['rating'],
                    status=rv['status'],
                    feedback=rv['feedback']
                )
                db.session.add(p_rev)
        db.session.commit()
        print("Performance reviews seeded.")

    # 8. Seed Leave Requests if needed
    pending_leaves = LeaveRequest.query.filter_by(status='Pending').count()
    if pending_leaves == 0:
        lr1 = LeaveRequest(
            user_id=user_map['Priya Desai'].id,
            leave_type='Casual Leave',
            start_date=today + timedelta(days=3),
            end_date=today + timedelta(days=4),
            reason='Family religious ceremony and travel out of station',
            status='Pending'
        )
        lr2 = LeaveRequest(
            user_id=user_map['Rohit Verma'].id,
            leave_type='Sick Leave',
            start_date=today,
            end_date=today + timedelta(days=1),
            reason='Viral fever and doctor consultation',
            status='Pending'
        )
        db.session.add_all([lr1, lr2])
        db.session.commit()
        print("Pending leave requests seeded.")

    print("HR seeding completed successfully!")
