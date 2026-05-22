# AloneWork CLI 增强规划 / AloneWork CLI Enhancement Plan

## 核心理念：从"静态推理"到"为了行动而思考" / Core Philosophy: From Static Reasoning to Thinking for Action

### 范式转变 / Paradigm Shift

传统AI CLI的局限性在于**静态推理**——模型独立完成推理链后输出答案。而下一代产品的核心竞争力在于：

**"为了行动而思考"（Thinking for Action）**

关键特征：
- **交互性**：模型在环境中行动、接收反馈、修正计划、继续推进
- **系统性**：系统记录完整的"模型+环境"交互轨迹
- **数据输出**：收集对话数据，输出可用于训练的结构化数据

### 竞争优势的新来源 / New Source of Competitive Advantage

| 传统视角 | 新视角 |
|---------|--------|
| 更好的RL算法 | 更好的环境设计 |
| 更好的反馈信号 | 更好的轨迹采样基础设施 |
| 单模型优化 | 多智能体协调接口 |
| 静态推理链 | 动态行动-反馈循环 |
| 模型能力 | 评估器的鲁棒性 |

### 核心策略：数据收集而非直接训练

**不做直接训练，而是：**
1. **收集用户对话数据**：记录完整的用户-Agent交互过程
2. **输出训练数据**：生成结构化的训练数据格式
3. **环境轨迹记录**：记录完整的行动-观察-反馈轨迹
4. **质量评估**：评估交互质量，筛选高质量数据

---

## 一、现状分析 / Current Status Analysis

### 1.1 现有CLI功能

基于 `alonework-cli` 的现有功能：

| 功能模块 | 现状 | 增强方向 |
|----------|------|----------|
| **CLI入口** | ✅ 已实现 | 添加环境层命令 |
| **模型层** | ✅ DeepSeek V4 Flash | 保持单一模型，优化上下文缓存 |
| **Agent层** | ⚠️ 基础实现 | 增强为Supervisor-Worker架构 |
| **工具层** | ⚠️ 基础工具 | 扩展工具集，增强沙箱 |
| **上下文层** | ✅ 已实现 | 优化超大上下文管理 |
| **会话管理** | ✅ 已实现 | 增加环境状态持久化 |
| **工作流** | ❌ 未实现 | 新增工作流编排能力 |
| **环境层** | ❌ 未实现 | **核心新增** |
| **数据收集** | ❌ 未实现 | **新增：轨迹记录与数据输出** |

### 1.2 现有架构

```
alonework-cli/
├── src/alonechat/
│   ├── cli.py                 # CLI主入口 ✅
│   ├── commands/              # 命令模块 ✅
│   │   ├── agent.py          # Agent命令 ⚠️需增强
│   │   ├── chat.py           # 聊天命令 ✅
│   │   ├── generate.py       # 生成命令 ✅
│   │   ├── commit.py         # 提交命令 ✅
│   │   └── test.py           # 测试命令 ✅
│   ├── agents/                # Agent模块 ⚠️需增强
│   ├── models/                # 模型层 ✅
│   ├── context/               # 上下文层 ✅
│   ├── session/               # 会话管理 ✅
│   ├── permissions/           # 权限管理 ✅
│   ├── tools/                 # 工具层 ⚠️需增强
│   └── slash/commands/        # 斜杠命令 ✅
```

---

## 二、增强目标 / Enhancement Goals

### 2.1 核心增强目标

**目标：在现有CLI基础上，增加"环境原生"能力，实现"为了行动而思考"，并收集交互数据输出训练数据**

具体目标：
1. **环境层**：新增行动环境，支持Agent在环境中行动、接收反馈
2. **多Agent协作**：增强Agent层，实现Supervisor-Worker架构
3. **工作流编排**：新增工作流引擎，支持复杂任务编排
4. **状态管理**：增强状态管理，支持检查点和恢复
5. **反馈系统**：新增反馈机制，实现行动-反馈闭环
6. **数据收集**：新增轨迹记录器，收集并输出训练数据

### 2.2 保持不变的部分

- **模型层**：继续使用 DeepSeek V4 Flash 作为唯一模型
- **CLI框架**：继续使用 Click + Rich
- **配置系统**：继续使用 YAML 配置
- **会话管理**：在现有基础上增强
- **不做训练**：只收集数据，不进行在线训练

---

## 三、核心架构增强 / Core Architecture Enhancement

