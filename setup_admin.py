# setup_admin.py (Rodar via EasyPanel Console APENAS UMA VEZ)

import os
import sys
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Garantir que o diretório 'app' seja importável
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db, SessionLocal
from app.security import hash_password
from app import models

load_dotenv()

SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "admin@deltabots.com.br")
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "Admin2025")

def create_initial_admin_and_client(db: Session):
    """ Tenta criar o primeiro cliente e o Super Admin. """
    
    # 1. Checa se o Super Admin já existe
    existing_user = db.query(models.User).filter(models.User.email == SUPERADMIN_EMAIL).first()
    if existing_user:
        print(f"ERRO: Usuário admin '{SUPERADMIN_EMAIL}' já existe. Setup abortado.")
        return

    # 2. Cria o Cliente Padrão (se não existir)
    client = models.Client(name="Deltabots Internal", status="Active")
    db.add(client)
    db.commit()
    db.refresh(client)
    print(f"Cliente Internal criado com ID: {client.id}")

    # 3. Cria o Super Admin com a senha HASHADA
    hashed_password = hash_password(SUPERADMIN_PASSWORD)

    admin_user = models.User(
        email=SUPERADMIN_EMAIL,
        name="Super Admin",
        password=hashed_password,
        role="superadmin",
        client_id=client.id 
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    print(f"Super Admin criado com sucesso. ID: {admin_user.id}")

    # 4. Finaliza a relação do cliente
    client.contact_user_id = admin_user.id
    db.commit()
    print("Setup Inicial Concluído!")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        create_initial_admin_and_client(db)
    except Exception as e:
        db.rollback()
        print(f"ERRO CRÍTICO DURANTE O SETUP: {e}")
        print("Certifique-se de que as tabelas do PostgreSQL foram criadas!")
    finally:
        db.close()
