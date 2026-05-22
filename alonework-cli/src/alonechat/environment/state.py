"""
环境状态模块 / Environment State Module

管理整个环境的完整状态，支持检查点和恢复
Manages complete environment state, supports checkpoint and restore
"""

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from uuid import uuid4
import json


@dataclass
class WorldState:
    """
    世界状态 / World State
    
    表示环境的全局状态
    Represents global state of the environment
    """
    variables: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "variables": self.variables,
            "resources": self.resources,
            "metadata": self.metadata,
        }
    
    def from_dict(self, data: dict[str, Any]) -> None:
        """从字典加载 / Load from dictionary"""
        self.variables = data.get("variables", {})
        self.resources = data.get("resources", {})
        self.metadata = data.get("metadata", {})
    
    def set_variable(self, name: str, value: Any) -> None:
        """
        设置变量 / Set variable
        
        Args:
            name: 变量名 / Variable name
            value: 变量值 / Variable value
        """
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """
        获取变量 / Get variable
        
        Args:
            name: 变量名 / Variable name
            default: 默认值 / Default value
            
        Returns:
            变量值 / Variable value
        """
        return self.variables.get(name, default)
    
    def add_resource(self, name: str, resource: Any) -> None:
        """
        添加资源 / Add resource
        
        Args:
            name: 资源名 / Resource name
            resource: 资源对象 / Resource object
        """
        self.resources[name] = resource
    
    def get_resource(self, name: str) -> Any | None:
        """
        获取资源 / Get resource
        
        Args:
            name: 资源名 / Resource name
            
        Returns:
            资源对象 / Resource object
        """
        return self.resources.get(name)


