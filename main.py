# main.py

import os
from typing import Annotated, List, Optional
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app import models, schemas, crud, database, security

# Carrega variáveis de ambiente
load_dotenv()

app = FastAPI(
    title="Deltabots Management API",
    version="1.0.0",
    description="API de Gestão para Clientes, Robôs e Usuários do Portal RPA."
)

# ====================================================================
# DEPENDÊNCIAS DE SEGURANÇA
# ====================================================================

async def get_current_user(token: Annotated[str, Depends(schemas.oauth2_scheme)], db: Session = Depends(database.get_db)):
    """ Injeta o usuário autenticado na rota a partir do JWT. """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = security.decode_access_token(token)
    if payload is None:
        raise credentials_exception
        
    email: str = payload.get("email")
    if email is None:
        raise credentials_exception
        
    user = crud.get_user_by_email(db, email=email)
    if user is None or not user.is_active:
        raise credentials_exception
        
    return user
    
async def is_super_admin(current_user: Annotated[models.User, Depends(get_current_user)]):
    """ Protege a rota, exigindo perfil Super Admin. """
    if current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Requer perfil Super Admin."
        )
    return current_user


# ====================================================================
# 1. ROTA DE STATUS/HEALTH CHECK
# ====================================================================
@app.get("/", status_code=status.HTTP_200_OK, tags=["Status"])
def read_root():
    return {"message": "Deltabots Management API is running! Access /docs for endpoints."}


# ====================================================================
# 2. ROTA DE AUTENTICAÇÃO (LOGIN)
# ====================================================================
@app.post("/token", response_model=schemas.Token, tags=["Auth"])
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(database.get_db)):
    """ Autentica o usuário e retorna um JWT Access Token. """
    user = crud.get_user_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")
        
    # Gera o token, lendo o tempo de expiração do .env
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)))
    
    access_token = security.create_access_token(
        data={"email": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


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

    # 1. Cria o cliente padrão
    client_data = schemas.ClientCreate(name="Deltabots Internal", status="Active")
    db_client = crud.create_client(db, client_data)
    
    # 2. Cria o usuário Superadmin
    superadmin_email = os.getenv("SUPERADMIN_EMAIL", "admin@deltabots.com.br")
    superadmin_password = os.getenv("SUPERADMIN_PASSWORD", "SuperSecurePassword123!")
    
    user_data = schemas.UserCreate(
        email=superadmin_email,
        name="Super Admin",
        password=superadmin_password,
        role="superadmin",
        client_id=db_client.id
    )
    db_user = crud.create_user(db, user_data)
    
    # 3. Atualiza o cliente para apontar para o usuário de contato
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
    # CORREÇÃO DA SINTAXE: Dependências sem valor padrão devem vir antes das com valor padrão
    admin: Annotated[models.User, Depends(is_super_admin)] = None # Adiciona default para corrigir a ordem
):
    """ Cria um novo cliente (Disponível apenas para Super Admin). """
    # O 'admin' será injetado e a dependência is_super_admin verificará o acesso.
    db_client = crud.create_client(db, client=client)
    return db_client

@app.get("/clients/", response_model=List[schemas.Client], tags=["Gestão: Clientes"])
def read_clients(skip: int = 0, limit: int = 100, 
                 db: Session = Depends(database.get_db), 
                 user: Annotated[models.User, Depends(get_current_user)] = None):
    """ Lista todos os clientes (Super Admin vê todos, Client Admin vê apenas o seu). """
    
    if user.role == 'superadmin':
        clients = crud.get_clients(db, skip=skip, limit=limit)
    else:
        # Client Admin só pode ver o seu próprio cliente
        client = crud.get_client(db, client_id=user.client_id)
        clients = [client] if client else []
        
    return clients

# ====================================================================
# 5. ROTAS DE GESTÃO DE ROBÔS RPA
# ====================================================================

@app.post("/bots/", response_model=schemas.RpaBot, tags=["Gestão: Robôs"])
def create_rpa_bot(
    bot: schemas.RpaBotCreate, 
    db: Session = Depends(database.get_db),
    # CORREÇÃO DA SINTAXE: Adiciona default para corrigir a ordem do Python
    admin: Annotated[models.User, Depends(is_super_admin)] = None
):
    """ Cria um novo robô e o associa a um cliente (Disponível apenas para Super Admin). """
    db_bot = crud.create_bot(db, bot=bot)
    return db_bot

@app.get("/bots/code/{code}", response_model=schemas.RpaBot, tags=["Gestão: Robôs"])
def read_bot_by_code(code: str, 
                     db: Session = Depends(database.get_db), 
                     user: Annotated[models.User, Depends(get_current_user)] = None):
    """ Busca um robô pelo código (Rastreabilidade). """
    
    bot = crud.get_bot_by_code(db, code=code)
    
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Robô não encontrado")
        
    # Se não for Super Admin, verifica se o robô pertence ao cliente do usuário
    if user.role != 'superadmin' and bot.client_id != user.client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: O robô não pertence ao seu cliente.")
        
    return bot
