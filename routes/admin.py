from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from db.database import SessionLocal
from models.user import User
from models.transaction import Transaction
from datetime import datetime
from auth import login_required
from io import StringIO
import csv

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_class=HTMLResponse)
@login_required
async def show_users(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    transactions = {user.id: db.query(Transaction).filter(Transaction.user_id == user.id).order_by(Transaction.timestamp.desc()).all() for user in users}
    return templates.TemplateResponse("admin.html", {"request": request, "users": users, "user_transactions": transactions})

@login_required
@router.post("/add", response_class=HTMLResponse)
async def add_user(request: Request, name: str = Form(...), rfid_uid: str = Form(...), balance: float = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.rfid_uid == rfid_uid).first()
    if existing:
        users = db.query(User).all()
        transactions = {user.id: db.query(Transaction).filter(Transaction.user_id == user.id).all() for user in users}
        return templates.TemplateResponse("admin.html", {"request": request, "users": users, "user_transactions": transactions, "error": f"UID {rfid_uid} est déjà utilisé"})
    user = User(name=name, rfid_uid=rfid_uid, balance=balance)
    db.add(user)
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@login_required
@router.post("/recharge", response_class=HTMLResponse)
async def recharge_user(request: Request, user_id: int = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.balance += amount
        tx = Transaction(user_id=user.id, type="recharge", amount=amount)
        db.add(tx)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@login_required
@router.post("/pay", response_class=HTMLResponse)
async def pay_user(request: Request, user_id: int = Form(...), amount: float = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.balance >= amount:
        user.balance -= amount
        tx = Transaction(user_id=user.id, type="payment", amount=amount)
        db.add(tx)
        db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@login_required
@router.post("/reset", response_class=HTMLResponse)
async def reset_tables(request: Request, db: Session = Depends(get_db)):
    db.query(Transaction).delete()
    db.query(User).delete()
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@login_required
@router.post("/reset-transactions", response_class=HTMLResponse)
async def reset_transactions(request: Request, db: Session = Depends(get_db)):
    db.query(Transaction).delete()
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@login_required
@router.post("/reset-balances", response_class=HTMLResponse)
async def reset_balances(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    for user in users:
        user.balance = 0.0
    db.commit()
    return RedirectResponse(url="/admin", status_code=303)

@login_required
@router.get("/export-balances")
async def export_balances(db: Session = Depends(get_db)):
    users = db.query(User).all()
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["Nom", "UID", "Solde (€)"])
    for user in users:
        writer.writerow([user.name, user.rfid_uid, user.balance])
    csv_buffer.seek(0)
    return StreamingResponse(csv_buffer, media_type="text/csv", headers={"Content-Disposition": "attachment; filename=balances.csv"})
