from abc import abstractmethod, ABC
from typing import Generic, TypeVar, List
from uuid import uuid4, UUID

T = TypeVar("T")

class BaseRepository(ABC, Generic[T]):
    
    @abstractmethod
    def get_all(self) -> List[T]:
        ...
        
    @abstractmethod
    def get_by_id(self, item_id: UUID) -> T:
        ...
        
    @abstractmethod
    def add_item(self, item: T) -> T:
        ...
    
    @abstractmethod
    def delete_item(self, item_id: UUID) -> bool:
        ...
        
    @abstractmethod
    def update_item(self, item_id: UUID, item: T) -> T:
        ...