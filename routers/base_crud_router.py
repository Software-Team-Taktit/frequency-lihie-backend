from typing import Generic, TypeVar, Type, Callable
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from repositories.base_repository import BaseRepository

T = TypeVar("T") #Type
C = TypeVar("C", bound=BaseModel) #Create
U = TypeVar("U", bound=BaseModel) #Update

class BaseCrudRouter(Generic[T, C, U]):
    def __init__(self, 
                entity_name: str,
                model_cls: Type[T],
                create_dto: Type[C],
                update_dto: Type[U],
                get_repository: Callable[[], BaseRepository[T]]
            ):
        self.model_cls = model_cls  
        self.create_dto = create_dto
        self.update_dto = update_dto
        self.router = APIRouter(prefix=f"/{entity_name}",tags=[entity_name])
        
        @self.router.post("")
        async def create_item(payload: create_dto, repo: BaseRepository[T] = Depends(get_repository)):
            obj = self.model_cls(**payload.model_dump())
            saved = await repo.add_item(obj)
            if not saved:
                raise HTTPException(status_code=400, detail=f"couldnt create {Type[T]}")
            return {"message": f"item {saved.id} created"}
        
        