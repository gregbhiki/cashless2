from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from auth import login_required
from db.database import get_db
from models.user import User
from models.transaction import Transaction
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
@login_required
def admin_home(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    return templates.TemplateResponse("admin.html", {"request": request, "users": users})


@router.post("/add")
@login_required
def add_user(request: Request, name: str = Form(...), rfid_uid: str = Form(...), balance: float = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(rfid_uid=rfid_uid).first()
    if existing:
        return RedirectResponse("/admin", status_code=303)

    user = User(name=name, rfid_uid=rfid_uid, balance=balance)
    db.add(user)
    db.commit()

    transaction = Transaction(user_id=user.id, amount=balance, type="recharge", timestamp=datetime.utcnow())
    db.add(transaction)
    db.commit()

    return RedirectResponse("/admin", status_code=303)


@router.post("/recharge")
@login_required
def recharge(request: Request, user_id: int = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        user.balance += amount
        db.commit()

        transaction = Transaction(user_id=user.id, amount=amount, type="recharge", timestamp=datetime.utcnow())
        db.add(transaction)
        db.commit()

    return RedirectResponse("/admin", status_code=303)


@router.post("/debit")
@login_required
def debit(request: Request, user_id: int = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    if user and user.balance >= amount:
        user.balance -= amount
        db.commit()

        transaction = Transaction(user_id=user.id, amount=amount, type="payment", timestamp=datetime.utcnow())
        db.add(transaction)
        db.commit()

    return RedirectResponse("/admin", status_code=303)


@router.get("/transactions/{user_id}", response_class=HTMLResponse)
@login_required
def view_transactions(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=user_id).first()
    transactions = db.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.timestamp.desc()).all()
    return templates.TemplateResponse("transactions.html", {
        "request": request,
        "user": user,
        "transactions": transactions
    })


@router.get("/live", response_class=HTMLResponse)
@login_required
def live_dashboard(request: Request):
    return templates.TemplateResponse("dashboard_live.html", {"request": request})

