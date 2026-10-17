from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, DecimalField, DateField, TimeField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, EqualTo, NumberRange
from datetime import date
from app.models import Roles

class LoginForm(FlaskForm):
    username = StringField('Username or Email', validators=[DataRequired(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Update Password')

class UserForm(FlaskForm):
    employee_code = StringField('Employee ID (e.g. EMP-001)', validators=[Optional(), Length(max=32)])
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=128)])
    phone = StringField('Phone', validators=[Optional(), Length(max=20)])
    role = SelectField('Role', choices=[(r, r) for r in Roles.ALL], validators=[DataRequired()])
    department = SelectField('Department', choices=[
        ('Business Development', 'Business Development'),
        ('Operations', 'Operations & Field Sales'),
        ('Sales', 'Sales & Closures'),
        ('Marketing', 'Marketing'),
        ('Human Resources', 'Human Resources'),
        ('Finance', 'Finance & Accounts'),
        ('Management', 'Management')
    ], default='Business Development')
    designation = StringField('Designation', default='Executive')
    employment_type = SelectField('Employment Type', choices=[('Full-Time', 'Full-Time'), ('Part-Time', 'Part-Time'), ('Contract', 'Contract'), ('Intern', 'Intern')])
    work_mode = SelectField('Work Mode', choices=[('Office', 'Office'), ('Field', 'Field'), ('Hybrid', 'Hybrid'), ('WFH', 'Work From Home')])
    joining_date = DateField('Date of Joining', validators=[Optional()])
    monthly_salary = DecimalField('Fixed Salary (₹/mo)', default=0, validators=[Optional()])
    password = PasswordField('Password', validators=[Optional(), Length(min=6)])
    is_active = BooleanField('Active Account', default=True)
    submit = SubmitField('Save User')

class LeadForm(FlaskForm):
    full_name = StringField('Lead / Client Name', validators=[DataRequired(), Length(max=128)])
    client_type = SelectField('Client Type', choices=[
        ('Company', 'Company'),
        ('Corporate', 'Corporate'),
        ('Individual', 'Individual'),
        ('Investor', 'Investor')
    ], default='Company')
    company_name = StringField('Company / Firm Name', validators=[Optional(), Length(max=128)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=128)])
    phone = StringField('Mobile Number', validators=[DataRequired(), Length(max=20)])
    whatsapp_number = StringField('WhatsApp Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    source = SelectField('Lead Source', choices=[
        ('Website', 'Website'),
        ('Google', 'Google Ads / SEO'),
        ('Property portal', 'Property Portal (MagicBricks/99Acres)'),
        ('Referral', 'Referral / Channel Partner'),
        ('Phone call', 'Direct Inbound Phone Call'),
        ('Walk-in', 'Office Walk-in'),
        ('Social media', 'Social Media / LinkedIn'),
        ('Advertisement', 'Hoarding / Offline Ad'),
        ('Other', 'Other')
    ])
    business_segment = SelectField('Business Segment', choices=[
        ('Commercial', 'Commercial (Offices/Corporate)'),
        ('Industrial', 'Industrial (Warehouses/Factories)'),
        ('Residential', 'Residential (Apartments/Villas)'),
        ('Land & Plot', 'Land & Commercial Plots'),
        ('Pre-Leased', 'Pre-Leased Investment Assets'),
        ('Retail', 'Retail (Shops/Showrooms)')
    ], default='Commercial')
    property_category = SelectField('Category', choices=[
        ('Office', 'Commercial Office Space'),
        ('Shop/Showroom', 'Retail Showroom / Shop'),
        ('Warehouse', 'Warehouse / Godown / Logistics'),
        ('Land/Plot', 'Industrial / Commercial Plot'),
        ('Pre-Leased', 'Pre-Leased Bank/Brand Asset'),
        ('Apartment', 'Residential Apartment / Flat'),
        ('Penthouse/Villa', 'Penthouse / Bungalow'),
        ('Hospital/School', 'Institutional (Hospital/School/Hotel)')
    ], default='Office')
    transaction_type = SelectField('Requirement Type', choices=[
        ('Rent', 'Rent / Lease'),
        ('Buy', 'Buy / Outright Purchase'),
        ('Lease', 'Long-term Pre-Lease')
    ])
    preferred_locations = StringField('Primary Target Locations in Ahmedabad', validators=[Optional(), Length(max=256)])
    alternative_locations = StringField('Alternative Locations', validators=[Optional(), Length(max=256)])
    budget_min = DecimalField('Min Budget (₹)', default=0, validators=[Optional()])
    budget_max = DecimalField('Max Budget (₹)', default=0, validators=[Optional()])
    area_min_sqft = DecimalField('Min Area (Sq.Ft)', default=0, validators=[Optional()])
    area_max_sqft = DecimalField('Max Area (Sq.Ft)', default=0, validators=[Optional()])
    priority = SelectField('Priority', choices=[('High', 'High Priority'), ('Medium', 'Medium Priority'), ('Low', 'Low Priority')])
    temperature = SelectField('Lead Temperature', choices=[('Hot', 'Hot (Immediate Closing)'), ('Warm', 'Warm (Exploring)'), ('Cold', 'Cold (Long Term)')])
    status = SelectField('Status', choices=[
        ('New', 'New Lead'),
        ('Contacted', 'Contacted / Pitch Made'),
        ('Qualified', 'Qualified Prospect'),
        ('Site Visit', 'Site Visit Planned/Done'),
        ('Negotiation', 'In Commercial Negotiation'),
        ('Won', 'Deal Won / Converted'),
        ('Lost', 'Lost / Dropped')
    ])
    assigned_to_id = SelectField('Assigned BDE / Executive', coerce=int, validators=[Optional()])
    lost_reason = StringField('Reason (if Lost)', validators=[Optional(), Length(max=256)])
    notes = TextAreaField('Detailed Client Requirements & Discussion Notes')
    submit = SubmitField('Save Lead')

