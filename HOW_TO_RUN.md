# ARCH Realty - Enterprise Real Estate ERP & CRM System
Ahmedabad, Gujarat Commercial & Residential Real Estate Platform

---

## 🚀 Quick Start (Easiest Way - Double-Click)

Inside the project folder:
`C:\Users\sakth\.gemini\antigravity\scratch\arch_realty_erp_crm`

Simply double-click:
👉 **`START.bat`**

It automatically:
1. Activates the Python virtual environment (`venv`).
2. Seeds database tables and demo datasets for all departments.
3. Launches the web server at: **http://127.0.0.1:5000**

---

## 💻 Manual Start (PowerShell Terminal)

```powershell
# 1. Navigate to project directory
cd C:\Users\sakth\.gemini\antigravity\scratch\arch_realty_erp_crm

# 2. Allow activation script for this session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 3. Activate Virtual Environment
.\venv\Scripts\Activate.ps1

# 4. Run the Flask Server
python -m flask run --host=127.0.0.1 --port=5000
```

Open your browser and navigate to:
🌐 **http://127.0.0.1:5000**

---

## 🔑 Login Credentials (Password for all: `admin123`)

| Department / Role | Username | Password |
|---|---|---|
| **Super Admin** | `admin` | `admin123` |
| **Managing Director** | `director` | `admin123` |
| **Sales Branch Manager** | `manager` | `admin123` |
| **Senior Sales Executive** | `sales_rahul` | `admin123` |
| **Field Operations Agent** | `field_amit` | `admin123` |
| **Finance & Accounts Officer**| `accounts_neha` | `admin123` |
| **HR & Operations Manager** | `hr_anita` | `admin123` |

---

## 🛡️ Departmental Access Control & Role Isolation

Each user only sees their own department in the sidebar and dashboard. Unauthorized direct URLs return `403 Forbidden`.

| Feature / Department | Super Admin & Director | Sales Manager | Sales Executive & BDE | Field Executive | Accounts Officer | HR Operations |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **Executive Dashboard** | ✅ Full | ✅ Full | ❌ (Sales Dash) | ❌ (Field Dash) | ❌ (Accounts Dash) | ❌ (HR Dash) |
| **CRM Leads & Inquiries** | ✅ Full | ✅ Full | ✅ Assigned | ❌ Hidden | ❌ Hidden | ❌ Hidden |
| **Client Directory** | ✅ Full | ✅ Full | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden |
| **BDE Targets & KPIs** | ✅ Full | ✅ Full | ✅ My Targets | ❌ Hidden | ❌ Hidden | ❌ Hidden |
| **Property Inventory & Map**| ✅ Full | ✅ Full | ✅ Full | ✅ View/Map | ❌ Hidden | ❌ Hidden |
| **Landlord Mandates** | ✅ Full | ✅ Full | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden |
| **Deals & Pipeline** | ✅ Full | ✅ Full | ✅ My Deals | ❌ Hidden | ✅ Read/Bill | ❌ Hidden |
| **Site Visits** | ✅ Full | ✅ Full | ✅ My Visits | ✅ My Visits | ❌ Hidden | ❌ Hidden |
| **Brokerage Receivables** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full | ❌ Hidden |
| **Invoices & Receipts** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full | ❌ Hidden |
| **Office Expenses Ledger** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full | ❌ Hidden |
| **Commission Claims** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full | ❌ Hidden |
| **Payroll Processing** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full | ✅ Full |
| **Staff Directory** | ✅ Full | ✅ View | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full |
| **Recruitment Pipeline** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full |
| **Office Assets Custody** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ❌ Hidden | ✅ Full |
| **My Tasks & Follow-ups** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **My Attendance & Punch** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Document Vault** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Reports & Analytics** | ✅ Full | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ❌ Hidden |
| **Settings & Users** | ✅ Full | ❌ Hidden | ❌ Hidden | ❌ Hidden | ❌ Hidden | ❌ Hidden |
