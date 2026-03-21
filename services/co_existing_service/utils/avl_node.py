from dataclasses import dataclass
from typing import Generator, Optional

@dataclass
class _AVLNode:
    key: float
    value: float
    height: int = 1
    left: Optional["_AVLNode"] = None
    right: Optional["_AVLNode"] = None

class _AVLFrequencyTree:
    """
    AVL tree used as a frequency index.

    key   = frequency in MHz
    value = aggregated rx_mw for this exact frequency

    For the blocked-frequency tree we insert value=0.0 and only use the keys.
    For the mission-interference tree we aggregate rx_mw by frequency.
    """
    
    def __init__(self):
        self.root: Optional[_AVLNode] = None
        
    def insert(self, key: float, value: float = 0.0) -> None:
        self.root = self._insert(self.root, round(float(key), 6), float(value))
        
    def delete(self, key: float) -> None:
        self.root = self._delete(self.root, round(float(key),6))
        
    def nearest_left(self, key: float) -> Optional[float]:
        key = round(float(key), 6)
        current = self.root
        result = None
        
        while current is not None:
            if key < current.key:
                current = current.left
            else:
                result = current.key
                current = current.right
        return result
    
    def nearest_right(self, key: float) -> Optional[float]:
        key = round(float(key), 6)
        current = self.root
        result = None
        
        while current is not None:
            if key < current.key:
                current = current.right
            else:
                result = current.key
                current = current.left
        return result
    
    def has_key_in_radius(self, key: float, radius: float) -> bool:
        key = round(float(key), 6)
        radius = float(radius)
        
        left_key = self.nearest_left(key)
        if left_key is not None and abs(left_key - key) <= radius:
            return True
        
        right_key = self.nearest_right(key)
        if right_key is not None and abs(right_key - key) <= radius:
            return True
        
        return False
    
    def iter_range(self, low: float, high: float) -> Generator[tuple[float, float], None, None]:
        low = round(float(low), 6)
        high = round(float(high), 6)
        yield from self._iter_range(self.root, low, high)
        
        
    def _iter_range(self, node: Optional[_AVLNode], low: float, high: float) -> Generator[tuple[float, float], None, None]:
        if node is None: return
        
        if low < node.key:
            yield from self._iter_range(node.left, low, high)
            
        if low <= node.key <= high:
            yield (node.key, node.value)
            
        if node.key < high:
            yield from self.iter_range(node.right, low, high)
            
    