# MTC (More Than Coding) 模式实现计划

## 项目概述

实现Trae Solo的MTC模式，这是一个面向非开发用户的AI工作模式，运行在沙箱环境中，支持文档处理、数据分析、信息调研等通用办公任务。

## 架构设计

### 核心组件

1. **模式管理层 (Mode Management)**

   * AgentMode枚举定义

   * ModeConfig配置类

   * 模式切换机制

2. **沙箱执行层 (Sandbox Execution)**

   * 项目文件夹隔离

   * 受限文件操作权限

   * 安全命令执行

3. **MTC Skills体系**

   * 文档处理技能

   * 数据分析技能

   * 信息调研技能

4. **意图澄清系统 (Intent Clarification)**

   * 需求追问表单

   * 上下文收集

5. **任务管理面板 (Task Dashboard)**

   * 待办事项管理

   * 进度追踪

   * 产出物展示

## 实施步骤

### Phase 1: 基础架构搭建 (Week 1)

#### Step 1: 定义模式枚举和配置

**文件**: `agent-framework/agent_framework/core/types.py`

* 添加AgentMode枚举(MTC, CODE)

* 添加ModeConfig类定义

* 定义FilePermission枚举

* 添加ExecutionEnvironment枚举

**文件**: `agent-framework/agent_framework/config.py`

* 添加MTCSettings配置类

* 扩展AgentConfig支持mode字段

#### Step 2: 创建MTC Agent实现

**文件**: `agent-framework/agent_framework/agent/mtc_agent.py` (新建)

* 继承ReActAgent或BaseAgent

* 实现MTC专用的system prompt

* 支持沙箱环境配置

* 实现意图澄清逻辑

* 添加任务规划能力

#### Step 3: 实现模式路由

**文件**: `agent-framework/agent_framework/gateway/router.py`

* 添加模式路由逻辑

* 根据mode选择对应Agent

* 实现模式切换API

**文件**: `agent-framework/agent_framework/gateway/core.py`

* 支持mode参数传入

* 模式切换后的状态管理

### Phase 2: 沙箱环境实现 (Week 2)

#### Step 4: 增强沙箱模块

**文件**: `agent-framework/agent_framework/sandbox/subprocess_sandbox.py`

* 实现项目文件夹隔离

* 添加文件系统权限控制

* 支持受限命令白名单

* 实现沙箱超时和退出机制

#### Step 5: 创建MTC工具集

**目录**: `agent-framework/agent_framework/tools/mtc/` (新建)

* `document_tools.py`: 文档生成/编辑

* `data_tools.py`: 数据分析/处理

* `research_tools.py`: 信息调研/搜索

* `file_tools.py`: 文件操作(受限)

**文件**: `agent-framework/agent_framework/tools/mtc/__init__.py`

* 注册MTC专用工具

#### Step 6: 实现MTC System Prompt

**文件**: `agent-framework/agent_framework/agent/mtc_prompts.py` (新建)

* MTC模式专用提示词

* 意图澄清模板

* 任务规划模板

* 多格式输出指导

### Phase 3: Skills体系构建 (Week 3)

#### Step 7: Skills注册系统

**文件**: `agent-framework/agent_framework/tools/skills_registry.py` (新建)

* Skills定义和注册

* Skills元数据管理

* Skills加载/卸载

* Skills依赖解析

#### Step 8: 内置MTC Skills

**目录**: `agent-framework/agent_framework/skills/mtc/` (新建)

* `document_generation/`: 文档生成技能

* `data_analysis/`: 数据分析技能

* `web_research/`: 网络调研技能

* `ppt_generation/`: PPT生成技能

* `report_generation/`: 报告生成技能

每个Skill包含:

* `__init__.py`: Skill注册

* `workflow.py`: 工作流定义

* `tools.py`: 使用的工具

* `templates/`: 输出模板

#### Step 9: Skills市场接口

**文件**: `agent-framework/agent_framework/tools/skills_marketplace.py` (新建)

* Skills列表API

* Skills安装/卸载

* Skills版本管理

* Skills元数据查询

### Phase 4: 任务管理系统 (Week 3-4)

#### Step 10: 任务规划器

**文件**: `agent-framework/agent_framework/agent/task_planner.py` (新建)