### 3.1 增强后的架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    AloneWork CLI Enhanced Architecture                  │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 5: CLI层 / CLI Layer (现有增强)                                   │
│  ├─ Commands (init, chat, generate, commit, test) ✅现有                │
│  ├─ Agent Commands (task, workflow, env) ⭐新增                          │
│  ├─ Data Commands (export, analyze) ⭐新增                               │
│  └─ Slash Commands (/help, /status, /workflow) ✅现有+增强               │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 4: 数据层 / Data Layer ⭐新增                                      │
│  ├─ Trajectory Recorder (轨迹记录器)                                     │
│  ├─ Data Collector (数据收集器)                                          │
│  ├─ Quality Evaluator (质量评估器)                                       │
│  └─ Data Exporter (数据导出器)                                           │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 3: 编排层 / Orchestration Layer ⭐新增                            │
│  ├─ Workflow Engine (工作流引擎)                                         │
│  ├─ Task Planner (任务规划器)                                            │
│  └─ Executor (执行器)                                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 2: 环境层 / Environment Layer ⭐核心新增                           │
│  ├─ Action Environment (行动环境)                                        │
│  │   ├─ Tool Registry (工具注册中心)                                     │
│  │   ├─ Resource Manager (资源管理器)                                    │
│  │   └─ Sandbox (安全沙箱)                                               │
│  ├─ Feedback System (反馈系统)                                           │
│  │   ├─ Observation Collector (观察收集器)                               │
│  │   ├─ Reward Calculator (奖励计算器)                                   │
│  │   └─ Error Analyzer (错误分析器)                                      │
│  └─ Environment State (环境状态)                                         │
│      ├─ World State (世界状态)                                           │
│      ├─ Agent States (各Agent状态)                                       │
│      └─ Interaction History (交互历史)                                   │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Agent层 / Agent Layer (现有增强)                               │
│  ├─ Supervisor Agent (主管Agent) ⭐新增                                   │
│  ├─ Worker Agents (工作Agent) ⭐增强                                      │
│  │   ├─ Code Agent (代码生成/修改) ✅现有+增强                            │
│  │   ├─ Data Agent (数据处理) ⭐新增                                      │
│  │   ├─ Research Agent (信息检索) ⭐新增                                  │
│  │   └─ Test Agent (测试验证) ✅现有+增强                                 │
│  ├─ Agent Communication (Agent间通信) ⭐新增                              │
│  └─ Reflection (反思机制) ⭐新增                                           │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 0: 基础层 / Foundation Layer (现有)                               │
│  ├─ Model Layer (DeepSeek V4 Flash) ✅保持不变                           │
│  ├─ Context Layer (超大上下文管理) ✅保持不变                             │
│  ├─ Session Layer (会话管理) ✅保持不变                                   │
│  ├─ Permissions Layer (权限管理) ✅保持不变                               │
│  └─ Tools Layer (工具集) ⚠️增强                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据层设计（核心新增）

```python
# 数据层核心设计 / Data Layer Core Design
# 文件: src/alonechat/data/trajectory.py

from dataclasses import dataclass, field
from typing import Any
from datetime import datetime
from uuid import uuid4

@dataclass
class InteractionStep:
    """交互步骤 / Interaction Step"""
    step_id: str
    timestamp: datetime
    
    # 用户输入
    user_input: str | None = None
    
    # Agent思考过程
    agent_thought: str | None = None
    
    # 行动
    action_type: str = ""
    action_params: dict[str, Any] = field(default_factory=dict)
    
    # 执行结果
    observation: dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = False
    
    # 反馈
    reward: float = 0.0
    feedback: str | None = None
    
    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Trajectory:
    """
    完整轨迹 / Complete Trajectory
    
    记录一次完整的用户-Agent交互过程
    """
    trajectory_id: str
    session_id: str
    start_time: datetime
    end_time: datetime | None = None
    
    # 任务信息
    task_description: str = ""
    task_type: str = ""
    
    # 交互步骤序列
    steps: list[InteractionStep] = field(default_factory=list)
    
    # 环境状态
    initial_state: dict[str, Any] = field(default_factory=dict)
    final_state: dict[str, Any] = field(default_factory=dict)
    
    # 质量评估
    quality_score: float = 0.0
    is_successful: bool = False
    
    # 元数据
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: InteractionStep) -> None:
        """添加交互步骤"""
        self.steps.append(step)
        
    def to_training_format(self) -> dict:
        """
        转换为训练数据格式 / Convert to training data format
        
        输出可用于训练的结构化数据
        """
        return {
            "id": self.trajectory_id,
            "task": {
                "description": self.task_description,
                "type": self.task_type,
            },
            "trajectory": [
                {
                    "thought": step.agent_thought,
                    "action": {
                        "type": step.action_type,
                        "params": step.action_params,
                    },
                    "observation": step.observation,
                    "reward": step.reward,
                }
                for step in self.steps
            ],
            "outcome": {
                "success": self.is_successful,
                "quality_score": self.quality_score,
                "final_state": self.final_state,
            },
            "metadata": self.metadata,
        }


class TrajectoryRecorder:
    """
    轨迹记录器 / Trajectory Recorder
    
    记录完整的交互轨迹，不做训练
    """
    
    def __init__(self, config: dict):
        self.trajectories: dict[str, Trajectory] = {}
        self.current_trajectory: Trajectory | None = None
        self.config = config
        
    def start_trajectory(
        self,
        session_id: str,
        task_description: str,
        task_type: str,
        initial_state: dict = None
    ) -> str:
        """开始新轨迹"""
        trajectory_id = str(uuid4())
        
        self.current_trajectory = Trajectory(
            trajectory_id=trajectory_id,
            session_id=session_id,
            start_time=datetime.now(),
            task_description=task_description,
            task_type=task_type,
            initial_state=initial_state or {},
        )
        
        self.trajectories[trajectory_id] = self.current_trajectory
        return trajectory_id
        
    def record_step(
        self,
        user_input: str | None,
        agent_thought: str | None,
        action_type: str,
        action_params: dict,
        observation: dict,
        result: Any,
        success: bool,
        reward: float,
        feedback: str | None = None
    ) -> None:
        """记录交互步骤"""
        if not self.current_trajectory:
            return
            
        step = InteractionStep(
            step_id=str(uuid4()),
            timestamp=datetime.now(),
            user_input=user_input,
            agent_thought=agent_thought,
            action_type=action_type,
            action_params=action_params,
            observation=observation,
            result=result,
            success=success,
            reward=reward,
            feedback=feedback,
        )
        
        self.current_trajectory.add_step(step)
        
    def end_trajectory(
        self,
        final_state: dict,
        quality_score: float,
        is_successful: bool
    ) -> Trajectory:
        """结束轨迹"""
        if not self.current_trajectory:
            return None
            
        self.current_trajectory.end_time = datetime.now()
        self.current_trajectory.final_state = final_state
        self.current_trajectory.quality_score = quality_score
        self.current_trajectory.is_successful = is_successful
        
        trajectory = self.current_trajectory
        self.current_trajectory = None
        return trajectory
```

