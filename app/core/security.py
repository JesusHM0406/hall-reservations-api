from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()

def verify_password(plain_password: str, hashed_password: str):
  return password_hash.verify(plain_password, hashed_password)
