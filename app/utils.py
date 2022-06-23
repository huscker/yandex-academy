from datetime import datetime
from typing import Type
from asyncpg import Record
from app.models import BaseModel, ShopUnitOutput

def format_records(raw_records: list[Record], model: Type[BaseModel]) -> list[BaseModel]:
    if not raw_records:
        return []
    return list(map(lambda x: model(**x), raw_records))

def format_record(raw_record: Record, model: Type[BaseModel]) -> BaseModel:
    if not raw_record:
        return None
    result = model(**raw_record)
    if model == ShopUnitOutput and raw_record['parentid']:
        result.parentId = raw_record['parentid']
    if model == ShopUnitOutput:
        result.date = format_date(result.date)
    return result

def format_date(date:datetime) -> str:
    # return date.replace(microsecond=0).isoformat() + 'Z'
    return date.replace(tzinfo=None).isoformat(timespec='milliseconds') + 'Z'

def extract_uuids(raw_records: list[Record]) -> list[str]:
    return [record['uuid'] for record in raw_records]