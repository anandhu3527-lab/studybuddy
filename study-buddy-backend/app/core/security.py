from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import base64

ph = PasswordHasher()

def hash_password(password: str) -> str:
    return ph.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, password)
    except VerifyMismatchError:
        return False

def encode_response(value: str) -> str:
    try:
      return base64.urlsafe_b64encode(value.encode()).decode()
    except Exception:
        return None

def decode_response(value: str) -> str:
    try:
     return base64.urlsafe_b64decode(value.encode()).decode()
    except Exception:
        return None
