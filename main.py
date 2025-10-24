# main.py

import os
from typing import Annotated, List, Optional
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
# REMOVIDO: from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import requests 

from app import models, schemas, crud, database, security
from app.database import engine 

# Carrega variáveis de ambiente
load_dotenv()

# ====================================================================
# CRÍTICO: Variáveis de Chave Permanente
# ====================================================================
SUPERADMIN_PERMANENT_KEY = os.getenv("SUPERADMIN_PERMANENT_KEY", "SUA_CHAVE_SUPER_SECRETA")
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL")
# ====================================================================


# --- Carregamento de Metadados (Permanece) ---
try:
    print("Tentando carregar metadados do DB...")
    models.Base.metadata.create_all(bind=engine, checkfirst=True)
    print("Metadados carregados com sucesso.")
except Exception as e:
    print(f"AVISO: Falha ao carregar metadados do ORM (Pode ser ignorado se as tabelas já existirem): {e}")
# ---------------------------------------------


app = FastAPI(
    title="Deltabots Management API",
    version="1.0.0",
    description="API de Gestão para Clientes, Robôs e Usuários do Portal RPA."
)

# ====================================================================
# DEPENDÊNCIAS DE SEGURANÇA (API KEY)
# ====================================================================

async def get_current_user_by_apikey(api_key: Annotated[str, Depends(schemas.api_key_header)], db: Session = Depends(database.get_db)):
    """ Autentica o usuário pelo X-API-Key (Token Permanente). """
    
    # Verifica a Chave de Administrador Global
    if api_key == SUPERADMIN_PERMANENT_KEY:
        user = crud.get_user_by_email(db, email=SUPERADMIN_EMAIL)
        if user and user.role == 'superadmin':
            return user
        
    # Implementar lógica para chaves de clientes aqui, se necessário
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Chave X-API-Key inválida ou não autorizada.",
    )
    
async def is_super_admin(current_user: Annotated[models.User, Depends(get_current_user_by_apikey)]):
    """ Protege a rota, exigindo perfil Super Admin. """
    # A verificação já foi feita no get_current_user_by_apikey
    return current_user 


# ====================================================================
# 1. ROTA DE STATUS/HEALTH CHECK
# ====================================================================
@app.get("/", status_code=status.HTTP_200_OK, tags=["Status"])
def read_root():
    return {"message": "Deltabots Management API is running! Access /docs for endpoints."}


# ====================================================================
# 2. ROTA DE AUTENTICAÇÃO (LOGIN) - REMOVIDA
# ====================================================================
# REMOVIDA A ROTA /token

# ====================================================================
# 3. ENDPOINT DE SETUP (CRIAÇÃO DO PRIMEIRO ADMIN)
# ====================================================================
@app.post("/setup/initial-user", response_model=schemas.User, tags=["Setup"])
def create_initial_admin(db: Session = Depends(database.get_db)):
    """ 
    Cria um usuário superadmin inicial e o cliente interno (RODE APENAS UMA VEZ!).
    """
    if crud.get_clients(db, limit=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O setup já foi executado. Clientes/Usuários devem ser criados via rotas CRUD."
        )

    client_data = schemas.ClientCreate(name="Deltabots Internal", status="Active")
    db_client = crud.create_client(db, client_data)
    
    superadmin_email = os.getenv("SUPERADMIN_EMAIL", "admin@deltabots.com.br")
    superadmin_password = os.getenv("SUPERADMIN_PASSWORD", "Admin2025") # Senha curta padrão
    
    user_data = schemas.UserCreate(
        email=superadmin_email,
        name="Super Admin",
        password=superadmin_password,
        role="superadmin",
        client_id=db_client.id
    )
    db_user = crud.create_user(db, user_data)
    
    db_client.contact_user_id = db_user.id
    db.commit()
    
    return db_user


# ====================================================================
# 4. ROTAS DE GESTÃO DE CLIENTES
# ====================================================================
@app.post("/clients/", response_model=schemas.Client, tags=["Gestão: Clientes"])
def create_client(
    client: schemas.ClientCreate, 
    db: Session = Depends(database.get_db),
    admin: Annotated[models.User, Depends(is_super_admin)]
):
    """ Cria um novo cliente (Disponível apenas para Super Admin). """
    db_client = crud.create_client(db, client=client)
    return db_client

@app.get("/clients/", response_model=List[schemas.Client], tags=["Gestão: Clientes"])
def read_clients(skip: int = 0, limit: int = 100, 
                 db: Session = Depends(database.get_db), 
                 user: Annotated[models.User, Depends(get_current_user_by_apikey)]):
    """ Lista todos os clientes (Acesso por API Key). """
    
    if user.role == 'superadmin':
        clients = crud.get_clients(db, skip=skip, limit=limit)
    else:
        # Se for autenticado via API Key, mas não for o Super Admin (lógica futura)
        clients = [] 
        
    return clients

# ... (Restante das rotas de robôs) ...
