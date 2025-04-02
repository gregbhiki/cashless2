from db.database import Base, engine
from models.user import User
from models.transaction import Transaction

print("📦 Création de la base de données cashless.db...")

Base.metadata.create_all(bind=engine)

print("✅ Base de données créée avec succès !")

