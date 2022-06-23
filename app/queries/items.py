from uuid import UUID

from datetime import datetime
from asyncio import gather
from asyncpg import Record
from asyncpg.exceptions import UniqueViolationError, ForeignKeyViolationError
from app.db.db import DB
from app.exceptions import BadRequest, NotFoundException, InternalServerError
from app.models import ShopUnitImportRequest, ShopUnitOutput, ShopUnitOutputPlain, ShopUnitType
from app.utils import format_records, format_record

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
    unique_parent_ids = set()
    for item in items:
        # Проверка на тип родителей
        sql = """
            select type from shop_units
            where id = $1
        """
        parent_type = await DB.fetchval(sql, item.parentId)
        if parent_type and parent_type != ShopUnitType.CATEGORY.value:
            raise BadRequest('Родитель не типа категории')
        # Проверка на инвариантность типа
        sql = """
            select type from shop_units
            where id = $1
        """
        current_type = await DB.fetchrow(sql, item.id)
        if current_type and current_type != item.type.value:
            raise BadRequest('Невозможно измененить тип')
        # Добавление/Обновление
        sql = """
            insert into shop_units(id, name, type, parentId, date, price) 
            values (coalesce($6, uuid_generate_v4()), $1, $2, $3, $4, $5) 
            on conflict (id) do update 
            set name = excluded.name, parentid = excluded.parentid,
            date = excluded.date, price = excluded.price
            returning id
        """
        uuid = None
        try:
            uuid = await DB.fetchval(sql,item.name, item.type.value, item.parentId,request.updateDate,item.price, item.id)
        except ForeignKeyViolationError as e:
            raise BadRequest('Родитель не существует') from e
        sql = """
            insert into snapshot
                select * from shop_units
                where id = $1
        """
        await DB.execute(sql, uuid)
        unique_parent_ids.add(item.parentId)
    st = list(unique_parent_ids)
    while st:
        cur = st.pop()
        sql = """
            update shop_units
            set date = $1
            where id = $2
            returning parentid
        """
        comming = await DB.fetchval(sql, request.updateDate, cur)
        if comming:
            st.append(comming)


async def delete_shop_unit(unit_id: UUID) -> None:
    sql = """
        select id from shop_units
        where id = $1
    """
    unit_id = await DB.fetchval(sql, unit_id)
    if not unit_id:
        raise NotFoundException('Категория/товар не найден')
    sql = """
        delete from shop_units
        where id = $1
    """
    await DB.execute(sql,unit_id)

async def get_shop_unit(unit_id: UUID) -> ShopUnitOutput:
    async def recursive_get(unit_id: UUID) -> (ShopUnitOutput, int, int):
        sql = """
            select id, name, type, parentId, date, price from shop_units
            where id = $1
        """
        root = await DB.fetchrow(sql,unit_id)
        root = format_record(root, ShopUnitOutput)
        sql = """
            select id from shop_units
            where parentid = $1
        """
        children_uuids = await DB.fetch(sql, unit_id)
        children = [await recursive_get(uuid['id']) for uuid in children_uuids]
        price_sum = sum(map(lambda x: x[1], children))
        price_num = sum(map(lambda x: x[2], children))
        if root.type == ShopUnitType.CATEGORY:
            root.price = price_sum // price_num
        else:
            price_sum = root.price
            price_num = 1
        root.children = list(map(lambda x: x[0], children))
        if not root.children:
            root.children = None
        return root, price_sum, price_num

    sql = """
        select id from shop_units
        where id = $1
    """
    root = await DB.fetchrow(sql, unit_id)
    if not root:
        raise NotFoundException('Категория/товар не найден')
    result = await recursive_get(unit_id)
    return result[0]

async def get_updated(date: datetime) -> list[ShopUnitOutputPlain]:
    sql = """
       select id, name, type, parentId, date, price from shop_units
       where $1 - 1 <= date and date <= $1 and date = $2
    """
    result = await DB.fetch(sql, date, ShopUnitType.OFFER)
    return format_records(result, ShopUnitOutputPlain)


async def get_snapshots(uuid: UUID, date_start: datetime, date_end: datetime) -> list[ShopUnitOutputPlain]:
    async def calculate_category_price(uuid: UUID, date_end: datetime) -> int:
        sql = """
            select id, type, price, date from snapshot
            where date <= $1 and id = $2
            order by date desc 
        """
        root = await DB.fetchrow(sql, date_end, uuid)
        if root.type == ShopUnitType.OFFER:
            return root.price
        sql = """
            select id,date from snapshot
            where parentid = $1 and date <= $2
        """
        children = await DB.fetch(sql, uuid, root.date)
        coroutines = [
            calculate_category_price(item['uuid'], item['date'])
            for item in children
        ]
        return sum(list(await gather(*coroutines)))


    sql = """
        select id, name, type, parentId, date, price from snapshot
        where $1 <= date and date < $2
    """
    result = await DB.fetch(sql, uuid, date_start, date_end)
    for item in result:
        if item['type'] == ShopUnitType.CATEGORY:
            item['price'] = await calculate_category_price(item['uuid'], item['date'])
    return format_records(result, ShopUnitOutputPlain)