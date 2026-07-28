from passlib.hash import sha256_crypt
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
import os
import secrets

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.environ.get("JWT_EXPIRE_MINUTES", "480"))

def verify_secret(plain_secret, hashed_secret):
    return sha256_crypt.verify(plain_secret, hashed_secret)

def get_secret_hash(secret):
    return sha256_crypt.hash(secret)

def generate_api_key() -> str:
    return f"app_{secrets.token_hex(12)}"

def generate_api_secret() -> str:
    return secrets.token_urlsafe(32)[:40]

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
