ArchiSurance-Lite
A minimal but functional implementation of the ArchiMate-style business
architecture diagram (Sales Target / Profitability / Revenue-Costs /
Digital Customer Management / Smart Device Integration / Data-Driven
Insurance / CRM / Shared Back Office / Policy Administration / Financial
Services). Every element in the diagram is implemented as working code,
not just displayed — see the traceability table below.
Stack: Python (Flask + SQLite, one blueprint per concern) for the
backend, vanilla JS + Chart.js for the frontend. No build step, no
Node.js required — kept intentionally small.
1. Architecture
Code
2. Repository structure
Code
3. Setup
Bash
Open http://localhost:5000. The SQLite database and demo data are
created automatically on first run — no manual DB setup needed. To
reset, stop the server and delete archisurance.db.
Demo accounts (seeded automatically)
Username
Password
Role
admin
admin123
Admin (full access)
crm_manager
crm123
CRM Manager
policy_officer
policy123
Policy Officer
finance_manager
finance123
Finance Manager
customer1
customer123
Customer
Configuration
Environment variables (optional, all have safe defaults for local demo use):
JWT_SECRET — signing key for tokens (set this in production)
DATABASE_URL — SQLAlchemy URI, e.g. postgresql://user:pass@host/db to swap SQLite for PostgreSQL/MySQL
4. Tests
A lightweight smoke test suite is included:
Bash
5. Flowchart traceability
Flowchart element
Software module
Database entity
API
UI
Sales Target / Profitability / Revenue / Costs
Dashboard KPI service
Revenue, Cost
/api/dashboard, /api/dashboard/trends
Dashboard
Increase Revenue / Reduce Costs
Financial Service
Revenue, Cost
/api/financial/summary
Financial
Reduce Personnel Costs / Reduce Maintenance Costs
Cost Management
Cost (type=personnel/maintenance)
/api/costs
Financial
Improve Customer Retention / Increase Market Share
Customer + Dashboard KPIs
Customer
/api/dashboard, /api/customers/summary
Dashboard
Provide Competitive Premium Services
Data-Driven Insurance
Policy
/api/insurance/risk/<id>
Data-Driven Insurance
Integrate with Smart Device / Support for Smart Device Integration
Smart Device Integration
SmartDevice
/api/devices
Smart Devices
Improve Customer Interaction with Collected Data
Behavior + Recommendations service
CustomerBehavior
/api/behaviors, /api/analytics/recommendations/<id>
Analytics
Utilize the Insights of Customer Behaviors
Customer Behavior Analytics
CustomerBehavior
/api/analytics/behavior
Analytics
Digital Customer Management
Customer Management
Customer
/api/customers, /api/customers/<id>
Customers
Data Driven Insurance
Risk scoring service
Customer, Policy, SmartDevice, CustomerBehavior
/api/insurance/risk/<id>
Data-Driven Insurance
Maintain CRM Data Centrally / CRM Data Access
CRM aggregation service
Customer, Policy, SmartDevice, CustomerBehavior
/api/crm/customer/<id>
Customers (detail view)
Introduce the Common Use of Applications
Shared services (auth, CRM access) reused by every module
—
auth.py, api.py shared helpers
all pages
Establish a Shared Back Office for All Products
Back-office endpoints grouped under one API
Policy, Revenue, Cost
/api/policies, /api/financial/*
Policies, Financial
Support for Policy Administration / Policy Administration Services
Policy Administration
Policy, Payment
/api/policies, /api/policies/<id>/renew, /api/policies/<id>/cancel
Policies
Financial Services
Financial Service
Revenue, Cost, Payment
/api/revenue, /api/costs, /api/payments
Financial
General CRM System
Implemented as the app's own CRM layer (models + /api/crm/*)
Customer, Policy, SmartDevice, CustomerBehavior
/api/crm/customer/<id>
Customers
ArchiSurance Back Office Suite
Implemented as the Policy + Financial modules together
Policy, Payment, Revenue, Cost
/api/policies, /api/financial/*
Policies, Financial
6. Roles
Role
Access
Admin
Everything
CRM Manager
Customers, devices, analytics
Policy Officer
Policies, customers (read), risk scoring
Finance Manager
Revenue, costs, financial summary, customer summary
Customer
Own profile, own policies, own devices (read-only)
7. Notes
The risk score and market share figures are transparent,
rule-based demonstration values — explicitly not real insurance
underwriting or market research.
Smart device data is simulated (no real IoT hardware).
This project is intentionally compact for an academic/demo setting;
swap DATABASE_URL to Postgres/MySQL and set a real JWT_SECRET for
anything beyond a demo.