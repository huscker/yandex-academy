
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt

from app.models import TokenData
from app.settings import ALGORITHM, SECRET_KEY


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentails_exception) -> str:
    try:
        playload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        login: str = playload.get("sub")
        if login is None:
            raise credentails_exception
        token_data = TokenData(login=login)

    except JWTError:
        raise credentails_exception from JWTError
    return token_data.login
