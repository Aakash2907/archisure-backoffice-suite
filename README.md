ArchiSure Backoffice Suite

## Secure Management of Competitive Examination Question Papers

ArchiSure Backoffice Suite is a secure cloud-ready question-paper management system designed to protect sensitive competitive examination question papers throughout their lifecycle.

The system provides controlled authentication, role-based access control, encrypted question-paper storage, release policies, multi-role approval workflows, secure retrieval, and audit-integrity verification.

The application is designed to reduce the risk of unauthorized access, modification, premature release, and leakage of examination question papers.

---

## 1. Project Description

Competitive examination question papers are highly sensitive documents. They may be exposed through unauthorized access, insider threats, insecure storage, accidental disclosure, or compromised systems.

ArchiSure addresses these risks by providing a controlled digital workflow for:

- User authentication
- Role-based access control
- Secure question-paper upload
- Encrypted question-paper storage
- Release-policy management
- Question-paper approval
- Controlled paper retrieval
- Audit logging
- Audit-integrity verification
- Time-based TOTP authentication
- Demonstration accounts for testing

The backend is implemented using **FastAPI**, while the frontend is implemented using **React + Vite**.

---

# 2. Key Features

### Authentication

- User registration
- Username/password authentication
- TOTP-based second-factor authentication
- Token-based authenticated API access

### Role-Based Access Control

The system supports different roles for different examination-management responsibilities, including:

- `QUESTION_SETTER`
- `RELEASE_APPROVER`
- `EXAM_CENTER_OPERATOR`
- `AUDITOR`

### Secure Question-Paper Management

- Upload examination question papers
- Encrypt stored paper data
- Maintain controlled access to papers
- Retrieve papers only through authorized workflows

### Release Control

- Configure release policies
- Require approval before release
- Control when papers can be released

### Approval Workflow

- Submit papers for approval
- Approve question papers
- Track paper status

### Audit

- Record security-sensitive operations
- Retrieve audit information
- Verify audit-log integrity

### Demo Mode

The project provides demonstration accounts and a `/demo/accounts` endpoint for testing authentication and TOTP functionality.

> The demo-account endpoint is intended for development/testing and should be disabled or protected before production deployment.

---

# 3. Technologies and Tools Used

## Frontend

| Technology | Purpose |
|---|---|
| React | User interface |
| Vite | Frontend development and build tool |
| JavaScript / JSX | Frontend implementation |
| CSS | User interface styling |

## Backend

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| Pydantic | Request/response validation |
| Cryptography | Encryption and secure cryptographic operations |

## Security

| Technology / Mechanism | Purpose |
|---|---|
| Password authentication | User authentication |
| TOTP | Time-based second-factor authentication |
| RBAC | Role-based authorization |
| Encryption | Protection of stored question papers |
| Audit logging | Security activity tracking |
| Integrity verification | Detection of audit-data modification |

## Deployment

| Tool | Purpose |
|---|---|
| Vercel | Cloud deployment |
| GitHub | Source-code management |
| Vite | Production frontend build |
| Vercel Python Functions | Backend API deployment |

---


4.Project Structure 
archisure-backoffice-suite/
│
├── api/
│   └── index.py
│
├── backend/
│   ├── requirements.txt
│   ├── run.py
│   │
│   └── app/
│       ├── __init__.py
│       ├── main.py
│       ├── deps.py
│       ├── schemas.py
│       ├── system.py
│       │
│       └── core/
│           ├── auth.py
│           ├── audit.py
│           ├── crypto_utils.py
│           ├── rbac.py
│           ├── release_control.py
│           └── storage.py
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   │
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api.js
│       ├── styles.css
│       │
│       └── components/
│           └── ...
│
├── requirements.txt
├── vercel.json
└── README.md