### 3.3 数据收集与导出

```python
# 数据收集与导出 / Data Collection and Export
# 文件: src/alonechat/data/collector.py

import json
from pathlib import Path
from typing import Any
from datetime import datetime

class DataCollector:
    """
    数据收集器 / Data Collector
    
    收集并整理交互数据
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def collect_session_data(
        self,
        session_id: str,
        trajectories: list["Trajectory"]
    ) -> dict:
        """收集会话数据"""
        return {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "trajectories": [t.to_training_format() for t in trajectories],
            "statistics": self._compute_statistics(trajectories),
        }
        
    def _compute_statistics(
        self,
        trajectories: list["Trajectory"]
    ) -> dict:
        """计算统计信息"""
        if not trajectories:
            return {}
            
        return {
            "total_trajectories": len(trajectories),
            "successful_trajectories": sum(1 for t in trajectories if t.is_successful),
            "avg_quality_score": sum(t.quality_score for t in trajectories) / len(trajectories),
            "avg_steps": sum(len(t.steps) for t in trajectories) / len(trajectories),
            "total_steps": sum(len(t.steps) for t in trajectories),
        }


class QualityEvaluator:
    """
    质量评估器 / Quality Evaluator
    
    评估交互质量，筛选高质量数据
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.min_quality_threshold = config.get("min_quality_threshold", 0.5)
        
    def evaluate_trajectory(self, trajectory: "Trajectory") -> float:
        """评估轨迹质量"""
        scores = []
        
        # 1. 任务完成度
        if trajectory.is_successful:
            scores.append(1.0)
        else:
            scores.append(0.3)
            
        # 2. 步骤效率（步骤数是否合理）
        step_count = len(trajectory.steps)
        if step_count > 0:
            efficiency = min(1.0, 10.0 / step_count)  # 10步以内效率最高
            scores.append(efficiency)
            
        # 3. 奖励累积
        total_reward = sum(step.reward for step in trajectory.steps)
        if step_count > 0:
            avg_reward = total_reward / step_count
            scores.append(max(0, min(1, avg_reward + 0.5)))
            
        # 4. 错误率
        error_count = sum(1 for step in trajectory.steps if not step.success)
        if step_count > 0:
            error_rate = 1 - (error_count / step_count)
            scores.append(error_rate)
            
        return sum(scores) / len(scores) if scores else 0.0
        
    def is_high_quality(self, trajectory: "Trajectory") -> bool:
        """判断是否为高质量数据"""
        return trajectory.quality_score >= self.min_quality_threshold


class DataExporter:
    """
    数据导出器 / Data Exporter
    
    导出训练数据到各种格式
    """
    
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def export_to_jsonl(
        self,
        trajectories: list["Trajectory"],
        filename: str = "training_data.jsonl",
        high_quality_only: bool = True
    ) -> Path:
        """
        导出为JSONL格式 / Export to JSONL format
        
        每行一条轨迹数据，适合训练
        """
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            for trajectory in trajectories:
                if high_quality_only and trajectory.quality_score < 0.5:
                    continue
                    
                data = trajectory.to_training_format()
                f.write(json.dumps(data, ensure_ascii=False) + "\n")
                
        return output_path
        
    def export_to_json(
        self,
        data: dict,
        filename: str
    ) -> Path:
        """导出为JSON格式"""
        output_path = self.output_dir / filename
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        return output_path
        
    def export_statistics(
        self,
        trajectories: list["Trajectory"],
        filename: str = "statistics.json"
    ) -> Path:
        """导出统计信息"""
        stats = {
            "total_trajectories": len(trajectories),
            "successful_count": sum(1 for t in trajectories if t.is_successful),
            "high_quality_count": sum(1 for t in trajectories if t.quality_score >= 0.5),
            "quality_distribution": self._quality_distribution(trajectories),
            "task_type_distribution": self._task_type_distribution(trajectories),
            "step_count_distribution": self._step_count_distribution(trajectories),
        }
        
        return self.export_to_json(stats, filename)
        
    def _quality_distribution(self, trajectories: list) -> dict:
        """质量分布"""
        bins = {"0.0-0.2": 0, "0.2-0.4": 0, "0.4-0.6": 0, "0.6-0.8": 0, "0.8-1.0": 0}
        for t in trajectories:
            score = t.quality_score
            if score < 0.2:
                bins["0.0-0.2"] += 1
            elif score < 0.4:
                bins["0.2-0.4"] += 1
            elif score < 0.6:
                bins["0.4-0.6"] += 1
            elif score < 0.8:
                bins["0.6-0.8"] += 1
            else:
                bins["0.8-1.0"] += 1
        return bins
        
    def _task_type_distribution(self, trajectories: list) -> dict:
        """任务类型分布"""
        dist = {}
        for t in trajectories:
            task_type = t.task_type or "unknown"
            dist[task_type] = dist.get(task_type, 0) + 1
        return dist
        
    def _step_count_distribution(self, trajectories: list) -> dict:
        """步骤数分布"""
        dist = {}
        for t in trajectories:
            count = len(t.steps)
            bucket = f"{(count // 5) * 5}-{(count // 5) * 5 + 4}"
            dist[bucket] = dist.get(bucket, 0) + 1
        return dist
```