class ClientForm(FlaskForm):
    name = StringField('Client Name / Key Contact', validators=[DataRequired(), Length(max=128)])
    client_type = SelectField('Client Type', choices=[
        ('Company', 'Company'),
        ('Corporate', 'Corporate'),
        ('Individual', 'Individual'),
        ('Investor', 'Investor')
    ], default='Company')
    company_name = StringField('Company Name (if applicable)', validators=[Optional(), Length(max=128)])
    designation = StringField('Designation', validators=[Optional(), Length(max=100)])
    gst_number = StringField('GSTIN', validators=[Optional(), Length(max=32)])
    pan_number = StringField('PAN', validators=[Optional(), Length(max=32)])
    phone = StringField('Mobile Number', validators=[DataRequired(), Length(max=20)])
    alternate_phone = StringField('Alternate Phone / Landline', validators=[Optional(), Length(max=20)])
    whatsapp_number = StringField('WhatsApp Number', validators=[Optional(), Length(max=20)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Billing / Permanent Address')
    city = StringField('City', default='Ahmedabad')
    preferred_locations = StringField('Target Localities', validators=[Optional(), Length(max=256)])
    budget_range = StringField('Budget Expectation', validators=[Optional(), Length(max=128)])
    assigned_rm_id = SelectField('Relationship Manager (BDE/Sales)', coerce=int, validators=[Optional()])
    notes = TextAreaField('Client Profile Notes')
    submit = SubmitField('Save Client')

class PropertyForm(FlaskForm):
    title = StringField('Listing Title', validators=[DataRequired(), Length(max=256)])
    category = SelectField('Property Category', choices=[
        ('Commercial', 'Commercial (Office/Showroom)'),
        ('Industrial', 'Industrial (Warehouse/PEB/GIDC)'),
        ('Land', 'Land & Commercial/Residential Plot'),
        ('Pre-Leased', 'Pre-Leased (Income Generating Asset)'),
        ('Residential', 'Residential (Flat/Villa/Penthouse)')
    ])
    sub_category = SelectField('Sub Category', choices=[
        ('Office', 'Corporate Office'),
        ('Shop/Showroom', 'Retail Shop / Showroom'),
        ('Warehouse', 'Warehouse / Godown'),
        ('Pre-Leased', 'Pre-Leased Brand Store/Bank'),
        ('Land/Plot', 'Commercial/Industrial Plot'),
        ('Apartment', 'Residential Apartment'),
        ('Penthouse', 'Penthouse / Bungalow'),
        ('Hospital/Hotel', 'Hospital / School / Hotel')
    ], default='Office')
    transaction_type = SelectField('Transaction', choices=[('Rent', 'For Rent / Lease'), ('Sale', 'For Outright Sale'), ('Lease', 'For Long-term Lease')])
    building_name = StringField('Building / Project / Park Name', validators=[Optional(), Length(max=128)])
    unit_number = StringField('Unit / Shop / Office No.', validators=[Optional(), Length(max=64)])
    locality = StringField('Locality / Micro-Market', validators=[DataRequired(), Length(max=128)])
    address = TextAreaField('Full Address / Landmark', validators=[DataRequired()])
    city = StringField('City', default='Ahmedabad')
    latitude = DecimalField('Latitude (Optional)', places=6, validators=[Optional()])
    longitude = DecimalField('Longitude (Optional)', places=6, validators=[Optional()])
    google_maps_link = StringField('Google Maps Link', validators=[Optional(), Length(max=256)])
    
    # Areas
    carpet_area = DecimalField('Carpet Area (Sq.Ft)', default=0, validators=[Optional()])
    builtup_area = DecimalField('Built-up Area (Sq.Ft)', default=0, validators=[Optional()])
    super_builtup_area = DecimalField('Super Built-up Area (Sq.Ft)', default=0, validators=[Optional()])
    plot_area_sqyd = DecimalField('Plot Area (Sq.Yds for Land)', default=0, validators=[Optional()])
    
    # Pricing
    sale_price = DecimalField('Sale Asking Price (₹)', default=0, validators=[Optional()])
    rent_price = DecimalField('Monthly Rent (₹)', default=0, validators=[Optional()])
    rate_per_sqft = DecimalField('Rate per Sq.Ft (₹)', default=0, validators=[Optional()])
    security_deposit = DecimalField('Security Deposit (₹)', default=0, validators=[Optional()])
    brokerage_terms = StringField('Brokerage Terms', default='1 Month Rent / 2% Sale Consideration')
    
    # Pre-Leased Fields
    is_pre_leased = BooleanField('Pre-Leased Asset')
    tenant_name = StringField('Tenant / Brand Name (e.g. HDFC Bank, Croma)', validators=[Optional(), Length(max=128)])
    tenant_business_type = StringField('Tenant Business Type (e.g. Bank, IT, Retail)', validators=[Optional(), Length(max=64)])
    monthly_rental_income = DecimalField('Current Monthly Rent Inflow (₹)', default=0, validators=[Optional()])
    roi_percentage = DecimalField('Expected Gross ROI (%)', places=2, default=0, validators=[Optional()])
    lock_in_period_months = IntegerField('Lock-in Period (Months)', default=0, validators=[Optional()])
    escalation_percentage = DecimalField('Rent Escalation %', places=2, default=0, validators=[Optional()])
    
    furnishing = SelectField('Furnishing Status', choices=[
        ('Unfurnished', 'Unfurnished / Bare'),
        ('Semi-Furnished', 'Semi-Furnished'),
        ('Fully Furnished', 'Fully Furnished (Plug & Play)'),
        ('Bare Shell', 'Warm / Bare Shell')
    ])
    construction_type = StringField('Construction Type (e.g. RCC, PEB, Tilt-Up)', validators=[Optional(), Length(max=64)])
    zone_type = StringField('Zone Type (e.g. Commercial, Industrial GIDC, R1/R2, Agri)', validators=[Optional(), Length(max=64)])
    amenities = StringField('Amenities (Comma-separated: Parking, Lift, 24x7 Security, Power Backup, etc.)', validators=[Optional(), Length(max=512)])
    floors = StringField('Floor Details', validators=[Optional(), Length(max=64)])
    availability_status = SelectField('Availability Status', choices=[
        ('Available', 'Available Now'),
        ('Under Offer', 'Under Offer / Hold'),
        ('Sold', 'Sold Out'),
        ('Rented', 'Rented Out')
    ])
    owner_id = SelectField('Property Owner', coerce=int, validators=[Optional()])
    assigned_to_id = SelectField('Assigned Executive', coerce=int, validators=[Optional()])
    description = TextAreaField('Public Listing Description')
    internal_notes = TextAreaField('Internal Confidential Notes')
    submit = SubmitField('Save Property')

class OwnerForm(FlaskForm):
    name = StringField('Owner Full Name', validators=[DataRequired(), Length(max=128)])
    phone = StringField('Mobile Number', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    address = TextAreaField('Permanent Address')
    preferred_contact_method = SelectField('Preferred Contact Mode', choices=[('Phone', 'Phone Call'), ('WhatsApp', 'WhatsApp'), ('Email', 'Email')])
    pan_or_id = StringField('PAN or Govt ID Reference', validators=[Optional(), Length(max=64)])
    notes = TextAreaField('Owner Background & Negotiation History')
    submit = SubmitField('Save Owner')

class MandateForm(FlaskForm):
    owner_id = SelectField('Property Owner', coerce=int, validators=[DataRequired()])
    property_id = SelectField('Select Property Listing', coerce=int, validators=[Optional()])
    mandate_type = SelectField('Mandate Exclusivity', choices=[('Exclusive', 'Sole / Exclusive Mandate'), ('Semi-Exclusive', 'Semi-Exclusive Mandate'), ('Open', 'Open / General Listing')])
    asking_price = DecimalField('Asking Sale Price (₹)', default=0, validators=[Optional()])
    asking_rent = DecimalField('Asking Monthly Rent (₹)', default=0, validators=[Optional()])
    start_date = DateField('Mandate Start Date', validators=[DataRequired()])
    expiry_date = DateField('Mandate Expiry Date', validators=[DataRequired()])
    terms = TextAreaField('Agreed Mandate Terms & Commission Agreement')
    status = SelectField('Status', choices=[('Active', 'Active Mandate'), ('Expired', 'Expired'), ('Terminated', 'Terminated')])
    submit = SubmitField('Save Mandate')

class SiteVisitForm(FlaskForm):
    property_id = SelectField('Property to Visit', coerce=int, validators=[DataRequired()])
    client_id = SelectField('Associated Client', coerce=int, validators=[Optional()])
    lead_id = SelectField('Associated Lead', coerce=int, validators=[Optional()])
    assigned_employee_id = SelectField('Field Executive Responsible', coerce=int, validators=[DataRequired()])
    visit_date = DateField('Visit Date', validators=[DataRequired()])
    visit_time = TimeField('Visit Time', validators=[DataRequired()])
    status = SelectField('Visit Status', choices=[
        ('Scheduled', 'Scheduled'),
        ('Confirmed', 'Confirmed with Client'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Rescheduled', 'Rescheduled'),
        ('No Show', 'Client / Party No Show')
    ])
    interest_level = SelectField('Client Interest Level', choices=[
        ('Very Interested', 'Very Interested (High Deal Potential)'),
        ('Interested', 'Interested (Seeking Details/Comparison)'),
        ('Neutral', 'Neutral (Exploring Alternatives)'),
        ('Not Interested', 'Not Interested (Disliked Location/Budget)')
    ], default='Interested')
    client_feedback = TextAreaField('Client Feedback on Property')
    executive_notes = TextAreaField('Field Executive Notes')
    next_action = StringField('Next Recommended Action', validators=[Optional(), Length(max=128)])
    next_follow_up_date = DateField('Next Follow-up Date', validators=[Optional()])
    submit = SubmitField('Save Site Visit')

class DealForm(FlaskForm):
    title = StringField('Deal Title', validators=[DataRequired(), Length(max=256)])
    client_id = SelectField('Client', coerce=int, validators=[DataRequired()])
    property_id = SelectField('Property', coerce=int, validators=[DataRequired()])
    lead_id = SelectField('Originating Lead', coerce=int, validators=[Optional()])
    owner_user_id = SelectField('Deal Closing Manager / BDE', coerce=int, validators=[DataRequired()])
    stage = SelectField('Deal Stage', choices=[
        ('Initial Discussion', '1. Initial Discussion'),
        ('Requirement Confirmed', '2. Requirement Confirmed'),
        ('Property Shortlisted', '3. Property Shortlisted'),
        ('Site Visit', '4. Site Visit Completed'),
        ('Negotiation', '5. Commercial Negotiation'),
        ('Token Received', '6. Token / Advance Received'),
        ('Agreement', '7. Agreement / MoU Drafting'),
        ('Closed Won', '8. Closed Won (Signed & Settled)'),
        ('Closed Lost', '9. Closed Lost')
    ])
    quoted_value = DecimalField('Quoted Value (₹)', default=0, validators=[Optional()])
    expected_value = DecimalField('Expected Transaction Consideration (₹)', default=0, validators=[Optional()])
    final_value = DecimalField('Final Agreed Consideration (₹)', default=0, validators=[Optional()])
    token_amount = DecimalField('Token Advance Amount (₹)', default=0, validators=[Optional()])
    token_date = DateField('Token Date', validators=[Optional()])
    expected_closing_date = DateField('Target Closing Date', validators=[Optional()])
    actual_closing_date = DateField('Actual Closing Date', validators=[Optional()])
    agreement_status = SelectField('Agreement Status', choices=[('Draft', 'Drafting'), ('Sent', 'Sent to Parties'), ('Signed', 'Signed'), ('Registered', 'Sub-Registrar Registered')])
    lost_reason = StringField('Reason (if Lost)', validators=[Optional(), Length(max=256)])
    notes = TextAreaField('Negotiation Milestones & Contract Notes')
    submit = SubmitField('Save Deal')

class PaymentForm(FlaskForm):
    brokerage_id = SelectField('Brokerage Receivable Record', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Amount Received (₹)', validators=[DataRequired(), NumberRange(min=1)])
    payment_date = DateField('Date of Receipt', validators=[DataRequired()])
    payment_mode = SelectField('Payment Method', choices=[
        ('Bank Transfer', 'NEFT / RTGS / IMPS'),
        ('Cheque', 'Bank Cheque'),
        ('UPI', 'UPI / QR Code'),
        ('Cash', 'Cash Receipt')
    ])
    transaction_ref = StringField('Transaction UTR / Cheque No.', validators=[Optional(), Length(max=128)])
    notes = TextAreaField('Receipt Notes & Bank Particulars')
    submit = SubmitField('Record Payment')

class CommissionForm(FlaskForm):
    brokerage_id = SelectField('Brokerage Receivable', coerce=int, validators=[DataRequired()])
    recipient_type = SelectField('Recipient Type', choices=[('Employee', 'Employee / BDE'), ('Channel Partner', 'External Channel Partner')])
    user_id = SelectField('Employee Beneficiary', coerce=int, validators=[Optional()])
    partner_name = StringField('Partner / Firm Name (if Channel Partner)', validators=[Optional(), Length(max=128)])
    commission_type = SelectField('Type', choices=[('Deal Incentive', 'Deal Incentive'), ('Target Bonus', 'Target Bonus'), ('Referral', 'Referral Commission')])
    percentage = DecimalField('Commission % of Brokerage', default=10.0, validators=[DataRequired()])
    amount = DecimalField('Incentive Amount (₹)', default=0, validators=[DataRequired()])
    notes = TextAreaField('Notes & Incentive Breakdown')
    submit = SubmitField('Submit Commission Claim')

class ExpenseForm(FlaskForm):
    title = StringField('Expense Title', validators=[DataRequired(), Length(max=128)])
    category = SelectField('Expense Head', choices=[
        ('Marketing', 'Marketing & Digital Portals'),
        ('Travel/Field', 'Field Travel & Conveyance'),
        ('Office Rent', 'Office Rent & Facilities'),
        ('Utilities', 'Electricity, Water & Maintenance'),
        ('Legal', 'Legal & Advocate Searches'),
        ('IT & Telecom', 'Internet, Software & SIM Cards'),
        ('Stationery', 'Stationery & Printing Kits')
    ], default='Marketing')
    amount = DecimalField('Amount (₹)', validators=[DataRequired(), NumberRange(min=1)])
    expense_date = DateField('Expense Date', default=date.today, validators=[DataRequired()])
    paid_to = StringField('Vendor / Payee Name', validators=[Optional(), Length(max=128)])
    payment_mode = SelectField('Payment Mode', choices=[('Bank Transfer', 'Bank Transfer'), ('UPI', 'UPI'), ('Cheque', 'Cheque'), ('Cash', 'Cash / Petty Cash')])
    notes = TextAreaField('Expense Description & Bill Details')
    submit = SubmitField('Save Expense')

class TaskForm(FlaskForm):
    title = StringField('Task Title', validators=[DataRequired(), Length(max=256)])
    description = TextAreaField('Task Details')
    assigned_to_id = SelectField('Assignee', coerce=int, validators=[DataRequired()])
    priority = SelectField('Priority', choices=[('High', 'High Priority'), ('Medium', 'Medium Priority'), ('Low', 'Low Priority')])
    due_date = DateField('Due Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Pending', 'Pending'), ('In Progress', 'In Progress'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled')])
    completion_notes = TextAreaField('Completion / Outcome Notes')
    lead_id = SelectField('Linked Lead', coerce=int, validators=[Optional()])
    client_id = SelectField('Linked Client', coerce=int, validators=[Optional()])
    property_id = SelectField('Linked Property', coerce=int, validators=[Optional()])
    deal_id = SelectField('Linked Deal', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Task')

class LeaveRequestForm(FlaskForm):
    leave_type = SelectField('Leave Category', choices=[
        ('Casual Leave', 'Casual Leave'),
        ('Sick Leave', 'Sick Leave'),
        ('Earned Leave', 'Earned Leave'),
        ('Privilege Leave', 'Privilege Leave')
    ])
    start_date = DateField('From Date', validators=[DataRequired()])
    end_date = DateField('To Date', validators=[DataRequired()])
    reason = TextAreaField('Reason for Absence', validators=[DataRequired()])
    submit = SubmitField('Submit Leave Request')

class TargetForm(FlaskForm):
    user_id = SelectField('BDE / Executive', coerce=int, validators=[DataRequired()])
    month_year = StringField('Month & Year (e.g. October 2026)', validators=[DataRequired(), Length(max=32)])
    working_days = IntegerField('Working Days', default=25, validators=[DataRequired()])
    call_target = IntegerField('Daily/Monthly Call Target', default=500, validators=[DataRequired()])
    actual_calls = IntegerField('Actual Calls Made', default=0, validators=[Optional()])
    lead_target = IntegerField('New Leads Target', default=15, validators=[DataRequired()])
    actual_leads = IntegerField('Actual Leads Generated', default=0, validators=[Optional()])
    site_visit_target = IntegerField('Site Visits Target', default=10, validators=[DataRequired()])
    actual_site_visits = IntegerField('Actual Site Visits Done', default=0, validators=[Optional()])
    revenue_target = DecimalField('Brokerage Revenue Target (₹)', default=0, validators=[Optional()])
    actual_revenue = DecimalField('Actual Revenue Achieved (₹)', default=0, validators=[Optional()])
    notes = TextAreaField('Performance Remarks')
    submit = SubmitField('Save Target & Review')

class RecruitmentForm(FlaskForm):
    candidate_name = StringField('Candidate Full Name', validators=[DataRequired(), Length(max=128)])
    position = StringField('Applying Position (e.g. BDE)', validators=[DataRequired(), Length(max=100)])
    department = SelectField('Department', choices=[
        ('Business Development', 'Business Development'),
        ('Operations', 'Operations & Field Sales'),
        ('Marketing', 'Marketing'),
        ('Human Resources', 'Human Resources'),
        ('Finance', 'Finance & Accounts')
    ], default='Business Development')
    phone = StringField('Mobile Number', validators=[DataRequired(), Length(max=20)])
    email = StringField('Email Address', validators=[Optional(), Email(), Length(max=120)])
    source = SelectField('Source', choices=[
        ('LinkedIn', 'LinkedIn'),
        ('Naukri', 'Naukri.com'),
        ('Employee Referral', 'Employee Referral'),
        ('Indeed', 'Indeed'),
        ('Direct', 'Direct / Walk-in')
    ])
    stage = SelectField('Hiring Stage', choices=[
        ('Screening', '1. Screening'),
        ('Technical Interview', '2. Technical / Assessment'),
        ('Managerial Interview', '3. Managerial Interview'),
        ('HR Final', '4. HR Final'),
        ('Offer Released', '5. Offer Released'),
        ('Joined', '6. Candidate Joined'),
        ('Rejected', '7. Rejected')
    ], default='Screening')
    interview_date = DateField('Interview Date', validators=[Optional()])
    hiring_manager_id = SelectField('Hiring Manager', coerce=int, validators=[Optional()])
    notes = TextAreaField('Candidate Profile & Interview Feedback')
    submit = SubmitField('Save Candidate Record')

class AssetForm(FlaskForm):
    asset_code = StringField('Asset Tag / Code (e.g. AST-001)', validators=[DataRequired(), Length(max=32)])
    asset_name = StringField('Asset Name (e.g. Lenovo ThinkPad L14)', validators=[DataRequired(), Length(max=128)])
    category = SelectField('Category', choices=[
        ('IT Hardware', 'IT Hardware (Laptops, Monitros)'),
        ('Mobile Device', 'Mobile Device / Field Tablet'),
        ('Field Equipment', 'Field Measurement Device / Laser Meter'),
        ('Office Keys', 'Office / Property Keys'),
        ('Furniture', 'Furniture & Fixtures')
    ])
    serial_number = StringField('Serial / IMEI Number', validators=[Optional(), Length(max=128)])
    allocated_to_id = SelectField('Allocated Employee', coerce=int, validators=[Optional()])
    allocation_date = DateField('Allocation Date', validators=[Optional()])
    purchase_date = DateField('Purchase Date', validators=[Optional()])
    purchase_cost = DecimalField('Purchase Cost (₹)', default=0, validators=[Optional()])
    status = SelectField('Status', choices=[
        ('Available', 'Available in Office'),
        ('Allocated', 'Allocated to Staff'),
        ('Under Maintenance', 'Under Maintenance'),
        ('Scrapped', 'Decommissioned / Scrapped')
    ], default='Available')
    notes = TextAreaField('Asset Condition & Specifications')
    submit = SubmitField('Save Asset Record')
