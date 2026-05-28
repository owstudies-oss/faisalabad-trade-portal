import json
import secrets
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from backend.database import get_db, init_db
from backend.models import User, Package, Subscription, Payment, ActivityLog
from backend.auth import hash_password, verify_password, create_access_token, decode_token

app = FastAPI(title="Faisalabad Trade Portal API")
security = HTTPBearer(auto_error=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
import os
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

# Root redirect to frontend
from fastapi.responses import RedirectResponse
@app.get("/")
def root():
    return RedirectResponse(url="/frontend/public-dashboard.html")

# ─── Seed Data ──────────────────────────────────────────────

SEED_PACKAGES = [
    {
        "name": "Free",
        "slug": "free",
        "price_pkr": 0,
        "description": "Basic access to public data and limited personalized features.",
        "features": json.dumps([
            "Public dashboard access",
            "Basic export data (monthly)",
            "Email notifications (weekly digest)",
            "1 user account"
        ]),
        "is_addon": False,
        "is_popular": False,
    },
    {
        "name": "Starter",
        "slug": "starter",
        "price_pkr": 999,
        "description": "For small exporters and traders monitoring their market.",
        "features": json.dumps([
            "Everything in Free",
            "Real-time customs updates",
            "Personalized dashboard",
            "Monthly PDF reports",
            "SMS alerts (up to 50/mo)",
            "2 user accounts"
        ]),
        "is_addon": False,
        "is_popular": True,
    },
    {
        "name": "Business",
        "slug": "business",
        "price_pkr": 2999,
        "description": "For growing export businesses with active international shipments.",
        "features": json.dumps([
            "Everything in Starter",
            "Real-time FBR tax data",
            "Competitor analysis reports",
            "API access (1000 calls/day)",
            "Unlimited SMS alerts",
            "5 user accounts",
            "Priority support"
        ]),
        "is_addon": False,
        "is_popular": False,
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "price_pkr": 9999,
        "description": "For large manufacturing and export houses with complex needs.",
        "features": json.dumps([
            "Everything in Business",
            "Custom data integrations",
            "Dedicated account manager",
            "Unlimited API access",
            "Bulk data export (CSV/JSON)",
            "Unlimited user accounts",
            "24/7 phone & email support",
            "On-premise deployment option"
        ]),
        "is_addon": False,
        "is_popular": False,
    },
    {
        "name": "SMS Alerts Add-On",
        "slug": "sms-alerts",
        "price_pkr": 199,
        "description": "Additional SMS alert quota (100 messages/month).",
        "features": json.dumps([
            "100 SMS alerts per month",
            "Real-time customs & regulatory updates",
            "Urgent deadline notifications"
        ]),
        "is_addon": True,
        "is_popular": False,
    },
    {
        "name": "PDF Reports Add-On",
        "slug": "pdf-reports",
        "price_pkr": 499,
        "description": "Detailed monthly PDF reports with custom data views.",
        "features": json.dumps([
            "Customizable monthly PDF reports",
            "Export/import trend analysis",
            "Price & tariff comparisons"
        ]),
        "is_addon": True,
        "is_popular": False,
    },
    {
        "name": "API Access Add-On",
        "slug": "api-access",
        "price_pkr": 1999,
        "description": "Direct API access to real-time trade data (10000 calls/day).",
        "features": json.dumps([
            "10,000 API calls per day",
            "REST API with JSON responses",
            "API key management",
            "Webhook support"
        ]),
        "is_addon": True,
        "is_popular": False,
    },
]


def seed_packages(db: Session):
    existing = db.query(Package).count()
    if existing > 0:
        return
    for pkg_data in SEED_PACKAGES:
        db.add(Package(**pkg_data))
    db.commit()


@app.on_event("startup")
def startup():
    init_db()
    db = next(get_db())
    try:
        seed_packages(db)
    finally:
        db.close()


# ─── Auth Helpers ───────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == int(payload.get("sub"))).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    if not credentials:
        return None
    payload = decode_token(credentials.credentials)
    if payload is None:
        return None
    return db.query(User).filter(User.id == payload.get("sub")).first()


# ─── Schemas ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: str
    password: str
    company_name: str
    contact_person: str
    phone: str
    city: str = "Faisalabad"

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

class PaymentRequest(BaseModel):
    package_slug: str
    method: str  # jazzcash, easypaisa, bank_transfer, card
    card_number: str | None = None
    card_expiry: str | None = None
    card_cvv: str | None = None


# ─── API Routes ─────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "portal": "Faisalabad Trade Portal"}


@app.post("/api/auth/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=req.email,
        company_name=req.company_name,
        contact_person=req.contact_person,
        phone=req.phone,
        city=req.city,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "company_name": user.company_name,
            "contact_person": user.contact_person,
            "phone": user.phone,
            "city": user.city,
        }
    )


