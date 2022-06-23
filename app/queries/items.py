from datetime import datetime
from asyncio import gather
from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError
from app.db.db import DB
from app.exceptions import BadRequest, NotFoundException, InternalServerError
from app.models import ShopUnitImportRequest, ShopUnitOutput, ShopUnitOutputPlain, ShopUnitType
from app.utils import format_records

# TODO: добавить обновление средней цены категории
# TODO: обновить цены и парент айди при обновлении
# TODO: add_shop_units обновляет товары
# TODO: снапшоты
# TODO: BadRequest заменить на validation failed
# TODO: при удалении удаляются и снапшоты
# TODO: измение типа недопускается при обновлении
# TODO: проверить уникальность uuid при добавлении
# TODO: get_snapshots добавить цену
# TODO: целочисленное деление
# TODO: проверить является ли родитель категорией
# TODO: сделать insert ы одним запросом (с проверками не требуется)

# TODO: в README упомянуть что у меня не вылетает ошибки при изменении типа

async def add_shop_units(request: ShopUnitImportRequest) -> None:
    # Проверка на уникальные UUID
    items = request.items
    if len(set(map(lambda x: x.id, items))) != len(list(map(lambda x: x.id, items))):
        raise BadRequest('Уникальные UUID должны быть')
    # Проверка на типы родителей
    sql = """
        select u1.type from shop_units as u1
        join shop_units as u2
        on u1.uuid = u2.parentid
        where u2.uuid = ANY($1::uuid[])
    """
    parent_types = await DB.fetch(sql, list(map(lambda x: x.id)))
    category_types = map(lambda x: x['type'] == ShopUnitType.CATEGORY, parent_types)
    if len(list(category_types)) != len(items):
        raise BadRequest('Родители не типа категории')
    # Добавление/Обновление
    sql = """
        insert into shop_units(uuid, name, type, parentid, date, price) 
        values (coalesce($6, uuid_generate_v4()), $1, $2, $3, $4, $5) 
        on conflict (uuid) do update 
        set name = excluded.name, parentid = excluded.parentid,
        date = excluded.date, price = excluded.price
        returning uuid
    """
    coroutines = [
        DB.execute(sql,item.name, item.type, item.parentId,request.updateDate,item.price, item.id)
        for item in items
    ]
    uuids = list()
    try:
        uuids = list(await gather(*coroutines))
    except ForeignKeyViolationError as e:
        raise BadRequest('Родитель не существует') from e
    sql = """
        insert into snapshot
            select * from shop_units
            where uuid = ANY($1::uuid[]) 
    """
    await DB.execute(sql, uuids)


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
    sql = """
        delete from snapshot
        where uuid = $1
    """
    await DB.execute(sql, unit_id)

async def get_shop_unit(unit_id: int) -> ShopUnitOutput:
    async def recursive_get(unit_id: int) -> (ShopUnitOutput, int):
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
        children_uuids = await DB.fetch(sql, unit_id) # Тут посмотреть что возвращает DB fetch если детей нет
        children = [await recursive_get(uuid) for uuid in children_uuids]
        price_sum = sum(map(lambda x: x[1], children))
        if root.type == ShopUnitType.CATEGORY:
            root.price = price_sum // len(children)
        else:
            price_sum = root.price
        root.children = list(map(lambda x: x[0], children))
        return root, price_sum

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
       where $1 - 1 <= date and date <= $1 and date = $2
    """
    result = await DB.fetch(sql, date, ShopUnitType.OFFER)
    return format_records(result, ShopUnitOutputPlain)


async def get_snapshots(uuid: int, date_start: datetime, date_end: datetime) -> list[ShopUnitOutputPlain]:
    async def calculate_category_price(uuid: int, date_end: datetime) -> int:
        sql = """
            select uuid, type, price, date from snapshot
            where date <= $1 and uuid = $2
            order by date desc 
        """
        root = await DB.fetchrow(sql, date_end, uuid)
        if root.type == ShopUnitType.OFFER:
            return root.price
        sql = """
            select uuid,date from snapshot
            where parentid = $1 and date <= $2
        """
        children = await DB.fetch(sql, uuid, root.date)
        coroutines = [
            calculate_category_price(item['uuid'], item['date'])
            for item in children
        ]
        return sum(list(await gather(*coroutines)))


    sql = """
        select uuid, name, type, parentId, date, price from snapshot
        where $1 <= date and date < $2
    """
    result = await DB.fetch(sql, uuid, date_start, date_end)
    for item in result:
        if item['type'] == ShopUnitType.CATEGORY:
            item['price'] = await calculate_category_price(item['uuid'], item['date'])
    return format_records(result, ShopUnitOutputPlain)