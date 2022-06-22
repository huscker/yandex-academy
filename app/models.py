from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


class SuccessfullResponse(BaseModel):
    details: str = Field('Выполнено', title='Статус операции')

class ShopUnitType(Enum):
    OFFER='OFFER'
    CATEGORY='CATEGORY'

class ShopUnitImport(BaseModel):
    id: str = Field(..., title='Уникальный идентификатор')
    name : str = Field(..., title='Имя категории')
    parentId: str = Field(None, title='UUID родительской категории')
    type: ShopUnitType = Field(..., title='Тип элемента - категория или товар')
    price: int = Field(None, title='Целое число, для категорий должно содержать null')

class ShopUnitImportRequest(BaseModel):
    items: list[ShopUnitImport] = Field([], title='Импортируемые элементы')
    updateDate: datetime = Field(None, title='Время обновления добавляемых товаров/категорий')


class ShopUnitOutput(BaseModel):
    pass

class ShopUnitOutput(BaseModel):
    id: str = Field(..., title='Уникальный идентификатор')
    name: str = Field(..., title='Имя категории')
    parentId: str = Field(None, title='UUID родительской категории')
    type: ShopUnitType = Field(..., title='Тип элемента - категория или товар')
    date: datetime = Field(..., title='Время обновления добавляемых товаров/категорий')
    price: int = Field(None, title='Целое число, для категорий должно содержать null')
    children: list[ShopUnitOutput] = Field([], title='Дочерние элементы')

class ShopUnitOutputPlain(BaseModel):
    id: str = Field(..., title='Уникальный идентификатор')
    name: str = Field(..., title='Имя категории')
    date: datetime = Field(..., title='Время обновления добавляемых товаров/категорий')
    parentId: str = Field(None, title='UUID родительской категории')
    price: int = Field(None, title='Целое число, для категорий должно содержать null')
    type: ShopUnitType = Field(..., title='Тип элемента - категория или товар')
