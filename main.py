# main.py

import os
from typing import Annotated, List, Optional
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
# NOVO: Importa o middleware de CORS
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
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
SUPERADMIN_PERMANENT_KEY = os.getenv("SUPERADMIN_PERMANENT_KEY", "SUA_CHAVE_SUPER_SECRETA").strip()
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "admin@deltabots.com.br").strip()
# ====================================================================


# --- Carregamento de Metadados ---
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
# CORREÇÃO: CONFIGURAÇÃO DE CORS (Cross-Origin Resource Sharing)
# ====================================================================
# Isso é OBRIGATÓRIO para que o seu frontend (portal.html) possa
# chamar a API de outro domínio.
origins = [
    "*", # Permite todas as origens (mais fácil para depuração)
    # Você pode restringir isso no futuro para o domínio do seu frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Permite GET, POST, etc.
    allow_headers=["*"], # Permite "Authorization", "X-API-Key", etc.
)
# ====================================================================


# ====================================================================
# DEPENDÊNCIAS DE SEGURANÇA (API KEY SUPER ADMIN)
# ====================================================================

async def get_current_user_by_apikey(api_key: Annotated[str, Depends(schemas.api_key_header)], db: Session = Depends(database.get_db)):
    """ Autentica o usuário pelo X-API-Key (Token Permanente). """
    
    if api_key == SUPERADMIN_PERMANENT_KEY:
        # CORREÇÃO: Usando o email limpo que definimos no topo
        user = crud.get_user_by_email(db, email=SUPERADMIN_EMAIL) 
        
        if user and user.role == 'superadmin':
            return user
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Chave X-API-Key inválida ou não autorizada.",
    )
    
async def is_super_admin(current_user: Annotated[models.User, Depends(get_current_user_by_apikey)]):
    """ Protege a rota, exigindo perfil Super Admin (API KEY). """
    return current_user 

# ====================================================================
# DEPENDÊNCIAS DE SEGURANÇA (LOGIN/SENHA JWT CLIENTE)
# ====================================================================

async def get_current_user_by_jwt(token: Annotated[str, Depends(schemas.oauth2_scheme)], db: Session = Depends(database.get_db)):
    """ Injeta o usuário (Cliente) autenticado na rota a partir do JWT. """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais (Token JWT)",
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

# ====================================================================
# 1. ROTA DE STATUS/HEALTH CHECK
# ====================================================================
@app.get("/", status_code=status.HTTP_200_OK, tags=["Status"])
def read_root():
    return {"message": "Deltabots Management API is running! Access /docs for endpoints."}


