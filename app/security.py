# app/security.py

import os
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from typing import Optional
import hashlib
import secrets

from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# Configurações JWT lidas do .env (Mantidas para o caso de uso futuro)
SECRET_KEY = os.getenv("SECRET_KEY", "chave_secreta_default_insegura")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# Define o algoritmo de hashing de senha
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Lógica de Hashing de Senha (CRÍTICO: Truncamento para Setup) ---
BCRYPT_MAX_LENGTH = 72 

def _truncate_password(password: str) -> str:
    """ Trunca a senha em bytes para garantir que não exceda o limite do bcrypt. """
    return password.encode('utf-8')[:BCRYPT_MAX_LENGTH].decode('utf-8', 'ignore')

def verify_password(plain_password, hashed_password):
    """ Verifica se a senha em texto puro corresponde ao hash armazenado. """
    hashed_password = hashed_password.strip() 
    plain_password = _truncate_password(plain_password)
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """ Retorna o hash bcrypt de uma senha em texto puro. """
    password = password.strip()
    password = _truncate_password(password)
    return pwd_context.hash(password)

# --- Funções de Token JWT (Apenas para referência, não usadas na nova lógica) ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    # Função para criar JWT (Não usada na nova Auth)
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire, "sub": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    # Função para decodificar JWT
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
