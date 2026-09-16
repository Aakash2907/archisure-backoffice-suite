ArchiSure Back-Office Suite
Description
ArchiSure Back-Office Suite is a small, functional implementation of an ArchiMate-style
business architecture diagram for an insurance company. Instead of just
displaying the diagram, every element in it — business goals, drivers,
capabilities, services, and applications — is implemented as working
software: a REST API backed by a database, with role-based dashboards for
CRM, policy administration, financial services, smart-device integration,
customer-behavior analytics, and data-driven insurance risk scoring.
The project is intentionally kept small (a handful of Python files and a
single-page frontend) so it is easy to read, run, and demonstrate end to end.
Technologies / Tools Used
Backend: Python, Flask
Database / ORM: SQLite, Flask-SQLAlchemy
Authentication: JWT (PyJWT), role-based authorization
Frontend: HTML, CSS, vanilla JavaScript, Chart.js (via CDN)
Testing: pytest
Version control: Git
Installation and Running Instructions
Clone the repository:
Bash
Create a virtual environment and activate it:
Bash
Install dependencies:
Bash
Run the application:
Bash
Open the app in a browser at http://localhost:5000.
The SQLite database (archisure.db) and demo data are created and
seeded automatically the first time the app runs — no manual database setup
is required. To reset all data, stop the server and delete
archisure.db, then restart.
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
Configuration (optional)
JWT_SECRET — signing key for tokens (set a real one before deploying beyond a demo)
DATABASE_URL — SQLAlchemy URI, e.g. postgresql://user:pass@host/db, to swap SQLite for PostgreSQL/MySQL
Running tests
Bash
Project Structure and Module Purpose
Code
Module → API summary
Module
Endpoints
What it does
Customer Management
/api/customers, /api/customers/<id>, /api/customers/summary
Register, search, and view customers; retention/satisfaction KPIs
CRM Data Access
/api/crm/customer/<id>
Aggregated view of a customer's policies, devices, and behavior in one call
Smart Device Integration
/api/devices
Register, list, and remove smart devices linked to customers (simulated IoT)
Customer Behavior Analytics
/api/behaviors, /api/analytics/behavior, /api/analytics/recommendations/<id>
Logs customer actions; produces action/service breakdowns, at-risk customers, and simple personalized recommendations
Policy Administration
/api/policies, /api/policies/<id>/renew, /api/policies/<id>/cancel
Create, search, renew, and cancel insurance policies
Financial Services
/api/revenue, /api/costs, /api/payments, /api/financial/summary
Records revenue/costs/payments; computes profit and profit margin
Data-Driven Insurance
/api/insurance/risk/<id>
Transparent, rule-based risk score and recommended premium (demo only, not real underwriting)
Main Dashboard
/api/dashboard, /api/dashboard/trends
Sales target, revenue, costs, profit, satisfaction, retention, market share, and 6-month trends
Sample Input and Output
1. Login
Request:
Http
Response:
Json
2. Dashboard KPIs (using the token from step 1)
Request:
Http
Response:
Json
3. Data-driven insurance risk score
Request:
Http
Response:
Json
4. Creating a new policy
Request:
Http
Response:
Json