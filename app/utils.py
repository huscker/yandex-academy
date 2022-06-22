from typing import Type
from asyncpg import Record
from app.models import BaseModel

def format_records(raw_records: list[Record], model: Type[BaseModel]) -> list[BaseModel]:
    if not raw_records:
        return []
    return list(map(lambda x: model(**x), raw_records))

def format_record(raw_record: Record, model: Type[BaseModel]) -> BaseModel:
    if not raw_record:
        return None
    return model(**raw_record)
