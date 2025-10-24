# app/security.py (Simplificado)

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets # Para geração de salts

from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# Configurações JWT lidas do .env
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_default_insegura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# --- Funções de Hashing de Senha (USANDO PADRÃO SHA-256 PARA SETUP) ---
# NOTE: O hash é o que será armazenado no DB.
# Vamos usar SHA-256 + salt.
def hash_password(password: str) -> str:
    """ Cria um hash simples (para o setup inicial) """
    salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
    return f"{salt}:{hashed}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """ Verifica a senha hashada (salt:hash) """
    try:
        salt, stored_hashed_password = stored_hash.split(':')
        new_hash = hashlib.sha256((plain_password + salt).encode('utf-8')).hexdigest()
        return new_hash == stored_hashed_password
    except ValueError:
        return False

# --- Funções de Token JWT (Sem Alterações) ---
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # ... (JWT code remains the same)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire, "sub": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    # ... (JWT code remains the same)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
