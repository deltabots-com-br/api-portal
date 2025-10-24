# main.py

import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app import models, schemas, crud, database

# Carrega variáveis de ambiente (necessário apenas para execução local)
load_dotenv()

# Cria as tabelas se elas não existirem (apenas se o DB estivesse vazio)
# Como suas tabelas já existem, esta linha é opcional.
# models.Base.metadata.create_all(bind=database.engine) 

app = FastAPI(
    title="Deltabots Management API",
    version="1.0.0",
    description="API de Gestão para Clientes, Robôs e Usuários do Portal RPA."
)

# ====================================================================
# 1. ROTA DE STATUS/HEALTH CHECK
# ====================================================================
@app.get("/", status_code=status.HTTP_200_OK, tags=["Status"])
def read_root():
    return {"message": "Deltabots Management API is running! Access /docs for endpoints."}


# ====================================================================
# 2. ENDPOINT PARA INSERÇÃO DO PRIMEIRO SUPERADMIN (OPCIONAL/DEBUG)
#    Você deve rodar isso uma única vez após o deploy para criar o admin
# ====================================================================
@app.post("/setup/initial-user", response_model=schemas.User, tags=["Setup"])
def create_initial_admin(db: Session = Depends(database.get_db)):
    """ 
    Cria um usuário superadmin inicial se nenhum usuário existir.
    RODE ISSO APENAS UMA VEZ!
    """
    if crud.get_clients(db, limit=1):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O banco de dados já tem clientes. Use o endpoint /users/ para criar novos usuários."
        )

    # Cria o cliente padrão (necessário para FK)
    client_data = schemas.ClientCreate(name="Deltabots Internal", status="Active")
    db_client = crud.create_client(db, client_data)
    
    # Cria o usuário Superadmin
    superadmin_email = os.getenv("SUPERADMIN_EMAIL", "admin@deltabots.com.br")
    superadmin_password = os.getenv("SUPERADMIN_PASSWORD", "SuperSecurePassword123!") # Use uma senha complexa
    
    user_data = schemas.UserCreate(
        email=superadmin_email,
        name="Super Admin",
        password=superadmin_password,
        role="superadmin",
        client_id=db_client.id
    )
    
    db_user = crud.create_user(db, user_data)
    
    # Atualiza o cliente para apontar para o usuário de contato
    db_client.contact_user_id = db_user.id
    db.commit()
    
    return db_user

# ====================================================================
# 3. ENDPOINT DE AUTENTICAÇÃO (A SER ADICIONADO NO PRÓXIMO PASSO)
# ====================================================================
# Incluiremos as rotas de autenticação (JWT) e CRUD no próximo passo.
