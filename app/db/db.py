import asyncpg
from asyncpg.exceptions import PostgresError, UniqueViolationError, ForeignKeyViolationError
from asyncpg import Record
from app.settings import DATABASE_URL
from app.exceptions import InternalServerError

def exception_wrapper(func):
    async def inner_func(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except UniqueViolationError:
            raise
        except ForeignKeyViolationError:
            raise
        except PostgresError as e:
            raise InternalServerError(e) from e
    return inner_func

class DB:
    pool: asyncpg.Pool = None

    @classmethod
    async def connect_db(cls) -> None:
        print(DATABASE_URL)
        try:
            cls.pool = await asyncpg.create_pool(DATABASE_URL)
            print(cls.pool)
        except Exception as e:
            print(e)

    @classmethod
    @exception_wrapper
    async def execute(cls, sql, *args) -> None:
        async with cls.pool.acquire() as con:
            return await con.execute(sql, *args)

    @classmethod
    @exception_wrapper
    async def fetch(cls, sql, *args) -> list[Record]:
        async with cls.pool.acquire() as con:
            return await con.fetch(sql, *args)

    @classmethod
    @exception_wrapper
    async def fetchval(cls, sql, *args):
        async with cls.pool.acquire() as con:
            return await con.fetchval(sql, *args)

    @classmethod
    @exception_wrapper
    async def fetchrow(cls, sql, *args) -> Record:
        async with cls.pool.acquire() as con:
            return await con.fetchrow(sql, *args)

    @classmethod
    async def disconnect_db(cls) -> None:
        await cls.pool.close()