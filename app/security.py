# app/security.py

from passlib.context import CryptContext

# Define o algoritmo de hashing a ser usado
# bcrypt é o padrão recomendado para hashing de senhas.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """
    Verifica se a senha em texto puro corresponde ao hash armazenado.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Retorna o hash bcrypt de uma senha em texto puro.
    """
    return pwd_context.hash(password)

# Exemplo de uso:
# hash = get_password_hash("minhasenha123")
# print(hash)
# print(verify_password("minhasenha123", hash))
