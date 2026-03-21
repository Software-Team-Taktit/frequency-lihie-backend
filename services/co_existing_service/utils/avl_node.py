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
            
    def _insert(self, node: Optional[_AVLNode], key: float, value: float) -> _AVLNode:
        if node is None: return _AVLNode(key = key, value = value)
        
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            node.value += value
            return node
        
        self._update_height(node)
        return self._rebalance(node)
    
    def _delete(self, node: Optional[_AVLNode], key: float) -> Optional[_AVLNode]:
        if node is None:
            return None

        if key < node.key:
            node.left = self._delete(node.left, key)
        elif key > node.key:
            node.right = self._delete(node.right, key)
        else:
            if node.left is None:
                return node.right

            if node.right is None:
                return node.left

            successor = self._min_value_node(node.right)
            node.key = successor.key
            node.value = successor.value
            node.right = self._delete(node.right, successor.key)

        self._update_height(node)
        return self._rebalance(node)
    
    def _min_value_node(self, node: _AVLNode) -> _AVLNode:
        current = node
        while current.left is not None:
            current = current.left
        return current
    
    @staticmethod
    def _height(node: Optional[_AVLNode]) -> int:
        return node.height if node is not None else 0
    
    def _update_height(self, node: _AVLNode) -> None:
        node.height = 1 + max(self._height(node.left), self._height(node.right))
        
    def _balance_factor(self, node: _AVLNode) -> int:
        return self._height(node.left) - self._height(node.right)
    
    def _rebalance(self, node: _AVLNode) -> _AVLNode:
        balance = self._balance_factor(node)
        
        if balance > 1:
            if self._balance_factor(node.left) < 0:
                node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        
        if balance < -1:
            if self._balance_factor(node.right) > 0:
                node.right = self._rotate_right(node.right)
            return self._rotate_left(node)
        
        return node
    
    def _rotate_left(self, z: _AVLNode) -> _AVLNode:
        y = z.right
        t2 = y.left
        
        y.left = z
        z.right = t2
        
        self._update_height(z)
        self._update_height(y)
        return y
    
    def _rotate_right(self, z: _AVLNode) -> _AVLNode:
        y = z.left
        t3 = y.right
        
        y.right = z
        z.left = t3
        
        self._update_height(z)
        self._update_height(y)
        return y