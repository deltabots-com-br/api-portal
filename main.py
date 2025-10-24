# main.py

import os
from typing import Annotated, List, Optional
from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
# A linha abaixo deve ser descomentada se você estivesse usando JWT/OAuth2. 
# Como removemos o /token, não é estritamente necessário, mas mantemos para referência:
# from fastapi.security import OAuth2PasswordRequestForm 
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
# Garante que o valor lido do sistema seja limpo de quaisquer espaços ou quebras de linha.
SUPERADMIN_PERMANENT_KEY = os.getenv("SUPERADMIN_PERMANENT_KEY", "SUA_CHAVE_SUPER_SECRETA").strip()
SUPERADMIN_EMAIL = os.getenv("SUPERADMIN_EMAIL", "admin@deltabots.com.br")
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
    
    # 1. Verifica a Chave de Administrador Global
    if api_key == SUPERADMIN_PERMANENT_KEY:
        user = crud.get_user_by_email(db, email=SUPERADMIN_EMAIL)
        if user and user.role == 'superadmin':
            return user
        
    # Se fosse para clientes, a lógica de busca na tabela api_keys viria aqui.
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Chave X-API-Key inválida ou não autorizada.",
    )
    
async def is_super_admin(current_user: Annotated[models.User, Depends(get_current_user_by_apikey)]):
    """ Protege a rota, exigindo perfil Super Admin. """
    return current_user 


# ====================================================================
# 1. ROTA DE STATUS/HEALTH CHECK
# ====================================================================
@app.get("/", status_code=status.HTTP_200_OK, tags=["Status"])
def read_root():
    return {"message": "Deltabots Management API is running! Access /docs for endpoints."}


# ====================================================================
# 2. ROTA DE AUTENTICAÇÃO (TOKEN JWT REMOVIDA)
# ====================================================================


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
    # CORREÇÃO SINTÁTICA
    admin: Annotated[models.User, Depends(is_super_admin)] = None
):
    """ Cria um novo cliente (Disponível apenas para Super Admin). """
    db_client = crud.create_client(db, client=client)
    return db_client

@app.get("/clients/", response_model=List[schemas.Client], tags=["Gestão: Clientes"])
def read_clients(skip: int = 0, limit: int = 100, 
                 db: Session = Depends(database.get_db), 
                 user: Annotated[models.User, Depends(get_current_user_by_apikey)] = None
):
    """ Lista todos os clientes (Super Admin vê todos, outros perfis só veem seus dados). """
    
    if user.role == 'superadmin':
        clients = crud.get_clients(db, skip=skip, limit=limit)
    else:
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
    # CORREÇÃO SINTÁTICA
    admin: Annotated[models.User, Depends(is_super_admin)] = None
):
    """ Cria um novo robô e o associa a um cliente (Disponível apenas para Super Admin). """
    db_bot = crud.create_bot(db, bot=bot)
    return db_bot

@app.get("/bots/code/{code}", response_model=schemas.RpaBot, tags=["Gestão: Robôs"])
def read_bot_by_code(code: str, 
                     db: Session = Depends(database.get_db), 
                     user: Annotated[models.User, Depends(get_current_user_by_apikey)] = None
):
    """ Busca um robô pelo código (Rastreabilidade). """
    
    bot = crud.get_bot_by_code(db, code=code)
    
    if bot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Robô não encontrado")
        
    if user.role != 'superadmin' and bot.client_id != user.client_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado: O robô não pertence ao seu cliente.")
        
    return bot

# ====================================================================
# 6. ROTA DE CONSULTA DE LOGS EXTERNA
# ====================================================================

@app.get("/logs/transactions", response_model=schemas.RpaLogResponse, tags=["Logs RPA"])
def get_rpa_logs(
    robo_codigo: str, 
    data_inicio: Optional[str] = None, 
    data_fim: Optional[str] = None,
    db: Session = Depends(database.get_db), 
    user: Annotated[models.User, Depends(get_current_user_by_apikey)] = None
):
    """ 
    Consulta logs na API Externa de Logs (Flask/MongoDB). 
    Requer autenticação de API Key e verifica a permissão do robô.
    """
    
    # 1. VERIFICAR PERMISSÃO DE CLIENTE
    if user.role != 'superadmin':
        bot = crud.get_bot_by_code(db, code=robo_codigo)
        if not bot or bot.client_id != user.client_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado ao código do robô.")

    # 2. PREPARAR CHAMADA EXTERNA
    base_url = os.getenv("LOG_API_BASE_URL")
    api_key = os.getenv("LOG_API_KEY")
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
