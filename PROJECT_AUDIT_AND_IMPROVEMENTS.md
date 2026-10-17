# ARCH Realty ERP + CRM — Complete Project Audit, Deployment & Improvement Report

**Generated for:** Development Team & Management  
**Date:** October 2026  
**Status:** Live on Cloud (Render + Neon Cloud PostgreSQL)  
**GitHub Repository:** [https://github.com/shivkuma9/arch-realty-erp](https://github.com/shivkuma9/arch-realty-erp)

---

## 1. Executive Summary

This project is a full-featured real estate ERP and CRM platform customized for property consulting operations in Ahmedabad, Gujarat. It unifies lead ingestion, property matching, deals pipeline, 18% GST brokerage invoicing, field site visits with GPS check-ins, and HR attendance/payroll.

The application has been successfully configured, containerized with Gunicorn, connected to a cloud serverless PostgreSQL database (Neon), verified end-to-end, and deployed live.

---

## 2. Production Deployment & Live Setup Done

The following changes were implemented to take the project from local-only to live cloud production:

1. **Cloud Database (Neon PostgreSQL):**
   - Configured via Neon CLI (`neon@8.8.0`) under branch `production`.
   - Wired pooled connection string (`ep-square-resonance-b4m25w74-pooler.c-6.us-east-2.aws.neon.tech`) with SSL enabled.
   - Tested live connections, schema migrations, and queries end-to-end.
2. **Production WSGI Server:**
   - Replaced development server with `gunicorn run:app` and configured `Procfile`.
   - Added `psycopg[binary]>=3.1.18` and `psycopg2-binary>=2.9.9` to support modern SQLAlchemy 2.x PostgreSQL dialects.
3. **Automated Database Table Bootstrapping:**
   - Updated `app/__init__.py` to automatically detect empty cloud databases and bootstrap tables and demo data on initial launch.
4. **Build & Config Testing:**
   - Added `package.json` with `npm run build` (`neon config plan`) and `npm run test:neon` for CI verification.

---

## 3. Default Demo Credentials

| Role / Designation | Username | Password | Access Scope |
| :--- | :--- | :--- | :--- |
| **Super Admin** | `admin` | `admin123` | Full IT administration, backups, user management |
| **Managing Director** | `director` | `admin123` | Executive dashboard, revenue KPIs, reports |
| **Branch Sales Manager** | `manager` | `admin123` | Team leads, deals pipeline, site visits |
| **Senior Sales Executive** | `sales_rahul` | `admin123` | Assigned leads, owned deals, client directory |
| **Sales Executive** | `sales_priya` | `admin123` | Assigned leads, deals, site visits |
| **Accounts Officer** | `accounts_neha` | `admin123` | GST invoices, brokerage ledgers, expenses |
| **HR Operations** | `hr_anita` | `admin123` | Team attendance, leave approvals, payroll |
| **Field Executive** | `field_amit` | `admin123` | Site visits, GPS check-ins, calendar |

---

## 4. Key Recommendations & Improvements for the Developers

Here are the highest-priority improvements the development team should implement:

### 🔴 High Priority: Security & Data Integrity

1. **Remove Hardcoded Password Backdoor (`app/models/__init__.py` L59–60):**
   - **Current Code:**
     ```python
     if password in ['admin123', 'arch1234']:
         return True
     ```
   - **Risk:** Anyone who knows an employee's username can log in as Admin or Director using `admin123` or `arch1234`.
   - **Fix:** Remove this condition in production so passwords strictly validate via `check_password_hash`.

2. **Migrate Local File Uploads to Cloud Object Storage:**
   - **Current Code:** Uploaded property floor plans and KYC documents are saved to `instance/uploads/` on local disk.
   - **Risk:** Cloud platforms (Render, Heroku, containers) have ephemeral disks; uploaded files are lost when the server restarts or scales.
   - **Fix:** Connect to **AWS S3**, **Cloudflare R2**, or **Supabase Storage** with pre-signed download URLs.

3. **Rate Limiting on Authentication (`/auth/login`):**
   - Install `Flask-Limiter` to protect login endpoints from automated brute-force attacks.

4. **Production Session Security:**
   - Set `SESSION_COOKIE_SECURE = True` so session cookies only transmit over encrypted HTTPS.

---

### 🟡 Medium Priority: User Experience & Business Features

1. **Instant WhatsApp / SMS Lead Notifications:**
   - Real estate conversion in India depends on speed to lead.
   - Integrate the **WhatsApp Business API** or **Twilio** to automatically send an instant WhatsApp message to the assigned sales executive whenever a new lead arrives.

2. **Automated PDF Generator for Brokerage Invoices:**
   - Add automated invoice and receipt PDF generation (via `WeasyPrint` or `ReportLab`) containing company letterhead, GSTIN, PAN, and a UPI/Bank payment QR code.

3. **Interactive Drag-and-Drop Deals Pipeline (Kanban):**
   - Currently, moving deals between stages requires dropdown selection and page reloading.
   - Add client-side drag-and-drop using `SortableJS` so agents can drag deal cards across stages smoothly.

4. **Progressive Web App (PWA) for Field Agents:**
   - Add a `manifest.json` and basic service worker so field agents on smartphones can add ARCH Realty to their home screen like a native app for instant GPS check-in.

---

### 🟢 Low Priority: Infrastructure & Long-term Evolution

1. **Docker Containerization:**
   - Add a `Dockerfile` and `docker-compose.yml` so new developers can spin up the application with one command without Python environment mismatch issues.

2. **Consider a Next.js / React Frontend Migration (Next Phase):**
   - Rebuilding the frontend in **Next.js + Tailwind CSS + Shadcn UI** connected to the existing Neon PostgreSQL database would eliminate server sleep times on free tiers, provide instant SPA navigation without full page reloads, and deliver a modern interface.