### 3.4 环境层设计（核心新增）

```python
# 环境层核心接口设计 / Environment Layer Core Interface Design
# 文件: src/alonechat/environment/action_env.py

from dataclasses import dataclass, field
from typing import Any
from enum import Enum

class ActionType(Enum):
    """行动类型 / Action Types"""
    TOOL_CALL = "tool_call"
    CODE_GENERATE = "code_generate"
    FILE_OPERATION = "file_operation"
    COMMUNICATE = "communicate"
    OBSERVE = "observe"
    REFLECT = "reflect"


@dataclass
class Action:
    """行动定义 / Action Definition"""
    type: ActionType
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Observation:
    """观察结果 / Observation Result"""
    world_state: dict[str, Any]
    agent_state: dict[str, Any]
    recent_actions: list[Action]
    messages: list[dict]
    errors: list[str]


@dataclass
class Reward:
    """奖励信号 / Reward Signal（用于数据收集，非训练）"""
    values: dict[str, float] = field(default_factory=dict)
    
    def add(self, name: str, value: float) -> None:
        self.values[name] = value
        
    def total(self) -> float:
        return sum(self.values.values())


@dataclass
class ActionResult:
    """行动结果 / Action Result"""
    success: bool
    output: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class ActionEnvironment:
    """
    行动环境 / Action Environment
    
    提供Agent行动的完整环境，记录交互轨迹（不做训练）
    """
    
    def __init__(self, config: dict, trajectory_recorder: "TrajectoryRecorder" = None):
        from .tools import ToolRegistry
        from .sandbox import Sandbox
        from .state import EnvironmentState
        from .feedback import FeedbackSystem
        
        self.tool_registry = ToolRegistry()
        self.sandbox = Sandbox(config.get("sandbox", {}))
        self.state = EnvironmentState()
        self.feedback_system = FeedbackSystem(config.get("feedback", {}))
        self.trajectory_recorder = trajectory_recorder
        
    async def step(
        self, 
        agent_id: str, 
        action: Action,
        agent_thought: str = None
    ) -> tuple[Observation, Reward, bool, dict]:
        """
        执行一步行动 / Execute one action step
        
        返回: (observation, reward, done, info)
        """
        # 1. 验证行动合法性
        if not self.sandbox.is_valid_action(action):
            return self._invalid_action_response(action)
            
        # 2. 执行行动
        result = await self._execute_action(agent_id, action)
        
        # 3. 更新环境状态
        self.state.update(agent_id, action, result)
        
        # 4. 收集观察
        observation = self.feedback_system.collect_observation(
            self.state, agent_id
        )
        
        # 5. 计算奖励（用于数据收集，非训练）
        reward = self.feedback_system.calculate_reward(
            action, result, self.state
        )
        
        # 6. 检查是否结束
        done = self._check_done(action, result)
        
        # 7. 记录轨迹（数据收集）
        if self.trajectory_recorder:
            self.trajectory_recorder.record_step(
                user_input=None,
                agent_thought=agent_thought,
                action_type=action.type.value,
                action_params=action.params,
                observation=observation.__dict__ if hasattr(observation, '__dict__') else {},
                result=result.output if result.success else result.error,
                success=result.success,
                reward=reward.total(),
                feedback=None
            )
        
        return observation, reward, done, {"result": result}
    
    async def _execute_action(
        self, 
        agent_id: str, 
        action: Action
    ) -> ActionResult:
        """执行具体行动"""
        if action.type == ActionType.TOOL_CALL:
            tool = self.tool_registry.get(action.name)
            return await tool.execute(action.params, context=self.state)
            
        elif action.type == ActionType.CODE_GENERATE:
            return await self._generate_code(action)
            
        elif action.type == ActionType.FILE_OPERATION:
            return await self._file_operation(action)
            
        elif action.type == ActionType.COMMUNICATE:
            return await self._agent_communicate(agent_id, action)
            
        elif action.type == ActionType.OBSERVE:
            return await self._observe(action)
            
        elif action.type == ActionType.REFLECT:
            return await self._reflect(action)
```

