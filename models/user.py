from sqlalchemy import Column, Integer, String, Float
from db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    rfid_uid = Column(String, unique=True, index=True)
    balance = Column(Float, default=0.0)
