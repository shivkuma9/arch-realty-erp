# ARCH Realty — Complete ERP + CRM Platform
**Real Estate Consulting • Ahmedabad, Gujarat, India**

---

## 1. System Overview

ARCH Realty ERP + CRM is a production-grade, centralized enterprise web platform engineered for real estate consulting companies in Ahmedabad. It unites commercial and residential property inventory management, client and lead lifecycle tracking, field executive site visits, negotiations, pipeline deals, auditable brokerage ledgers, and operational human resources into a single system.

### Key Capabilities
- **Executive Real-Time Dashboard**: Database-backed KPIs, lead funnels, property distributions, and financial receivables formatted in Indian Rupees (`₹`).
- **CRM & Lead Lifecycle**: Ingestion channels, qualification, automatic duplicate detection, follow-up scheduling, and one-click lead conversion to Client.
- **Client & Mandate Registry**: Individual and corporate accounts, GSTIN/PAN support, exclusive and open developer/owner mandates.
- **Property Inventory & OpenStreetMap**: Multi-category listings (Commercial, Residential, Industrial, Land, Pre-Leased) with interactive Leaflet mapping across key Ahmedabad commercial hubs (SG Highway, Sindhu Bhavan Road, Bodakdev, Prahlad Nagar).
- **Rule-Based Property Matching**: Explainable scoring (0–100%) correlating budget, area, category, and preferred localities with match factors and alerts.
- **Deals & Negotiations Pipeline**: Kanban board and table views, stage change audit trail, and automatic brokerage fee calculation upon closure.
- **Finance & Audit-Safe Brokerage**: Configurable brokerage rules (Percentage & Rent Months), GST invoicing (18%), partial payment receipts, and operating expenses.
- **Field Operations**: Site visit calendar, conflict detection for executives, and geolocation check-in logging.
- **Operational HR**: Daily shift check-in/out, leave applications, task management, and team directory.
- **Protected Document Vault**: Storage outside public web root with mime-type and extension validation.
- **Security & RBAC**: Role-based access control across 7 roles, session management, CSRF protection, and audit logging.

---

## 2. Default Demo Credentials

All seed accounts are initialized with password: `arch1234` (configurable via `DEMO_PASSWORD` environment variable).

| Role | Username | Department | Access Scope |
| :--- | :--- | :--- | :--- |
| **Director / Owner** | `director` | Management | Full visibility across leads, finances, reports, settings |
| **Super Admin** | `admin` | IT & Admin | System configuration, database backups, user access |
| **Manager** | `manager` | Sales | Team-wide leads, deals, site visits, and tasks |
| **Senior Sales Exec** | `sales_rahul` | Sales | Assigned leads, owned deals, site visits, clients |
| **Sales Exec** | `sales_priya` | Sales | Assigned leads, owned deals, site visits, clients |
| **Field Executive** | `field_amit` | Operations | Assigned site visits, field check-ins, tasks |
| **Accounts Executive**| `accounts_neha`| Finance | Invoices, brokerage ledger, payment receipts, expenses |
| **HR / Operations** | `hr_anita` | HR & Admin | Team attendance, leave request approvals |

---

## 3. Windows 11 PowerShell Setup & Execution

### Prerequisites
- Python 3.11+ installed and available in Windows PATH.
- Windows PowerShell or Command Prompt.

### Step-by-Step Instructions

1. **Navigate to the Project Directory**:
   ```powershell
   cd C:\Users\sakth\.gemini\antigravity\scratch\arch_realty_erp_crm
   ```

2. **Create and Activate Python Virtual Environment**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install Dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Initialize Database & Seed Fictional Ahmedabad Data**:
   ```powershell
   python scripts\seed_demo_data.py
   ```

5. **Run the Automated Tests**:
   ```powershell
   pytest -v
   ```

6. **Start the Local Web Server**:
   ```powershell
   python run.py
   ```
   *The application will be live at `http://127.0.0.1:5000`.*

---

## 4. Database Point-in-Time Backup & Restoration

### Backup via Web Interface
Directors and Super Admins can click **💾 Instant DB Backup** under `/settings/`. The system creates a point-in-time snapshot under `instance/backups/arch_realty_backup_<timestamp>.db`.

### Restoration Procedure
1. Stop the application server (`Ctrl + C`).
2. Replace `instance/arch_realty.db` with the chosen backup file:
   ```powershell
   Copy-Item .\instance\backups\arch_realty_backup_YYYYMMDD_HHMMSS.db .\instance\arch_realty.db -Force
   ```
3. Restart the server:
   ```powershell
   python run.py
   ```

---

## 5. Technology Stack & Architectural Standards
- **Backend**: Flask 3.1+, Flask-SQLAlchemy 3.1+, Flask-Login, Flask-WTF, Werkzeug password hashing.
- **Frontend**: Clean Jinja2 modular templates, Vanilla ES6+ JavaScript, CSS3 variables with Light/Dark theme tokens.
- **Mapping & Charts**: Chart.js 4+ for executive funnels, Leaflet 1.9+ with OpenStreetMap tiles (no paid API key required).
- **Financial Architecture**: `Decimal`-backed calculations preventing floating-point inaccuracies.
