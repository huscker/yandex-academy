from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError, PostgresError
from app.db.db import DB
from app.exceptions import BadRequest, NotFoundException, InternalServerError


async def add_user(name: str,login: str, password: str) -> None:
    sql = """  INSERT INTO users(name,login,hashed_password)
               VALUES ($1,$2,$3)"""
    try:
        await DB.execute(sql, name, login, password)
    except UniqueViolationError as e:
        raise BadRequest('Пользователь с таким логином уже существует') from e
    except PostgresError as e:
        raise InternalServerError(e) from e


async def get_user_name(login: str) -> str:
    sql = """ SELECT id,name
              FROM users
              WHERE login = $1"""
    try:
        result = await DB.fetchrow(sql, login)
        if not result:
            raise NotFoundException('Пользователь не найден')
        return result['name']
    except PostgresError as e:
        raise InternalServerError(e) from e

async def get_user_by_login(login: str) -> Record:
    sql = """ SELECT id,name,login,hashed_password
              FROM users
              WHERE login = $1"""
    try:
        result = await DB.fetchrow(sql,login)
        if not result:
            raise NotFoundException('Пользователь не найден')
        return result
    except PostgresError as e:
        raise InternalServerError(e) from e

async def update_user_data(login: str, name: str, hashed_password: str) -> None:
    sql = """ UPDATE users
              SET name = COALESCE($1, name), 
                  hashed_password = COALESCE($2, hashed_password)
              WHERE login = $3"""
    try:
        result = await DB.execute(sql, name, hashed_password, login)
        return result
    except PostgresError as e:
        raise InternalServerError(e) from e