# ====================================================================
# 2. ROTA DE AUTENTICAÇÃO (LOGIN DO CLIENTE)
# ====================================================================
@app.post("/token", response_model=schemas.Token, tags=["Auth (Cliente Frontend)"])
def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(database.get_db)):
    """ 
    Autentica um usuário (Cliente) e retorna um JWT Access Token. 
    (Usado pelo Frontend)
    """
    user = crud.get_user_by_email(db, email=form_data.username)
    
    if not user or not security.verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuário inativo")
        
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)))
    
    access_token = security.create_access_token(
        data={"email": user.email, "role": user.role, "client_id": user.client_id},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# ====================================================================
# 3. ENDPOINT DE SETUP (CRIAÇÃO DO PRIMEIRO ADMIN)
# ====================================================================
@app.post("/setup/initial-user", response_model=schemas.User, tags=["Setup (Super Admin)"])
def create_initial_admin(db: Session = Depends(database.get_db)):
    """ 
    Cria um usuário superadmin inicial e o cliente interno (RODE APENAS UMA VEZ!).
    """
    if crud.get_clients(db, limit=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O setup já foi executado."
        )

    client_data = schemas.ClientCreate(name="Deltabots Internal", status="Active")
    db_client = crud.create_client(db, client_data)
    
    superadmin_email = os.getenv("SUPERADMIN_EMAIL", "admin@deltabots.com.br").strip()
    superadmin_password = os.getenv("SUPERADMIN_PASSWORD", "Admin2025")
    
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
# 4. ROTAS DE GESTÃO DE CLIENTES (Super Admin)
# ====================================================================
@app.post("/clients/", response_model=schemas.Client, tags=["Gestão (Super Admin)"])
def create_client(
    client: schemas.ClientCreate, 
    db: Session = Depends(database.get_db),
    admin: Annotated[models.User, Depends(is_super_admin)] = None
):
    """ Cria um novo cliente (Apenas Super Admin com X-API-Key). """
    db_client = crud.create_client(db, client=client)
    return db_client

@app.get("/clients/", response_model=List[schemas.Client], tags=["Gestão (Super Admin)"])
def read_clients(skip: int = 0, limit: int = 100, 
                 db: Session = Depends(database.get_db), 
                 admin: Annotated[models.User, Depends(is_super_admin)] = None
):
    """ Lista todos os clientes (Apenas Super Admin com X-API-Key). """
    clients = crud.get_clients(db, skip=skip, limit=limit)
    return clients

# ====================================================================
# 5. ROTAS DE GESTÃO DE ROBÔS RPA (Super Admin)
# ====================================================================

@app.post("/bots/", response_model=schemas.RpaBot, tags=["Gestão (Super Admin)"])
def create_rpa_bot(
    bot: schemas.RpaBotCreate, 
    db: Session = Depends(database.get_db),
    admin: Annotated[models.User, Depends(is_super_admin)] = None
):
    """ Cria um novo robô (Apenas Super Admin com X-API-Key). """
    db_bot = crud.create_bot(db, bot=bot)
    return db_bot

@app.get("/bots/code/{code}", response_model=schemas.RpaBot, tags=["Gestão (Super Admin)"])
def read_bot_by_code(code: str, 
                     db: Session = Depends(database.get_db), 
                     admin: Annotated[models.User, Depends(is_super_admin)] = None
):
    """ Busca um robô pelo código (Apenas Super Admin com X-API-Key). """
    bot = crud.get_bot_by_code(db, code=code)
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Robô não encontrado")
    return bot

# ====================================================================
# 6. ROTAS DO CLIENTE (Frontend)
# ====================================================================

@app.get("/me/bots", response_model=List[schemas.RpaBot], tags=["Dashboard (Cliente Frontend)"])
def get_my_bots(
    db: Session = Depends(database.get_db),
    user: Annotated[models.User, Depends(get_current_user_by_jwt)] = None
):
    """ Retorna a lista de robôs associados ao cliente do token JWT. """
    if user.client_id is None:
        if user.role == 'superadmin':
             # Superadmin logado via JWT pode ver todos os robôs
            return crud.get_all_bots(db) # (Necessário implementar crud.get_all_bots)
        return [] 
        
    bots = crud.get_bots_by_client(db, client_id=user.client_id)
    return bots

@app.get("/logs/transactions", response_model=schemas.RpaLogResponse, tags=["Dashboard (Cliente Frontend)"])
def get_rpa_logs(
    robo_codigo: str, 
    data_inicio: Optional[str] = None, 
    data_fim: Optional[str] = None,
    db: Session = Depends(database.get_db), 
    user: Annotated[models.User, Depends(get_current_user_by_jwt)] = None 
):
    """ 
    Consulta logs na API Externa de Logs (Flask/MongoDB). 
    Requer autenticação JWT de cliente e verifica a permissão do robô.
    """
    
    # 1. VERIFICAR PERMISSÃO DE CLIENTE
    if user.role != 'superadmin':
        bot = crud.get_bot_by_code(db, code=robo_codigo)
        if not bot or bot.client_id != user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado ao código do robô.")

    # 2. PREPARAR CHAMADA EXTERNA
    base_url = os.getenv("LOG_API_BASE_URL")
    api_key = os.getenv("LOG_API_KEY") # A chave permanente da API de Logs
    endpoint = f"{base_url}/logs" 
    
    params = {"robo_codigo": robo_codigo}
    if data_inicio:
        params["data_inicio"] = data_inicio
    if data_fim:
        params["data_fim"] = data_fim

    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json"
    }

    try:
        response = requests.get(endpoint, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        
        if response.status_code in [401, 403]:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, 
                                detail="Falha na autenticação da API de Logs (Verifique LOG_API_KEY).")
        
        response.raise_for_status() 

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                            detail=f"Falha de conexão com a API de Logs: {e}")

    raise HTTPException(status_code=response.status_code, detail="Erro desconhecido na API de Logs")