@app.post("/api/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        user={
            "id": user.id,
            "email": user.email,
            "company_name": user.company_name,
            "contact_person": user.contact_person,
            "phone": user.phone,
            "city": user.city,
        }
    )


@app.get("/api/auth/me")
def get_me(user: User = Depends(get_current_user)):
    subs = []
    for s in user.subscriptions:
        pkg = s.package
        subs.append({
            "id": s.id,
            "package_name": pkg.name,
            "package_slug": pkg.slug,
            "price_pkr": pkg.price_pkr,
            "status": s.status,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
        })
    return {
        "id": user.id,
        "email": user.email,
        "company_name": user.company_name,
        "contact_person": user.contact_person,
        "phone": user.phone,
        "city": user.city,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "subscriptions": subs,
    }


@app.get("/api/packages")
def list_packages(include_addons: bool = True, db: Session = Depends(get_db)):
    q = db.query(Package)
    if not include_addons:
        q = q.filter(Package.is_addon == False)
    packages = q.all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "slug": p.slug,
            "price_pkr": p.price_pkr,
            "description": p.description,
            "features": json.loads(p.features),
            "is_addon": p.is_addon,
            "is_popular": p.is_popular,
        }
        for p in packages
    ]


@app.get("/api/public/dashboard")
def public_dashboard(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_revenue = db.query(Payment).filter(Payment.status == "completed").count() * 1000
    active_subs = db.query(Subscription).filter(Subscription.status == "active").count()
    return {
        "stats": {
            "total_exports_pkr": "428,000,000,000",
            "total_factories": "8,200+",
            "active_users": total_users,
            "active_subscriptions": active_subs,
            "total_revenue_pkr": f"{total_revenue:,}",
            "data_sources": ["FBR", "Pakistan Customs", "TDAP", "SMEDA", "Punjab Board of Investment"],
        },
        "currency_updates": [
            {"pair": "USD/PKR", "rate": "278.50", "change": "+0.35%"},
            {"pair": "EUR/PKR", "rate": "302.10", "change": "-0.18%"},
            {"pair": "GBP/PKR", "rate": "352.75", "change": "+0.42%"},
            {"pair": "CNY/PKR", "rate": "38.45", "change": "+0.12%"},
            {"pair": "SAR/PKR", "rate": "74.20", "change": "+0.08%"},
        ],
        "regulatory_alerts": [
            {"title": "New Textile Export Subsidy Announced", "date": "2026-05-28", "urgency": "high"},
            {"title": "Customs Duty Changes on Raw Cotton", "date": "2026-05-25", "urgency": "medium"},
            {"title": "TDAP Trade Show Registration Open", "date": "2026-05-20", "urgency": "low"},
            {"title": "FBR Tax Filing Deadline Extended", "date": "2026-05-18", "urgency": "high"},
            {"title": "New SRO on Export Rebates", "date": "2026-05-15", "urgency": "medium"},
        ],
        "market_intelligence": [
            {"sector": "Textiles", "growth": "+12.5%", "demand": "High", "top_market": "China"},
            {"sector": "Leather", "growth": "+8.3%", "demand": "Medium", "top_market": "Italy"},
            {"sector": "Sports Goods", "growth": "+15.1%", "demand": "High", "top_market": "USA"},
            {"sector": "Chemicals", "growth": "+5.9%", "demand": "Medium", "top_market": "Bangladesh"},
            {"sector": "Food Processing", "growth": "+10.2%", "demand": "High", "top_market": "UAE"},
        ],
    }


@app.get("/api/user/dashboard")
def user_dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    subs = db.query(Subscription).filter(Subscription.user_id == user.id).all()
    payments = db.query(Payment).filter(Payment.user_id == user.id).order_by(Payment.created_at.desc()).limit(10).all()
    activities = db.query(ActivityLog).filter(ActivityLog.user_id == user.id).order_by(ActivityLog.created_at.desc()).limit(10).all()

    active_subs_list = []
    for s in subs:
        if s.status == "active":
            pkg = s.package
            active_subs_list.append({
                "id": s.id,
                "package_name": pkg.name,
                "slug": pkg.slug,
                "price_pkr": pkg.price_pkr,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            })

    monthly_exports = 12800000  # simulated
    active_shipments = len(active_subs_list) * 5 + 3

    return {
        "company_name": user.company_name,
        "contact_person": user.contact_person,
        "email": user.email,
        "phone": user.phone,
        "city": user.city,
        "kpis": {
            "monthly_exports_pkr": monthly_exports,
            "active_shipments": active_shipments,
            "active_packages": len(active_subs_list),
            "total_payments": sum(p.amount_pkr for p in payments),
        },
        "subscriptions": active_subs_list,
        "recent_payments": [
            {
                "id": p.id,
                "amount_pkr": p.amount_pkr,
                "method": p.method,
                "status": p.status,
                "date": p.created_at.isoformat() if p.created_at else None,
            }
            for p in payments
        ],
        "recent_activities": [
            {
                "action": a.action,
                "details": a.details,
                "date": a.created_at.isoformat() if a.created_at else None,
            }
            for a in activities
        ],
    }


@app.post("/api/payment/subscribe")
def subscribe(
    req: PaymentRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    pkg = db.query(Package).filter(Package.slug == req.package_slug).first()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    # Create subscription
    expires = datetime.now(timezone.utc) + timedelta(days=30) if pkg.price_pkr > 0 else None
    sub = Subscription(
        user_id=user.id,
        package_id=pkg.id,
        status="active",
        expires_at=expires,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)

    # Create payment record
    txn_ref = f"TXN-{secrets.token_hex(4).upper()}"
    payment = Payment(
        user_id=user.id,
        subscription_id=sub.id,
        amount_pkr=pkg.price_pkr,
        method=req.method,
        status="completed" if pkg.price_pkr == 0 else "completed",
        transaction_ref=txn_ref,
    )
    db.add(payment)

    # Log activity
    db.add(ActivityLog(
        user_id=user.id,
        action=f"subscribed_to_{pkg.slug}",
        details=f"Subscribed to {pkg.name} package (PKR {pkg.price_pkr:,}) via {req.method}",
    ))
    db.commit()

    return {
        "success": True,
        "message": f"Successfully subscribed to {pkg.name}",
        "transaction_ref": txn_ref,
        "subscription_id": sub.id,
        "amount_pkr": pkg.price_pkr,
    }


@app.get("/api/user/activities")
def user_activities(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    activities = db.query(ActivityLog).filter(
        ActivityLog.user_id == user.id
    ).order_by(ActivityLog.created_at.desc()).limit(50).all()
    return [
        {
            "id": a.id,
            "action": a.action,
            "details": a.details,
            "date": a.created_at.isoformat() if a.created_at else None,
        }
        for a in activities
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
