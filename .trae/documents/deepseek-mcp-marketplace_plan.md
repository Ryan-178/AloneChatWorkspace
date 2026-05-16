# DeepSeek MCP 市场 - 实施计划

## 1. 项目概述

DeepSeek MCP 市场是一个专门为 DeepSeek 优化的模型上下文协议（MCP）工具市场，提供 MCP 服务器的发现、安装、配置和管理功能。

### 核心愿景

* 构建 DeepSeek 生态的专属工具市场

* 提供简单易用的 MCP 工具发现与安装体验

* 与现有 agent 框架无缝集成

***

## 2. 仓库研究结论

### 现有架构分析

1. **工具系统** (`agent_framework/tools/`): 已有完整的工具注册机制，包括 `BaseTool` 基类和 `ToolRegistry`
2. **API 框架** (`chat-app/backend/`): 使用 FastAPI，已有用户认证、会话管理等基础设施
3. **DeepSeek 优化** (`agent_framework/deepseek_optimization/`): 已有 DeepSeek 专用的 LLM provider
4. **数据库** (`chat-app/backend/models.py`): 使用 SQLAlchemy + AsyncPG

### 设计风格

* RESTful API 设计

* Pydantic 用于数据验证

* 分页、筛选、错误处理模式已在现有代码中确立

***

## 3. 架构设计

### 模块结构

```
agent_framework/
└── deepseek_optimization/
    └── mcp_marketplace/
        ├── __init__.py
        ├── models.py          # MCP 服务器数据模型
        ├── registry.py        # MCP 注册表
        ├── loader.py          # MCP 服务器加载器
        ├── client.py          # MCP 客户端
        └── types.py           # 类型定义

chat-app/
└── backend/
    ├── routers/
    │   └── mcp_marketplace.py  # MCP 市场 API 路由
    ├── schemas/
    │   └── mcp_marketplace.py  # Pydantic 模式
    └── models/
        └── mcp_marketplace.py  # 数据库模型
```

### API 资源设计

```
/api/v1/mcp-marketplace
├── /servers              [GET]     列出 MCP 服务器
├── /servers              [POST]    添加 MCP 服务器
├── /servers/{id}         [GET]     获取服务器详情
├── /servers/{id}         [PATCH]   更新服务器配置
├── /servers/{id}         [DELETE]  删除服务器
├── /servers/{id}/tools   [GET]     获取服务器提供的工具
└── /discover             [POST]    发现可用的 MCP 服务器
```

***

## 4. 文件和模块列表

### 需要修改/新增的文件

#### 1. 核心模块 (`agent_framework/`)

* **新增** `agent_framework/deepseek_optimization/mcp_marketplace/__init__.py`

* **新增** `agent_framework/deepseek_optimization/mcp_marketplace/types.py`

* **新增** `agent_framework/deepseek_optimization/mcp_marketplace/models.py`

* **新增** `agent_framework/deepseek_optimization/mcp_marketplace/registry.py`

* **新增** `agent_framework/deepseek_optimization/mcp_marketplace/loader.py`

* **新增** `agent_framework/deepseek_optimization/mcp_marketplace/client.py`

#### 2. 后端 API (`chat-app/backend/`)

* **新增** `chat-app/backend/models/mcp_marketplace.py`

* **新增** `chat-app/backend/schemas/mcp_marketplace.py`

* **新增** `chat-app/backend/routers/mcp_marketplace.py`

* **修改** `chat-app/backend/main.py` (集成新路由)

#### 3. 前端 (`chat-app/frontend/`)

* **新增** `chat-app/frontend/src/components/mcp-marketplace/`

  * `MarketplaceHome.tsx`

  * `ServerList.tsx`

  * `ServerDetail.tsx`

  * `ToolExplorer.tsx`

* **新增** `chat-app/frontend/src/app/mcp-marketplace/page.tsx`

***

## 5. 实施步骤

### 阶段 1: 核心数据模型和类型定义

1. 定义 MCP 相关的 Pydantic 类型 (`types.py`)
2. 创建 SQLAlchemy 数据库模型 (`models.py`)
3. 定义 API 请求/响应模式 (`schemas.py`)

### 阶段 2: MCP 客户端和注册表

1. 实现 MCP 协议客户端 (`client.py`)
2. 实现 MCP 服务器注册表 (`registry.py`)
3. 实现服务器加载器 (`loader.py`)

### 阶段 3: REST API 端点

1. 实现 `/api/v1/mcp-marketplace/servers` CRUD 端点
2. 实现工具发现端点
3. 集成认证和权限控制

### 阶段 4: 前端界面

1. 创建 MCP 市场主页
2. 实现服务器列表和详情视图
3. 实现工具浏览器

### 阶段 5: 集成与测试

1. 与现有 agent 框架集成
2. 编写单元测试
3. 端到端测试

***

## 6. 潜在依赖和注意事项

### 新增依赖

* `mcp` (MCP 协议 SDK)

* 可能需要 `asyncio-subprocess` 用于启动 MCP 服务器进程

### 安全考虑

1. MCP 服务器执行需要沙箱环境
2. API 端点需要认证保护
3. 防止恶意 MCP 服务器

### 性能考虑

1. MCP 工具调用需要超时控制
2. 服务器状态需要缓存
3. 异步处理长运行操作

***

## 7. 风险处理

| 风险        | 影响 | 概率 | 缓解措施           |
| --------- | -- | -- | -------------- |
| MCP 协议变更  | 高  | 中  | 抽象协议层，支持多版本    |
| 安全漏洞      | 高  | 中  | 沙箱执行、权限控制、审计日志 |
| 服务器进程管理   | 中  | 高  | 使用进程管理器、健康检查   |
| 与现有工具系统冲突 | 中  | 低  | 适配器模式，保持兼容性    |