### 3.5 多Agent协作增强

```python
# 多智能体协作设计 / Multi-Agent Collaboration Design
# 文件: src/alonechat/agents/supervisor.py

from dataclasses import dataclass, field
from typing import Any

@dataclass
class Task:
    """任务定义 / Task Definition"""
    id: str
    description: str
    type: str
    params: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Subtask(Task):
    """子任务 / Subtask"""
    parent_id: str = ""
    assigned_agent: str = ""


@dataclass
class Plan:
    """执行计划 / Execution Plan"""
    task: Task
    subtasks: list[Subtask]
    dependencies: dict[str, list[str]]
    
    @property
    def execution_order(self) -> list[Subtask]:
        """返回拓扑排序后的执行顺序"""
        ...


class SupervisorAgent:
    """
    主管Agent / Supervisor Agent
    
    负责任务分解、分配、协调和监督
    不做训练，只记录交互数据
    """
    
    def __init__(self, model, environment, trajectory_recorder=None):
        self.model = model  # DeepSeek V4 Flash
        self.environment = environment
        self.trajectory_recorder = trajectory_recorder
        self.workers: dict[str, "WorkerAgent"] = {}
        
    def register_worker(self, worker: "WorkerAgent") -> None:
        """注册工作Agent"""
        self.workers[worker.id] = worker
        
    async def plan(self, task: Task) -> Plan:
        """任务规划"""
        # 1. 分析任务
        analysis = await self._analyze(task)
        
        # 2. 分解为子任务
        subtasks = await self._decompose(task, analysis)
        
        # 3. 分配给Worker
        assignments = await self._assign(subtasks)
        
        # 4. 生成执行计划
        plan = Plan(
            task=task,
            subtasks=subtasks,
            dependencies=self._build_dependencies(subtasks),
        )
        
        return plan
    
    async def coordinate(self, plan: Plan) -> dict:
        """协调执行"""
        results = {}
        
        for subtask in plan.execution_order:
            # 检查依赖是否满足
            if not self._check_dependencies(subtask, results):
                await self._handle_dependency_failure(subtask)
                continue
                
            # 分配给Worker执行
            worker = self._select_worker(subtask)
            result = await worker.execute(subtask, context=results)
            
            # 收集结果
            results[subtask.id] = result
            
            # 根据结果调整计划（动态重规划）
            if not result.success:
                plan = await self._replan(plan, subtask, result)
                
        return results
    
    async def _decompose(self, task: Task, analysis: dict) -> list[Subtask]:
        """使用DeepSeek分解任务"""
        prompt = f"""
分析以下任务，将其分解为可并行执行的子任务：

任务: {task.description}
类型: {task.type}
参数: {task.params}

分析结果: {analysis}

请输出JSON格式的子任务列表，每个子任务包含:
- id: 子任务ID
- description: 子任务描述
- type: 子任务类型 (code/data/research/test)
- dependencies: 依赖的其他子任务ID列表
"""
        response = await self.model.chat(prompt)
        ...
```

---

## 四、CLI命令增强 / CLI Commands Enhancement

### 4.1 新增数据命令

