"""
响应式状态存储 / Reactive State Store

参考 claude-code-claude 的 createStore 模式
Reference: claude-code-claude's createStore pattern

提供不可变状态管理和订阅机制
Provides immutable state management and subscription mechanism
"""

from typing import TypeVar, Generic, Callable, Set, Optional, Any
from dataclasses import dataclass, field

T = TypeVar('T')

# 类型别名 / Type aliases
Listener = Callable[[], None]
StateUpdater = Callable[[T], T]
OnChangeCallback = Callable[[T, T], None]  # (new_state, old_state)


@dataclass
class Store(Generic[T]):
    """
    响应式状态存储 / Reactive state store
    
    特性 / Features:
    - 不可变状态更新 / Immutable state updates
    - 订阅-通知机制 / Subscribe-notify mechanism
    - 状态变更回调 / State change callback
    
    使用示例 / Usage Example:
        store = create_store({"count": 0})
        store.set_state(lambda s: {**s, "count": s["count"] + 1})
        unsubscribe = store.subscribe(lambda: print("State changed!"))
    """
    _state: T
    _listeners: Set[Listener] = field(default_factory=set)
    _on_change: Optional[OnChangeCallback] = None
    
    def get_state(self) -> T:
        """
        获取当前状态 / Get current state
        
        Returns:
            当前状态对象 / Current state object
        """
        return self._state
    
    def set_state(self, updater: StateUpdater[T]) -> None:
        """
        更新状态 / Update state
        
        使用 updater 函数计算新状态，如果新状态与旧状态相同（引用相等），
        则不触发通知。
        Uses updater function to compute new state. If new state is the same
        as old state (reference equal), notifications are not triggered.
        
        Args:
            updater: 状态更新函数 / State update function
        """
        prev = self._state
        next_state = updater(prev)
        
        # 引用相等检查 / Reference equality check
        if next_state is prev:
            return
        
        self._state = next_state
        
        # 触发回调 / Trigger callback
        if self._on_change:
            self._on_change(next_state, prev)
        
        # 通知订阅者 / Notify subscribers
        for listener in self._listeners.copy():
            try:
                listener()
            except Exception:
                pass  # 防止单个监听器错误影响其他监听器
    
    def subscribe(self, listener: Listener) -> Callable[[], None]:
        """
        订阅状态变更 / Subscribe to state changes
        
        Args:
            listener: 状态变更时调用的函数 / Function to call on state change
            
        Returns:
            取消订阅函数 / Unsubscribe function
        """
        self._listeners.add(listener)
        
        def unsubscribe() -> None:
            self._listeners.discard(listener)
        
        return unsubscribe
    
    def get_listener_count(self) -> int:
        """
        获取当前监听器数量 / Get current listener count
        
        Returns:
            监听器数量 / Number of listeners
        """
        return len(self._listeners)


def create_store(
    initial_state: T,
    on_change: Optional[OnChangeCallback] = None
) -> Store[T]:
    """
    创建状态存储 / Create state store
    
    工厂函数，创建并返回一个新的 Store 实例。
    Factory function that creates and returns a new Store instance.
    
    Args:
        initial_state: 初始状态 / Initial state
        on_change: 可选的状态变更回调 / Optional state change callback
        
    Returns:
        新的 Store 实例 / New Store instance
        
    使用示例 / Usage Example:
        from alonechat.core.store import create_store
        
        # 创建简单状态存储 / Create simple state store
        store = create_store({"count": 0, "name": "test"})
        
        # 订阅变更 / Subscribe to changes
        unsubscribe = store.subscribe(lambda: print("Changed!"))
        
        # 更新状态 / Update state
        store.set_state(lambda s: {**s, "count": s["count"] + 1})
        
        # 取消订阅 / Unsubscribe
        unsubscribe()
    """
    return Store(_state=initial_state, _listeners=set(), _on_change=on_change)


class StoreManager:
    """
    存储管理器 / Store Manager
    
    管理多个命名存储实例
    Manages multiple named store instances
    """
    
    def __init__(self) -> None:
        self._stores: dict[str, Store[Any]] = {}
    
    def create(
        self,
        name: str,
        initial_state: T,
        on_change: Optional[OnChangeCallback] = None
    ) -> Store[T]:
        """
        创建命名存储 / Create named store
        
        Args:
            name: 存储名称 / Store name
            initial_state: 初始状态 / Initial state
            on_change: 状态变更回调 / State change callback
            
        Returns:
            创建的存储实例 / Created store instance
            
        Raises:
            ValueError: 如果名称已存在 / If name already exists
        """
        if name in self._stores:
            raise ValueError(f"Store '{name}' already exists")
        
        store = create_store(initial_state, on_change)
        self._stores[name] = store
        return store
    
    def get(self, name: str) -> Optional[Store[Any]]:
        """
        获取命名存储 / Get named store
        
        Args:
            name: 存储名称 / Store name
            
        Returns:
            存储实例或 None / Store instance or None
        """
        return self._stores.get(name)
    
    def remove(self, name: str) -> bool:
        """
        移除命名存储 / Remove named store
        
        Args:
            name: 存储名称 / Store name
            
        Returns:
            是否成功移除 / Whether successfully removed
        """
        if name in self._stores:
            del self._stores[name]
            return True
        return False
    
    def list_stores(self) -> list[str]:
        """
        列出所有存储名称 / List all store names
        
        Returns:
            存储名称列表 / List of store names
        """
        return list(self._stores.keys())


# 全局存储管理器实例 / Global store manager instance
_global_store_manager = StoreManager()


def get_store_manager() -> StoreManager:
    """
    获取全局存储管理器 / Get global store manager
    
    Returns:
        全局存储管理器实例 / Global store manager instance
    """
    return _global_store_manager
