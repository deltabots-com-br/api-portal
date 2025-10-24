# app/crud.py

from sqlalchemy.orm import Session
from . import models, schemas, security

# ====================================================================
# USUÁRIOS
# ====================================================================
def get_user_by_email(db: Session, email: str):
    """ Busca um usuário pelo email. """
    # Esta query agora funcionará, pois o ORM está mapeado corretamente
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """ Cria um novo usuário com hash de senha. """
    
    # A senha é hasheada, e a limpeza/truncamento ocorre em security.py
    hashed_password = security.get_password_hash(user.password)
    
    db_user = models.User(
        email=user.email,
        name=user.name,
        password=hashed_password, # Nome da coluna no DB
        role=user.role,
        client_id=user.client_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# ====================================================================
# CLIENTES e ROBÔS (Restante do CRUD)
# ====================================================================

# ... (Restante do código CRUD permanece o mesmo) ...
def get_client(db: Session, client_id: int):
    """ Busca um cliente pelo ID. """
    return db.query(models.Client).filter(models.Client.id == client_id).first()

def get_clients(db: Session, skip: int = 0, limit: int = 100):
    """ Lista todos os clientes. """
    return db.query(models.Client).offset(skip).limit(limit).all()

def create_client(db: Session, client: schemas.ClientCreate):
    """ Cria um novo cliente. """
    db_client = models.Client(name=client.name, status=client.status)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

def get_bots_by_client(db: Session, client_id: int, skip: int = 0, limit: int = 100):
    """ Lista os robôs de um cliente específico. """
    return db.query(models.RpaBot).filter(models.RpaBot.client_id == client_id).offset(skip).limit(limit).all()

def get_bot_by_code(db: Session, code: str):
    """ Busca um robô pelo código. """
    return db.query(models.RpaBot).filter(models.RpaBot.code == code).first()

def create_bot(db: Session, bot: schemas.RpaBotCreate):
    """ Cria um novo robô. """
    db_bot = models.RpaBot(
        client_id=bot.client_id,
        code=bot.code,
        description=bot.description,
        system_target=bot.system_target,
        status=bot.status
    )
    db.add(db_bot)
    db.commit()
    db.refresh(db_bot)
    return db_bot
