# setup_admin.py (VERSÃO TEMPORÁRIA: APENAS GERA O HASH)

import os
import sys
from passlib.context import CryptContext
from dotenv import load_dotenv

# Configuração mínima para o hash
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 1. Defina a senha que você quer usar
PASSWORD_TO_HASH = "Deltas2025" 

# 2. Gere o hash
correct_hash = pwd_context.hash(PASSWORD_TO_HASH)

# 3. Imprime o hash para que você possa copiá-lo
print("-------------------------------------------------------")
print(f"PASSWORD: {PASSWORD_TO_HASH}")
print(f"HASH GERADO: {correct_hash}")
print("-------------------------------------------------------")
print("AGORA COPIE O HASH E ATUALIZE O BANCO DE DADOS MANUALMENTE.")

# Este script não tentará criar o usuário, apenas mostra o hash.
