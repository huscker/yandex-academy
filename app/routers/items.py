from datetime import timedelta,datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Path, Query
from fastapi.param_functions import Depends
from fastapi.security import OAuth2PasswordRequestForm

import app.queries.items as items_queries
from app.exceptions import NotFoundException, BadRequest, ForbiddenException
from app.settings import ACCESS_TOKEN_EXPIRE_MINUTES
from app.models import SuccessfullResponse, ShopUnitImportRequest, ShopUnitOutput, ShopUnitOutputPlain
from app.utils import format_record

basic_router = APIRouter(tags=["Базовые задачи"])
additional_router = APIRouter(tags=['Дополнительные задачи'])

# TODO: пошаманить с responses
# TODO: response_model_exclude

@basic_router.post('/imports',
                   response_model=SuccessfullResponse,
                   responses={400: {'code': 400, 'message': 'Validation Failed'}},
                   description="""
                   Импортирует новые товары и/или категории. Товары/категории импортированные повторно обновляют текущие. Изменение типа элемента с товара на категорию или с категории на товар не допускается. Порядок элементов в запросе является произвольным.

                      - uuid товара или категории является уникальным среди товаров и категорий
                      - родителем товара или категории может быть только категория
                      - принадлежность к категории определяется полем parentId
                      - товар или категория могут не иметь родителя (при обновлении parentId на null, элемент остается без родителя)
                      - название элемента не может быть null
                      - у категорий поле price должно содержать null
                      - цена товара не может быть null и должна быть больше либо равна нулю.
                      - при обновлении товара/категории обновленными считаются **все** их параметры
                      - при обновлении параметров элемента обязательно обновляется поле **date** в соответствии с временем обновления
                      - в одном запросе не может быть двух элементов с одинаковым id
                      - дата должна обрабатываться согласно ISO 8601 (такой придерживается OpenAPI). Если дата не удовлетворяет данному формату, необходимо отвечать 400.
            
                    Гарантируется, что во входных данных нет циклических зависимостей и поле updateDate монотонно возрастает. Гарантируется, что при проверке передаваемое время кратно секундам.
                   """
                   )
async def import_units(request: ShopUnitImportRequest):
    await items_queries.add_shop_units(request)
    return SuccessfullResponse()

@basic_router.delete('/delete/{id}',
                     response_model=SuccessfullResponse,
                     responses={
                         400: {'code': 400, 'message': 'Validation Failed'},
                         404: {'code': 404, 'message': 'Item not found'}
                     },
                     description="""
                     Удалить элемент по идентификатору. При удалении категории удаляются все дочерние элементы. Доступ к статистике (истории обновлений) удаленного элемента невозможен.

                     Так как время удаления не передается, при удалении элемента время обновления родителя изменять не нужно.

                     **Обратите, пожалуйста, внимание на этот обработчик. При его некорректной работе тестирование может быть невозможно.**                     """
                     )
async def delete_units(id: uuid4 = Path(..., description='Идентификатор')):
    await items_queries.delete_shop_unit(id)
    return SuccessfullResponse()

@basic_router.get('/nodes/{id}',
                  response_model=ShopUnitOutput,
                  responses={
                      400: {'code': 400, 'message': 'Validation Failed'},
                  },
                  description="""
                  Получить информацию об элементе по идентификатору. При получении информации о категории также предоставляется информация о её дочерних элементах.
                
                  - для пустой категории поле children равно пустому массиву, а для товара равно null
                  - цена категории - это средняя цена всех её товаров, включая товары дочерних категорий. Если категория не содержит товаров цена равна null. При обновлении цены товара, средняя цена категории, которая содержит этот товар, тоже обновляется.                    """
                  )
async def get_units(id: uuid4 = Path(..., description='Идентификатор элемента')):
    result = await items_queries.get_shop_unit(id)
    return result

@additional_router.get('/sales',
                      response_model=list[ShopUnitOutputPlain],
                      responses={
                          400: {'code': 400, 'message': 'Validation Failed'},
                      },
                      description="""
                      Получение статистики (истории обновлений) по товару/категории за заданный полуинтервал [from, to). Статистика по удаленным элементам недоступна.
                    
                      - цена категории - это средняя цена всех её товаров, включая товары дочерних категорий.Если категория не содержит товаров цена равна null. При обновлении цены товара, средняя цена категории, которая содержит этот товар, тоже обновляется.
                      - можно получить статистику за всё время. """
                      )
async def get_sales(date: datetime = Query(..., description='Дата и время запроса. Дата должна обрабатываться согласно ISO 8601 (такой придерживается OpenAPI). Если дата не удовлетворяет данному формату, необходимо отвечать 400')):
    result = await items_queries.get_updated(date)
    return result

@additional_router.get('/node/{id}/statistic',
                       response_model=list[ShopUnitOutputPlain],
                       responses={
                           400: {'code': 400, 'message': 'Validation Failed'},
                           404: {'code': 404, 'message': 'Item not found'}
                       },
                       description="""
                       Получение статистики (истории обновлений) по товару/категории за заданный полуинтервал [from, to). Статистика по удаленным элементам недоступна.
                        
                       - цена категории - это средняя цена всех её товаров, включая товары дочерних категорий.Если категория не содержит товаров цена равна null. При обновлении цены товара, средняя цена категории, которая содержит этот товар, тоже обновляется.
                       - можно получить статистику за всё время.
                        """
                       )
async def get_statistic(id: uuid4 = Path(..., description='UUID товара/категории для которой будет отображаться статистика'),
                        dateStart: datetime = Query(..., description='Дата и время начала интервала, для которого считается статистика. Дата должна обрабатываться согласно ISO 8601 (такой придерживается OpenAPI). Если дата не удовлетворяет данному формату, необходимо отвечать 400.'),
                        dateEnd: datetime = Query(..., description='Дата и время конца интервала, для которого считается статистика. Дата должна обрабатываться согласно ISO 8601 (такой придерживается OpenAPI). Если дата не удовлетворяет данному формату, необходимо отвечать 400.')):
    result = await items_queries.get_snapshots(id,dateStart,dateEnd)
    return result
