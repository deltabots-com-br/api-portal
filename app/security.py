import os
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# Configurações JWT lidas do .env
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_default_insegura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Define o algoritmo de hashing de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Lógica de Truncamento (Correção do ValueError) ---
BCRYPT_MAX_LENGTH = 72 

def _truncate_password(password: str) -> str:
    """ 
    Trunca a senha em bytes para garantir que não exceda o limite do bcrypt (72 bytes).
    """
    # Codifica para bytes, trunca, e decodifica de volta para string
    return password.encode('utf-8')[:BCRYPT_MAX_LENGTH].decode('utf-8', 'ignore')

# --- Funções de Hashing de Senha ---

def verify_password(plain_password, hashed_password):
    """ Verifica se a senha em texto puro corresponde ao hash armazenado. """
    
    # CRÍTICO: Limpa o hash lido do banco de dados (remove espaços, \n)
    hashed_password = hashed_password.strip() 

    # Trunca a senha de entrada antes de verificar o hash
    plain_password = _truncate_password(plain_password)
    
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """ Retorna o hash bcrypt de uma senha em texto puro. """
    
    # Aplica .strip() na entrada antes de hash, por segurança
    password = password.strip()
    
    # APLICAR TRUNCAMENTO ANTES DO HASHING
    password = _truncate_password(password)
    return pwd_context.hash(password)

# --- Funções de Token JWT ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """ Cria um novo JWT Access Token. """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire, "sub": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    """ Decodifica e valida um JWT Access Token. """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
