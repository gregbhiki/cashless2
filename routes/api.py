from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.transaction import Transaction
from models.user import User
from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    total_balance = db.query(func.sum(User.balance)).scalar() or 0
    total_recharges = db.query(func.sum(Transaction.amount)).filter(Transaction.type == "recharge").scalar() or 0
    total_payments = db.query(func.sum(Transaction.amount)).filter(Transaction.type == "payment").scalar() or 0

    now = datetime.utcnow()
    minute_data = []
    for i in range(10):  # les 10 dernières minutes
        t1 = now - timedelta(minutes=i+1)
        t2 = now - timedelta(minutes=i)
        count = db.query(Transaction).filter(Transaction.timestamp >= t1, Transaction.timestamp < t2).count()
        minute_data.append({
            "minute": t1.strftime("%H:%M"),
            "count": count
        })

    return {
        "total_balance": total_balance,
        "total_recharges": total_recharges,
        "total_payments": total_payments,
        "transactions_per_minute": list(reversed(minute_data))
    }

