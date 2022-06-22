from datetime import datetime
from asyncio import gather
from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError
from app.db.db import DB
from app.exceptions import BadRequest, NotFoundException, InternalServerError
from app.models import ShopUnitImportRequest, ShopUnitOutput, ShopUnitOutputPlain
from app.utils import format_records

# TODO: добавить обновление средней цены категории

async def add_shop_units(request: ShopUnitImportRequest) -> None:
    sql = """
        insert into shop_units(uuid, name, type, parentid, date, price) 
        values (uuid_generate_v4(), $1, $2, $3, $4, $5) 
    """
    items = request.items
    coroutines = [
        DB.execute(sql,item.name, item.type, item.parentId,request.updateDate,item.price)
        for item in items
    ]
    try:
        await gather(*coroutines)
    except UniqueViolationError as e:
        raise BadRequest('UUID не уникальны') from e
    except ForeignKeyViolationError as e:
        raise BadRequest('Родитель не существует') from e

async def delete_shop_unit(unit_id: int) -> None:
    sql = """
        select uuid from shop_units
        where uuid = $1
    """
    unit_id = await DB.fetchval(sql, unit_id)
    if not unit_id:
        raise NotFoundException('Категория/товар не найден')
    sql = """
        delete from shop_units
        where uuid = $1
    """
    await DB.execute(sql,unit_id)

async def get_shop_unit(unit_id: int) -> ShopUnitOutput:
    async def recursive_get(unit_id: int) -> ShopUnitOutput:
        sql = """
            select uuid, name, type, parentId, date, price from shop_units
            where uuid = $1
        """
        root = await DB.fetchrow(sql,unit_id)
        root = format_records(root, ShopUnitOutput)
        sql = """
            select uuid from shop_units
            where parentid = $1
        """
        children_uuids = await DB.fetch(sql, unit_id)
        children = [await recursive_get(uuid) for uuid in children_uuids]
        root.children = children
        return root

    sql = """
        select uuid from shop_units
        where uuid = $1
    """
    root = await DB.fetchrow(sql, unit_id)
    if not root:
        raise NotFoundException('Категория/товар не найден')
    result = await recursive_get(unit_id)
    return format_records(result, ShopUnitOutput)

async def get_updated(date: datetime) -> list[ShopUnitOutputPlain]:
    sql = """
       select uuid, name, type, parentId, date, price from shop_units
        where $1 - 1 <= date and date <= $2
    """
    result = await DB.fetch(sql, date)
    return format_records(result, ShopUnitOutputPlain)