```python
# 数据命令 / Data Commands
# 文件: src/alonechat/commands/data.py

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


@click.group()
def data_commands():
    """数据命令组 / Data commands group"""
    pass


@data_commands.command("export")
@click.option("--format", "-f", type=click.Choice(["jsonl", "json"]), default="jsonl", help="输出格式")
@click.option("--output", "-o", type=click.Path(), default="./training_data", help="输出目录")
@click.option("--high-quality-only", is_flag=True, help="仅导出高质量数据")
@click.option("--min-quality", type=float, default=0.5, help="最低质量阈值")
def export_data(format: str, output: str, high_quality_only: bool, min_quality: float):
    """
    导出训练数据 / Export training data
    
    示例 / Examples:
        alonework data export
        alonework data export --format jsonl --high-quality-only
        alonework data export --output ./my_data --min-quality 0.7
    """
    from ..data.collector import DataCollector
    from ..data.exporter import DataExporter
    
    output_dir = Path(output)
    exporter = DataExporter(output_dir)
    
    # 加载轨迹数据
    trajectories = _load_trajectories()
    
    # 过滤高质量数据
    if high_quality_only:
        trajectories = [t for t in trajectories if t.quality_score >= min_quality]
    
    # 导出
    if format == "jsonl":
        output_path = exporter.export_to_jsonl(trajectories, high_quality_only=high_quality_only)
    else:
        data = {"trajectories": [t.to_training_format() for t in trajectories]}
        output_path = exporter.export_to_json(data, "training_data.json")
    
    # 导出统计信息
    stats_path = exporter.export_statistics(trajectories)
    
    console.print(f"[green]数据已导出到: {output_path}[/green]")
    console.print(f"[green]统计信息: {stats_path}[/green]")


@data_commands.command("analyze")
@click.option("--session", "-s", help="会话ID")
def analyze_data(session: str):
    """
    分析收集的数据 / Analyze collected data
    
    示例 / Examples:
        alonework data analyze
        alonework data analyze --session abc123
    """
    from ..data.collector import DataCollector
    from ..data.quality import QualityEvaluator
    
    trajectories = _load_trajectories(session)
    evaluator = QualityEvaluator({})
    
    # 显示统计表格
    table = Table(title="数据分析结果 / Data Analysis Results")
    table.add_column("指标", style="cyan")
    table.add_column("值", style="green")
    
    table.add_row("总轨迹数", str(len(trajectories)))
    table.add_row("成功轨迹", str(sum(1 for t in trajectories if t.is_successful)))
    table.add_row("高质量数据", str(sum(1 for t in trajectories if t.quality_score >= 0.5)))
    table.add_row("平均质量分", f"{sum(t.quality_score for t in trajectories) / len(trajectories):.2f}" if trajectories else "N/A")
    
    console.print(table)


@data_commands.command("stats")
def show_stats():
    """显示数据统计 / Show data statistics"""
    ...


# 环境命令 / Environment Commands
@click.group()
def env_commands():
    """环境命令组 / Environment commands group"""
    pass


@env_commands.command("init")
@click.option("--name", "-n", default="default", help="环境名称")
def init_env(name: str):
    """初始化环境 / Initialize environment"""
    ...


@env_commands.command("status")
def env_status():
    """查看环境状态 / View environment status"""
    ...


@env_commands.command("checkpoint")
@click.option("--name", "-n", help="检查点名称")
def create_checkpoint(name: str):
    """创建检查点 / Create checkpoint"""
    ...


@env_commands.command("restore")
@click.argument("checkpoint_id")
def restore_checkpoint(checkpoint_id: str):
    """恢复检查点 / Restore checkpoint"""
    ...
```

### 4.2 Agent命令增强

```python
# Agent命令增强 / Agent Commands Enhancement
# 文件: src/alonechat/commands/agent.py (增强)

@click.group()
def agent_commands():
    """Agent命令组 / Agent commands group"""
    pass


@agent_commands.command("task")
@click.argument("description")
@click.option("--type", "-t", default="auto", help="任务类型")
@click.option("--workers", "-w", default=4, help="Worker数量")
@click.option("--interactive", "-i", is_flag=True, help="交互模式")
@click.option("--record/--no-record", default=True, help="是否记录轨迹")
def run_task(description: str, type: str, workers: int, interactive: bool, record: bool):
    """
    执行任务（使用Supervisor-Worker架构）
    
    示例 / Examples:
        alonework agent task "实现用户登录功能"
        alonework agent task "重构代码库" --workers 8
        alonework agent task "修复所有测试" --interactive
        alonework agent task "分析代码" --no-record
    """
    from ..agents.supervisor import SupervisorAgent
    from ..environment import ActionEnvironment
    from ..data.trajectory import TrajectoryRecorder
    
    # 创建轨迹记录器（数据收集）
    trajectory_recorder = TrajectoryRecorder({}) if record else None
    
    # 创建环境
    env = ActionEnvironment.load_default(trajectory_recorder)
    
    # 创建Supervisor
    supervisor = SupervisorAgent(
        model=get_model(),  # DeepSeek V4 Flash
        environment=env,
        trajectory_recorder=trajectory_recorder
    )
    
    # 注册Workers
    supervisor.register_worker(CodeAgent(env))
    supervisor.register_worker(DataAgent(env))
    supervisor.register_worker(ResearchAgent(env))
    supervisor.register_worker(TestAgent(env))
    
    # 开始轨迹记录
    if trajectory_recorder:
        trajectory_id = trajectory_recorder.start_trajectory(
            session_id=get_session_id(),
            task_description=description,
            task_type=type,
            initial_state=env.state.snapshot()
        )
    
    # 规划并执行
    task = Task(id="main", description=description, type=type)
    plan = await supervisor.plan(task)
    results = await supervisor.coordinate(plan)
    
    # 结束轨迹记录
    if trajectory_recorder:
        trajectory = trajectory_recorder.end_trajectory(
            final_state=env.state.snapshot(),
            quality_score=evaluate_quality(results),
            is_successful=all(r.success for r in results.values())
        )
        console.print(f"[dim]轨迹已记录: {trajectory.trajectory_id}[/dim]")
    
    # 输出结果
    ...
```

