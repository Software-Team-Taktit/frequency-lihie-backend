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
        async def create(payload: create_dto, repo: BaseRepository[T] = Depends(get_repository)):
            obj = self.model_cls(**payload.model_dump())
            saved = await repo.add_item(obj)
            if not saved:
                raise HTTPException(status_code=400, detail=f"couldnt create {self.model_cls.__name__}")
            return saved.model_dump()
        
        @self.router.get("")
        async def read_all(repo: BaseRepository[T] = Depends(get_repository)):
            items = await repo.get_all()
            return [item.model_dump() for item in items]
        
        @self.router.get("/{item_id}")
        async def read_by_id(item_id:str, repo: BaseRepository[T] = Depends(get_repository)):
            obj = await repo.get_by_id(item_id)
            if not obj:
                raise HTTPException(status_code=404, detail=f"{self.model_cls.__name__} not found")
            return obj.model_dump()
        
        @self.router.put("/{item_id}")
        async def update(item_id: str, payload: update_dto, repo: BaseRepository[T] = Depends(get_repository)):
            obj = self.model_cls(id = item_id, **payload.model_dump())
            updated = await repo.update_item(item_id, obj)
            if not updated:
                raise HTTPException(status_code=404, detail=f"faild to update {self.model_cls.__name__}")
            return updated.model_dump()
        
        @self.router.delete("/{item_id}", status_code=204)
        async def delete(item_id: str, repo: BaseRepository[T] = Depends(get_repository)):
            deleted = await repo.delete_item(item_id)
            if not deleted:
                raise HTTPException(status_code= 404, detail=f"{self.model_cls.__name__} not found")
        
        