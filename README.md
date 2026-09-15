# archisure-backoffice-suite
ArchiSurance Back Office Suite
A runnable full-stack academic implementation derived from the attached ArchiMate-style business architecture. It turns the diagram's business objectives, drivers, outcomes, capabilities, services and application components into working modules.
Architecture
React + Recharts UI
        |
        | REST / JWT
        v
Express.js API
  |-- Auth & RBAC
  |-- CRM Data Access
  |-- Customer / Interaction / Behavior Services
  |-- Smart Device Service (simulated IoT)
  |-- Policy Administration Services
  |-- Revenue / Cost / Financial Services
  |-- Analytics / Data Driven Insurance
  |-- Shared Back Office
        |
        v
PostgreSQL
  |-- Customers, CRM interactions, behaviors, devices
  |-- Policies and payments
  |-- Revenue, costs, financial transactions
  |-- Satisfaction and notifications
Repository structure
archisure-backoffice-suite/
├── backend/
│   ├── sql/schema.sql
│   ├── src/
│   │   ├── config/db.js
│   │   ├── middleware/auth.js
│   │   ├── middleware/errorHandler.js
│   │   ├── models/crudModel.js
│   │   ├── services/crudService.js
│   │   ├── services/dashboardService.js
│   │   ├── controllers/authController.js
│   │   ├── controllers/crudController.js
│   │   ├── controllers/dashboardController.js
│   │   ├── controllers/specialControllers.js
│   │   ├── routes/index.js
│   │   ├── utils/asyncHandler.js
│   │   ├── utils/seed.js
│   │   └── server.js
│   ├── .env.example
│   └── package.json
├── frontend/
│   ├── src/components/{Layout.jsx,UI.jsx}
│   ├── src/pages/{Login,Dashboard,Customers,CustomerDetails,Devices,Policies,Analytics,Recommendations,Finance,BackOffice,Reports,Settings}.jsx
│   ├── src/services/api.js
│   ├── src/main.jsx
│   ├── src/styles.css
│   ├── .env.example
│   └── package.json
├── docs/TRACEABILITY.md
├── docker-compose.yml
└── README.md
Quick start
1. Start PostgreSQL
Install Docker Desktop, then from the repository root:
docker compose up -d db
2. Create database tables
psql postgresql://archisure:archisure@localhost:5432/archisure -f backend/sql/schema.sql
If psql is not installed, run the schema through pgAdmin or any PostgreSQL client using the same connection details.
3. Start the backend
cd backend
cp .env.example .env
npm install
npm run seed
npm run dev
API: http://localhost:5000
4. Start the frontend
Open another terminal:
cd frontend
cp .env.example .env
npm install
npm run dev
Open the Vite URL shown in the terminal, normally http://localhost:5173.
Demo credentials
Admin: admin@archisure.local / Admin@123
CRM Manager: crm@archisure.local / Demo@123
Policy Officer: policy@archisure.local / Demo@123
Finance Manager: finance@archisure.local / Demo@123
Customer: customer@archisure.local / Demo@123
Implemented capabilities
Sales Target, Revenue, Costs, Profitability and Customer Satisfaction KPIs
Customer retention and market-share indicators
Digital Customer Management and centralized CRM Data Access
Customer interaction and behavior capture
Smart Device registration and simulated IoT telemetry
Rule-based Data Driven Insurance risk and premium recommendation
Policy create/update/renew/cancel workflows
Revenue, costs, personnel and maintenance cost tracking
Financial transactions and reports
Shared Back Office module registry
JWT authentication and role-based authorization
Responsive React UI with charts and tables
PostgreSQL constraints, foreign keys and indexes
API
POST /api/auth/login
GET /api/dashboard
GET /api/customers
GET /api/customers/:id/detail
POST /api/customers
PATCH /api/customers/:id
GET/POST /api/interactions
GET/POST /api/behaviors
GET/POST /api/devices
POST /api/devices/:id/simulate
GET/POST/PATCH /api/policies
GET/POST /api/revenue
GET/POST /api/costs
GET/POST /api/financial
GET /api/analytics/customers
GET /api/analytics/customer/:id/risk
GET /api/reports
GET /api/crm/data-access
GET /api/back-office/modules
Testing checklist
Login with Admin credentials.
Confirm dashboard loads KPI cards and charts.
Register a customer and verify it appears in Customers.
Open a customer and verify CRM detail, policies, devices and behavior sections.
Add a smart device and press Simulate IoT; health/telemetry should update.
Create a policy, then use Renew or Cancel.
Record revenue and cost and confirm dashboard profitability changes.
Add a financial transaction and verify it in Financial Services.
Open Customer Analytics and Data Driven Insurance.
Log in as Policy Officer or Finance Manager and verify restricted operations are enforced by the API.
GitHub
This package is prepared as a Git repository structure. To publish it to your own GitHub repository:
git init
git add .
git commit -m "Initial ArchiSurance back office implementation"
git branch -M main
git remote add origin https://github.com/<your-username>/archisure-backoffice-suite.git
git push -u origin main