---

## 五、目录结构增强 / Directory Structure Enhancement

### 5.1 新增目录和文件

```
alonework-cli/src/alonechat/
├── data/                          # ⭐ 新增：数据层
│   ├── __init__.py
│   ├── trajectory.py             # 轨迹记录
│   ├── collector.py              # 数据收集
│   ├── quality.py                # 质量评估
│   └── exporter.py               # 数据导出
├── environment/                   # ⭐ 新增：环境层
│   ├── __init__.py
│   ├── action_env.py             # 行动环境
│   ├── feedback.py               # 反馈系统
│   ├── state.py                  # 环境状态
│   ├── sandbox.py                # 安全沙箱
│   └── tools/                    # 工具注册
│       ├── __init__.py
│       ├── registry.py
│       ├── file_ops.py
│       ├── code_exec.py
│       └── api_call.py
├── agents/                        # 增强：Agent层
│   ├── __init__.py
│   ├── base.py                   # 基础Agent (增强)
│   ├── supervisor.py             # ⭐ 新增：主管Agent
│   ├── workers/                  # ⭐ 新增：工作Agent
│   │   ├── __init__.py
│   │   ├── code_agent.py
│   │   ├── data_agent.py
│   │   ├── research_agent.py
│   │   └── test_agent.py
│   ├── communication.py          # ⭐ 新增：Agent通信
│   └── reflection.py             # ⭐ 新增：反思机制
├── orchestration/                 # ⭐ 新增：编排层
│   ├── __init__.py
│   ├── workflow.py               # 工作流引擎
│   ├── planner.py                # 任务规划器
│   ├── executor.py               # 执行器
│   └── nodes/                    # 工作流节点
│       ├── __init__.py
│       ├── triggers.py
│       ├── actions.py
│       ├── controls.py
│       └── feedback.py
├── commands/                      # 增强：命令层
│   ├── data.py                   # ⭐ 新增：数据命令
│   ├── workflow.py               # ⭐ 新增：工作流命令
│   ├── env.py                    # ⭐ 新增：环境命令
│   └── agent.py                  # 增强：Agent命令
├── configs/                       # 增强：配置层
│   ├── data.yaml                 # ⭐ 新增：数据配置
│   ├── environment.yaml          # ⭐ 新增：环境配置
│   ├── workflow.yaml             # ⭐ 新增：工作流配置
│   └── agents.yaml               # ⭐ 新增：Agent配置
└── ... (其他现有文件保持不变)
```

### 5.2 配置文件设计

```yaml
# configs/data.yaml - 数据配置

data:
  collection:
    enabled: true
    record_trajectories: true
    record_steps: true
    
  storage:
    type: "sqlite"
    path: "${HOME}/.alonework/data/trajectories.db"
    
  export:
    default_format: "jsonl"
    output_dir: "${HOME}/.alonework/exports"
    high_quality_threshold: 0.5
    
  quality:
    min_quality_threshold: 0.5
    weights:
      task_completion: 0.4
      efficiency: 0.2
      reward: 0.2
      error_rate: 0.2
```

```yaml
# configs/environment.yaml - 环境配置

environment:
  type: action
  
  sandbox:
    enabled: true
    timeout: 300
    memory_limit: "1GB"
    allowed_paths:
      - "${HOME}/projects"
      - "${PWD}"
      
  feedback:
    reward_weights:
      task_completion: 1.0
      efficiency: 0.3
      code_quality: 0.5
      collaboration: 0.2
      
  state:
    checkpoint_enabled: true
    checkpoint_interval: 60
    persistence: "sqlite"
```

```yaml
# configs/agents.yaml - Agent配置

supervisor:
  model: deepseek-v4-flash
  max_workers: 4
  planning_depth: 3
  reflection_enabled: true
  timeout: 600

workers:
  code_agent:
    enabled: true
    tools:
      - file_ops
      - code_execute
      - git
    languages:
      - python
      - javascript
      - typescript
      
  data_agent:
    enabled: true
    tools:
      - database
      - spreadsheet
      - api
      
  research_agent:
    enabled: true
    tools:
      - web_search
      - document_read
      
  test_agent:
    enabled: true
    tools:
      - pytest
      - coverage
```

---

## 六、实施路线图 / Implementation Roadmap

### Phase 1: 数据层基础（1周）

**目标**：实现数据收集与导出

**任务**：
- [ ] 创建 `data/` 目录结构
- [ ] 实现 `Trajectory` 和 `InteractionStep` 数据结构
- [ ] 实现 `TrajectoryRecorder` 轨迹记录器
- [ ] 实现 `DataCollector` 数据收集器
- [ ] 实现 `QualityEvaluator` 质量评估器
- [ ] 实现 `DataExporter` 数据导出器
- [ ] 添加配置文件 `data.yaml`

**交付物**：
- 数据层核心代码
- 单元测试
- 配置文件

### Phase 2: 环境层基础（2周）

**目标**：实现核心环境层

