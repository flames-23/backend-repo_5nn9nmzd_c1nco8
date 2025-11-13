import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

from database import db, create_document, get_documents
from schemas import PaymentReturn

app = FastAPI(title="Payments Returns Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Payments Returns Analytics API"}

@app.get("/schema")
def get_schema():
    # Expose schema names for viewer tools
    return {"collections": ["paymentreturn"]}

class SeedRequest(BaseModel):
    count: int = 50

@app.post("/seed")
def seed_data(body: SeedRequest):
    """Seed the database with synthetic payment return events for demo."""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    import random

    reasons = [
        "insufficient_funds",
        "card_expired",
        "fraud_suspected",
        "disputed",
        "technical_error",
        "account_closed",
        "other",
    ]
    methods = ["card", "ach", "wire", "wallet"]
    regions = ["US", "EU", "APAC", "LATAM", "MEA"]
    segments = ["consumer", "smb", "enterprise"]

    now = datetime.utcnow()

    created = 0
    for i in range(body.count):
        amount = round(random.uniform(5, 2000), 2)
        occurred_at = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        days_to_return = random.randint(0, 14)
        status = random.choice(["returned", "refunded", "reversed", "chargeback", "resolved"])  # no pending in seed

        pr = PaymentReturn(
            transaction_id=f"txn_{now.timestamp():.0f}_{i}",
            customer_id=random.choice([None, f"cust_{random.randint(1000,9999)}"]),
            amount=amount,
            currency="USD",
            reason=random.choice(reasons),
            status=status,
            payment_method=random.choice(methods),
            region=random.choice(regions),
            customer_segment=random.choice(segments),
            occurred_at=occurred_at,
            days_to_return=days_to_return,
        )
        create_document("paymentreturn", pr)
        created += 1

    return {"inserted": created}

@app.get("/stats/summary")
def summary_stats():
    """High-level KPIs for dashboard"""
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    docs = get_documents("paymentreturn")
    total_returns = len(docs)
    total_amount = round(sum(d.get("amount", 0) for d in docs), 2)

    # Return rate proxy: returns / unique transactions last 30d (use docs count as proxy here)
    last30 = [d for d in docs if (datetime.utcnow() - d.get("occurred_at", datetime.utcnow())).days <= 30]
    last30_amount = round(sum(d.get("amount", 0) for d in last30), 2)

    by_reason = {}
    for d in docs:
        r = d.get("reason", "other")
        by_reason[r] = by_reason.get(r, 0) + 1

    return {
        "total_returns": total_returns,
        "total_amount": total_amount,
        "last30_count": len(last30),
        "last30_amount": last30_amount,
        "by_reason": by_reason,
    }

@app.get("/stats/timeseries")
def time_series(days: int = 30):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    docs = get_documents("paymentreturn")
    cutoff = datetime.utcnow() - timedelta(days=days)
    buckets = {}
    for d in docs:
        ts: datetime = d.get("occurred_at", datetime.utcnow())
        if ts < cutoff:
            continue
        key = ts.strftime("%Y-%m-%d")
        if key not in buckets:
            buckets[key] = {"count": 0, "amount": 0.0}
        buckets[key]["count"] += 1
        buckets[key]["amount"] += float(d.get("amount", 0))

    # return sorted list
    series = [
        {"date": k, "count": v["count"], "amount": round(v["amount"], 2)}
        for k, v in sorted(buckets.items())
    ]
    return {"series": series}

@app.get("/stats/breakdown")
def breakdown():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    docs = get_documents("paymentreturn")

    def agg(field: str):
        out = {}
        for d in docs:
            key = d.get(field) or "unknown"
            out[key] = out.get(key, 0) + 1
        return out

    return {
        "by_method": agg("payment_method"),
        "by_region": agg("region"),
        "by_status": agg("status"),
        "by_segment": agg("customer_segment"),
    }

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available" if db is None else "✅ Connected",
    }
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
