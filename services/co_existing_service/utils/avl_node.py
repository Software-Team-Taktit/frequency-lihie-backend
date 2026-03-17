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
        
    