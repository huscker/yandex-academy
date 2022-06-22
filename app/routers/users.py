from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordRequestForm

import app.queries.users as users_queries
from app.models import SuccessfullResponse, UserIn, User
from app.auth.hash import get_password_hash, verify_password
from app.auth.jwt_token import create_access_token
from app.auth.oauth2 import get_current_user
from app.exceptions import NotFoundException, BadRequest, ForbiddenException
from app.settings import ACCESS_TOKEN_EXPIRE_MINUTES
from app.utils import format_record

users_router = APIRouter(tags=["Users"])


@users_router.post('/registration')
async def registration_user(request: OAuth2PasswordRequestForm = Depends()) -> dict:
    if len(request.password) < 8 or request.password.isdigit():
        raise BadRequest('Слабый пароль')
    request.password = get_password_hash(request.password)
    await users_queries.add_user('',request.username,request.password)
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@users_router.post("/login")
async def login(request: OAuth2PasswordRequestForm = Depends()) -> dict:
    print(request.username)
    user = await users_queries.get_user_by_login(request.username)
    if not verify_password(request.password, user['hashed_password']):
        raise ForbiddenException('Неверный пароль')
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@users_router.put('/user/update', response_model=SuccessfullResponse)
async def update_user_data(user_update: User, login: str = Depends(get_current_user)) -> SuccessfullResponse:
    user = await users_queries.get_user_by_login(login)
    user = format_record(user, User)
    if user_update.hashed_password:
        user_update.hashed_password = get_password_hash(user_update.hashed_password)
    else:
        user_update.hashed_password = None
    if not user.name:
        user.name = None
    await users_queries.update_user_data(user.login, user_update.name, user_update.hashed_password)
    return SuccessfullResponse()

@users_router.get('/user/name', response_model=str)
async def get_user_name(login: str = Depends(get_current_user)) -> str:
    user_name = await users_queries.get_user_name(login)
    return user_name