@dataclass
class AgentState:
    """
    Agent状态 / Agent State
    
    表示单个Agent的状态
    Represents state of a single Agent
    """
    agent_id: str
    status: str = "idle"
    current_task: str | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "current_task": self.current_task,
            "variables": self.variables,
            "history": self.history[-100:] if len(self.history) > 100 else self.history,
            "errors": self.errors[-50:] if len(self.errors) > 50 else self.errors,
            "messages": self.messages[-50:] if len(self.messages) > 50 else self.messages,
            "metadata": self.metadata,
        }
    
    def from_dict(self, data: dict[str, Any]) -> None:
        """从字典加载 / Load from dictionary"""
        self.agent_id = data.get("agent_id", self.agent_id)
        self.status = data.get("status", "idle")
        self.current_task = data.get("current_task")
        self.variables = data.get("variables", {})
        self.history = data.get("history", [])
        self.errors = data.get("errors", [])
        self.messages = data.get("messages", [])
        self.metadata = data.get("metadata", {})
    
    def set_status(self, status: str) -> None:
        """
        设置状态 / Set status
        
        Args:
            status: 状态字符串 / Status string
        """
        self.status = status
    
    def set_task(self, task: str | None) -> None:
        """
        设置当前任务 / Set current task
        
        Args:
            task: 任务描述 / Task description
        """
        self.current_task = task
    
    def add_history(
        self,
        action: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """
        添加历史记录 / Add history record
        
        Args:
            action: 行动记录 / Action record
            result: 结果记录 / Result record
        """
        self.history.append({
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        
        if len(self.history) > 1000:
            self.history = self.history[-500:]
    
    def add_error(self, error: str) -> None:
        """
        添加错误 / Add error
        
        Args:
            error: 错误信息 / Error message
        """
        self.errors.append(f"[{datetime.now().isoformat()}] {error}")
        
        if len(self.errors) > 100:
            self.errors = self.errors[-50:]
    
    def add_message(self, message: dict[str, Any]) -> None:
        """
        添加消息 / Add message
        
        Args:
            message: 消息对象 / Message object
        """
        self.messages.append(message)
        
        if len(self.messages) > 100:
            self.messages = self.messages[-50:]
    
    def get_pending_messages(self) -> list[dict[str, Any]]:
        """
        获取待处理消息 / Get pending messages
        
        Returns:
            待处理消息列表 / List of pending messages
        """
        pending = [m for m in self.messages if not m.get("read", False)]
        for m in pending:
            m["read"] = True
        return pending


@dataclass
class InteractionHistory:
    """
    交互历史 / Interaction History
    
    记录所有Agent的交互历史
    Records interaction history of all Agents
    """
    records: list[dict[str, Any]] = field(default_factory=list)
    
    def record(
        self,
        agent_id: str,
        action: dict[str, Any],
        result: dict[str, Any],
    ) -> None:
        """
        记录交互 / Record interaction
        
        Args:
            agent_id: Agent标识 / Agent identifier
            action: 行动记录 / Action record
            result: 结果记录 / Result record
        """
        self.records.append({
            "agent_id": agent_id,
            "action": action,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        
        if len(self.records) > 10000:
            self.records = self.records[-5000:]
    
    def get_by_agent(
        self,
        agent_id: str,
        n: int = 10,
    ) -> list[dict[str, Any]]:
        """
        按Agent获取记录 / Get records by agent
        
        Args:
            agent_id: Agent标识 / Agent identifier
            n: 数量 / Count
            
        Returns:
            记录列表 / List of records
        """
        agent_records = [
            r for r in self.records
            if r["agent_id"] == agent_id
        ]
        return agent_records[-n:] if agent_records else []
    
    def to_dict(self) -> list[dict[str, Any]]:
        """转换为字典 / Convert to dictionary"""
        return self.records[-1000:] if len(self.records) > 1000 else self.records
    
    def from_dict(self, records: list[dict[str, Any]]) -> None:
        """从字典加载 / Load from dictionary"""
        self.records = records


class EnvironmentState:
    """
    环境状态 / Environment State
    
    管理整个环境的完整状态，支持检查点和恢复
    Manages complete environment state, supports checkpoint and restore
    """
    
    def __init__(self):
        """初始化环境状态 / Initialize environment state"""
        self.world = WorldState()
        self.agents: dict[str, AgentState] = {}
        self.history = InteractionHistory()
        self._message_queue: list[dict[str, Any]] = []
    
    def update(
        self,
        agent_id: str,
        action: Any,
        result: Any,
    ) -> None:
        """
        更新状态 / Update state
        
        Args:
            agent_id: Agent标识 / Agent identifier
            action: 行动对象 / Action object
            result: 结果对象 / Result object
        """
        if agent_id not in self.agents:
            self.agents[agent_id] = AgentState(agent_id=agent_id)
        
        action_dict = action.to_dict() if hasattr(action, 'to_dict') else {}
        result_dict = result.to_dict() if hasattr(result, 'to_dict') else {}
        
        self.agents[agent_id].add_history(action_dict, result_dict)
        
        if hasattr(result, 'error') and result.error:
            self.agents[agent_id].add_error(result.error)
        
        self.history.record(agent_id, action_dict, result_dict)
    
    def add_message(
        self,
        from_agent: str,
        to_agent: str,
        message: str,
        message_type: str = "info",
    ) -> None:
        """
        添加消息 / Add message
        
        Args:
            from_agent: 发送者 / Sender
            to_agent: 接收者 / Receiver
            message: 消息内容 / Message content
            message_type: 消息类型 / Message type
        """
        msg = {
            "from": from_agent,
            "to": to_agent,
            "content": message,
            "type": message_type,
            "read": False,
            "timestamp": datetime.now().isoformat(),
        }
        
        if to_agent in self.agents:
            self.agents[to_agent].add_message(msg)
        else:
            self._message_queue.append(msg)
    
    def get_pending_messages(
        self,
        agent_id: str,
    ) -> list[dict[str, Any]]:
        """
        获取待处理消息 / Get pending messages
        
        Args:
            agent_id: Agent标识 / Agent identifier
            
        Returns:
            待处理消息列表 / List of pending messages
        """
        if agent_id in self.agents:
            return self.agents[agent_id].get_pending_messages()
        return []
    
    def get_recent_actions(
        self,
        agent_id: str,
        n: int = 10,
    ) -> list[dict[str, Any]]:
        """
        获取最近的行动 / Get recent actions
        
        Args:
            agent_id: Agent标识 / Agent identifier
            n: 数量 / Count
            
        Returns:
            行动列表 / List of actions
        """
        if agent_id in self.agents:
            history = self.agents[agent_id].history[-n:]
            return [h["action"] for h in history]
        return []
    
    def get_recent_errors(
        self,
        agent_id: str,
        n: int = 5,
    ) -> list[str]:
        """
        获取最近的错误 / Get recent errors
        
        Args:
            agent_id: Agent标识 / Agent identifier
            n: 数量 / Count
            
        Returns:
            错误列表 / List of errors
        """
        if agent_id in self.agents:
            return self.agents[agent_id].errors[-n:]
        return []
    
    def to_dict(self) -> dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "world": self.world.to_dict(),
            "agents": {
                k: v.to_dict() for k, v in self.agents.items()
            },
            "history": self.history.to_dict(),
        }
    
    def from_dict(self, data: dict[str, Any]) -> None:
        """从字典加载 / Load from dictionary"""
        self.world.from_dict(data.get("world", {}))
        
        agents_data = data.get("agents", {})
        self.agents = {}
        for k, v in agents_data.items():
            agent_state = AgentState(agent_id=k)
            agent_state.from_dict(v)
            self.agents[k] = agent_state
        
        self.history.from_dict(data.get("history", []))
    
    def reset(self) -> None:
        """重置状态 / Reset state"""
        self.world = WorldState()
        self.agents = {}
        self.history = InteractionHistory()
        self._message_queue = []
    
    def snapshot(self) -> dict[str, Any]:
        """
        创建快照 / Create snapshot
        
        Returns:
            快照数据 / Snapshot data
        """
        return self.to_dict()
    
    def restore(self, snapshot: dict[str, Any]) -> None:
        """
        从快照恢复 / Restore from snapshot
        
        Args:
            snapshot: 快照数据 / Snapshot data
        """
        self.from_dict(snapshot)
