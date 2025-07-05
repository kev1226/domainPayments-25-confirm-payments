from jose import jwt, JWTError
from app.config import SECRET_KEY


def decode_token(token: str):

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        return payload
    except JWTError as e:
        print("DEBUG >>> Error al decodificar token:", e)
        return None