**任务**：
- [ ] 创建 `environment/` 目录结构
- [ ] 实现 `ActionEnvironment` 核心类
- [ ] 实现 `FeedbackSystem` 反馈系统
- [ ] 实现 `EnvironmentState` 状态管理
- [ ] 实现 `Sandbox` 安全沙箱
- [ ] 实现 `ToolRegistry` 工具注册
- [ ] 集成轨迹记录
- [ ] 添加配置文件 `environment.yaml`

**交付物**：
- 环境层核心代码
- 单元测试
- 配置文件

### Phase 3: Agent层增强（2周）

**目标**：实现Supervisor-Worker架构

**任务**：
- [ ] 实现 `SupervisorAgent` 主管Agent
- [ ] 实现 `WorkerAgent` 基类
- [ ] 实现 `CodeAgent` 代码Agent
- [ ] 实现 `DataAgent` 数据Agent
- [ ] 实现 `ResearchAgent` 研究Agent
- [ ] 增强 `TestAgent` 测试Agent
- [ ] 实现 `AgentCommunication` Agent通信
- [ ] 实现 `Reflection` 反思机制
- [ ] 添加配置文件 `agents.yaml`

**交付物**：
- Agent层代码
- 单元测试
- 集成测试

### Phase 4: 工作流引擎（1周）

**目标**：实现工作流编排能力

**任务**：
- [ ] 创建 `orchestration/` 目录结构
- [ ] 实现 `WorkflowEngine` 工作流引擎
- [ ] 实现 `TaskPlanner` 任务规划器
- [ ] 实现各类节点
- [ ] 添加配置文件 `workflow.yaml`

**交付物**：
- 工作流引擎代码
- 工作流模板
- 单元测试

### Phase 5: CLI命令增强（1周）

**目标**：添加新命令

**任务**：
- [ ] 实现 `data` 命令组
- [ ] 实现 `workflow` 命令组
- [ ] 实现 `env` 命令组
- [ ] 增强 `agent` 命令
- [ ] 更新 CLI 帮助文档

**交付物**：
- CLI命令代码
- 命令文档

### Phase 6: 集成与测试（1周）

**目标**：集成测试和文档

**任务**：
- [ ] 集成测试
- [ ] 端到端测试
- [ ] 数据导出测试
- [ ] 文档更新
- [ ] 示例工作流

**交付物**：
- 测试报告
- 更新的文档
- 示例代码

---

## 七、风险与缓解 / Risks & Mitigation

### 7.1 技术风险

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| 环境设计复杂度高 | 延期 | 高 | 分阶段实现、参考现有框架 |
| 多Agent协调困难 | 性能问题 | 中 | 充分测试、性能优化 |
| 数据收集影响性能 | 性能下降 | 中 | 异步记录、批量写入 |
| 与现有代码冲突 | 集成问题 | 低 | 保持接口兼容、渐进增强 |

### 7.2 缓解策略

1. **渐进式增强**：不破坏现有功能，逐步添加新能力
2. **充分测试**：每个阶段完成后进行充分测试
3. **文档同步**：代码和文档同步更新
4. **性能优化**：数据收集使用异步方式，不影响主流程

---

## 八、成功指标 / Success Metrics

### 8.1 功能指标

| 指标 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|------|---------|---------|---------|---------|---------|---------|
| 数据层完整度 | 100% | 100% | 100% | 100% | 100% | 100% |
| 环境层完整度 | 0% | 80% | 100% | 100% | 100% | 100% |
| Agent协作能力 | 0% | 0% | 50% | 80% | 90% | 100% |
| 工作流能力 | 0% | 0% | 0% | 70% | 90% | 100% |
| 测试覆盖率 | 60% | 70% | 75% | 80% | 85% | 85% |

### 8.2 数据质量指标

| 指标 | 目标值 |
|------|--------|
| 高质量数据比例 | > 60% |
| 轨迹完整性 | > 95% |
| 数据导出成功率 | > 99% |
| 平均轨迹质量分 | > 0.6 |

---

## 九、总结 / Summary

### 核心增强点

1. **数据层**：新增轨迹记录、数据收集、质量评估、数据导出
2. **环境层**：新增行动环境，实现"为了行动而思考"
3. **多Agent协作**：Supervisor-Worker架构，支持复杂任务分解
4. **工作流编排**：新增工作流引擎，支持复杂任务编排
5. **反馈系统**：新增反馈机制，实现行动-反馈闭环

### 保持不变

- **模型**：继续使用 DeepSeek V4 Flash
- **CLI框架**：继续使用 Click + Rich
- **现有功能**：所有现有命令和功能保持兼容
- **不做训练**：只收集数据，输出训练数据格式

### 成功关键

1. **数据收集**：记录完整交互轨迹，输出高质量训练数据
2. **环境设计**：核心竞争力，需要持续投入
3. **质量评估**：筛选高质量数据，提升数据价值
4. **测试覆盖**：确保质量和稳定性

---

**文档版本**：v1.0  
**创建时间**：2026-05-18  
**作者**：AloneWork Team
