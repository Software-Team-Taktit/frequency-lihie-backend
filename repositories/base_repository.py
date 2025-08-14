from abc import abstractmethod, ABC
from typing import Generic, TypeVar, List

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    
    @abstractmethod
    async def get_all(self) -> List[T]:
        ...
        
    @abstractmethod
    async def get_by_id(self, item_id: str) -> T:
        ...
        
    @abstractmethod
    async def add_item(self, item: T) -> T:
        ...
    
    @abstractmethod
    async def delete_item(self, item_id: str) -> bool:
        ...
        
    @abstractmethod
    async def update_item(self, item_id: str, item: T) -> T:
        ...