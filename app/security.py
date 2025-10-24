# app/security.py (Atualizado)

import os
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional

# Adicione estas importações (se ainda não as fez no topo do arquivo)
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# Configurações JWT lidas do .env
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_default_insegura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Define o algoritmo de hashing de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Funções de Hashing de Senha (Já existentes) ---

def verify_password(plain_password, hashed_password):
    """ Verifica se a senha em texto puro corresponde ao hash armazenado. """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """ Retorna o hash bcrypt de uma senha em texto puro. """
    return pwd_context.hash(password)

# --- Funções de Token JWT (NOVAS) ---

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
