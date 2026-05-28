# Faisalabad Trade Portal — فیصل آباد ٹریڈ پورٹل

**A working web portal for Faisalabad's Export, Manufacturing & Factory Community**

Aggregates public government data (tax, customs, export records) with personalized, secure user dashboards and tiered paid packages.

## 🚀 Quick Start (Local)

```bash
git clone https://github.com/owstudies-oss/faisalabad-trade-portal.git
cd faisalabad-trade-portal
./run.sh
```

Then open **http://localhost:8000** in your browser.

## 🖥️ Live Demo

👉 https://owstudies-oss.github.io/faisalabad-trade-portal/

## ✨ Features

| Feature | Status |
|---------|--------|
| **Public Dashboard** — Hero stats, currency rates, market intelligence, regulatory alerts | ✅ Live |
| **User Registration** — Create an account with company details | ✅ Live |
| **Secure Login** — JWT-based authentication | ✅ Live |
| **Personal Dashboard** — KPIs, shipments, payments, activity log | ✅ Live |
| **Packages & Pricing** — 4 tiers: Free / PKR 999 / PKR 2,999 / PKR 9,999 | ✅ Live |
| **Add-On Services** — SMS alerts, PDF reports, API access | ✅ Live |
| **Payment** — JazzCash, Easypaisa, Bank Transfer, Credit Card | ✅ Live |
| **Payment History** — Transaction records | ✅ Live |

## 📁 Project Structure

```
├── backend/
│   ├── main.py           # FastAPI application (all API routes)
│   ├── models.py         # SQLAlchemy models (User, Package, Subscription, Payment)
│   ├── auth.py           # JWT authentication (register, login)
│   ├── database.py       # SQLite database setup
│   └── requirements.txt  # Python dependencies
├── frontend/
│   ├── public-dashboard.html  # Public landing page
│   ├── login.html             # Login page
│   ├── register.html          # Registration page
│   ├── dashboard.html         # Personal dashboard (protected)
│   ├── packages.html          # Packages & pricing
│   ├── payment.html           # Payment page
│   ├── css/style.css          # Shared stylesheet
│   └── js/api.js              # API client
├── run.sh                # One-command setup & run
└── README.md
```

## 🛠️ Tech Stack

- **Backend**: Python FastAPI + SQLite + JWT Auth
- **Frontend**: Vanilla HTML/CSS/JS (no build tools needed)
- **Auth**: JWT with bcrypt password hashing
- **Database**: SQLAlchemy ORM (SQLite local, PostgreSQL-ready)

## 🔧 Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🔌 API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/health` | No | Health check |
| GET | `/api/public/dashboard` | No | Public dashboard data |
| GET | `/api/packages` | No | List all packages |
| POST | `/api/auth/register` | No | Create account |
| POST | `/api/auth/login` | No | Sign in |
| GET | `/api/auth/me` | Yes | Get current user profile |
| GET | `/api/user/dashboard` | Yes | Personal dashboard |
| POST | `/api/payment/subscribe` | Yes | Subscribe to package |
| GET | `/api/user/activities` | Yes | Activity log |

## 📝 Todo / Future

- [ ] Email verification on registration
- [ ] 2FA support
- [ ] Real payment gateway integration (JazzCash API, Easypaisa API)
- [ ] Government data API integration (FBR, Pakistan Customs, TDAP)
- [ ] Urdu / English bilingual UI
- [ ] PostgreSQL migration
- [ ] Admin dashboard

---

*Empowering Faisalabad's export, manufacturing & factory community*