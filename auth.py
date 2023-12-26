import time
from typing import Dict
from decouple import config
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

def token_response(token: str):
    return {"access_token": token}

secret_key = config("SECRET_KEY")

def sign_jwt(user_id: str) -> Dict[str, str]:
    # Set the expiry time.
    payload = {"user_id": user_id, "expires": time.time() + 2400}
    return token_response(jwt.encode(payload, secret_key, algorithm="HS256"))


def decode_jwt(token: str) -> dict:
    decoded_token = jwt.decode(token.encode(), secret_key, algorithms=["HS256"])
    return decoded_token if decoded_token["expires"] >= time.time() else {}


def verify_jwt(jwtoken: str) -> bool:
    isTokenValid: bool = False

    payload = decode_jwt(jwtoken)
    if payload:
        isTokenValid = True
    return isTokenValid


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(
            JWTBearer, self
        ).__call__(request)
        print("Credentials :", credentials)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(
                    status_code=403, detail="Invalid authentication token"
                )

            if not verify_jwt(credentials.credentials):
                raise HTTPException(
                    status_code=403, detail="Invalid token or expired token"
                )

            return credentials.credentials
        else:
            raise HTTPException(status_code=403, detail="Invalid authorization token")