* 任务分解逻辑

* 依赖关系管理

* 进度追踪

* 状态持久化

**文件**: `agent-framework/agent_framework/core/task.py` (新建)

* Task数据模型

* Task状态枚举

* Task依赖关系

#### Step 11: 意图澄清系统

**文件**: `agent-framework/agent_framework/agent/intent_clarifier.py` (新建)

* 需求分析

* 追问表单生成

* 上下文收集

* 澄清结果整合

#### Step 12: 右侧面板数据结构

**文件**: `agent-framework/agent_framework/gateway/types.py`

* 添加TaskBoard模型

* 添加Artifact模型

* 添加Reference模型

* 支持流式更新

### Phase 5: API和集成 (Week 4)

#### Step 13: REST API实现

**文件**: `agent-framework/agent_framework/gateway/api.py` (新建)

* `/api/mode` - 模式切换

* `/api/tasks` - 任务管理

* `/api/skills` - Skills管理

* `/api/artifacts` - 产出物管理

#### Step 14: WebSocket流式输出

**文件**: `agent-framework/agent_framework/gateway/websocket.py` (新建)

* 任务进度流式推送

* Agent思考过程推送

* 产出物更新推送

* 错误处理

#### Step 15: 集成测试

**文件**: `agent-framework/tests/test_mtc_mode.py` (新建)

* MTC模式创建测试

* 沙箱隔离测试

* Skills调用测试

* 意图澄清测试

* 任务规划测试

## 文件结构变更

```
agent-framework/agent_framework/
├── agent/
│   ├── mtc_agent.py          [新建] MTC Agent实现
│   ├── mtc_prompts.py        [新建] MTC提示词模板
│   ├── task_planner.py       [新建] 任务规划器
│   └── intent_clarifier.py   [新建] 意图澄清器
├── core/
│   ├── types.py              [修改] 添加模式相关类型
│   └── task.py               [新建] Task数据模型
├── tools/
│   ├── mtc/                  [新建目录] MTC工具集
│   │   ├── document_tools.py
│   │   ├── data_tools.py
│   │   ├── research_tools.py
│   │   └── file_tools.py
│   ├── skills_registry.py    [新建] Skills注册系统
│   └── skills_marketplace.py [新建] Skills市场
├── skills/
│   └── mtc/                  [新建目录] MTC Skills
│       ├── document_generation/
│       ├── data_analysis/
│       ├── web_research/
│       ├── ppt_generation/
│       └── report_generation/
├── sandbox/
│   └── subprocess_sandbox.py [修改] 增强沙箱功能
├── gateway/
│   ├── router.py             [修改] 添加模式路由
│   ├── core.py               [修改] 支持模式参数
│   ├── types.py              [修改] 添加任务面板类型
│   ├── api.py                [新建] REST API
│   └── websocket.py          [新建] WebSocket推送
└── config.py                 [修改] 添加MTC配置
```

## 技术栈和依赖

* **沙箱**: 扩展现有subprocess\_sandbox，可选Docker集成

* **Skills**: 基于现有ToolRegistry扩展

* **API**: FastAPI (已有)

* **WebSocket**: FastAPI WebSocket支持

* **配置**: Pydantic Settings (已有)

## 验收标准

1. [ ] 可创建MTC模式Agent实例
2. [ ] 模式切换功能正常
3. [ ] 沙箱环境正确隔离项目文件夹
4. [ ] MTC专用工具可正常调用
5. [ ] Skills注册和加载成功
6. [ ] 意图澄清功能工作正常
7. [ ] 任务规划可正确分解任务
8. [ ] 流式输出功能正常
9. [ ] REST API和WebSocket接口可用
10. [ ] 所有测试用例通过

## 风险和缓解措施

| 风险         | 影响 | 缓解措施         |
| ---------- | -- | ------------ |
| 沙箱安全性      | 高  | 严格权限控制，命令白名单 |
| Skills加载性能 | 中  | 延迟加载，缓存机制    |
| 意图澄清过度     | 低  | 可配置追问次数上限    |
| 上下文窗口限制    | 中  | 上下文压缩，优先级管理  |

## 下一步行动

1. 确认计划范围和优先级
2. 开始Phase 1实现
3. 每周review进度
4. 持续集成和测试

