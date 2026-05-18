# MCP功能增强实施计划

## 1. 项目概述

### 当前状态分析

项目中已存在基础的MCP Marketplace实现：
- **位置**: `agent_framework/deepseek_optimization/mcp_marketplace/`
- **已实现**: 
  - MCP类型定义 (`types.py`)
  - MCP服务器注册表 (`registry.py`)
  - MCP协议客户端 (`client.py`)
  - MCP服务器加载器 (`loader.py`)

### 需要增强的功能

| 功能模块 | 优先级 | 说明 |
|---------|--------|------|
| MCP工具适配器 | 高 | 将MCP工具转换为BaseTool，集成到现有工具系统 |
| MCP API端点 | 高 | 在gateway中添加MCP管理API |
| MCP配置管理 | 中 | 在config.yaml中添加MCP配置项 |
| MCP前端界面 | 中 | 在user-client中添加MCP管理页面 |
| MCP服务发现 | 低 | 自动发现可用的MCP服务器 |
| 调用历史记录 | 低 | 记录MCP工具调用历史 |

---

## 2. 架构设计

### 2.1 模块结构

```
agent-framework/
├── agent_framework/
│   ├── deepseek_optimization/
│   │   └── mcp_marketplace/
│   │       ├── __init__.py          # 已存在
│   │       ├── types.py             # 已存在
│   │       ├── registry.py          # 已存在
│   │       ├── client.py            # 已存在
│   │       ├── loader.py            # 已存在
│   │       ├── adapter.py           # 新增: MCP工具适配器
│   │       ├── manager.py           # 新增: MCP管理器
│   │       └── config.py            # 新增: MCP配置
│   ├── gateway/
│   │   ├── api.py                   # 修改: 添加MCP API
│   │   └── mcp_api.py               # 新增: MCP专用API路由
│   └── config.py                    # 修改: 添加MCP配置加载
```

### 2.2 前端结构

```
user-client/
└── src/
    ├── app/(dashboard)/
    │   └── mcp/                      # 新增: MCP管理页面
    │       └── page.tsx
    ├── components/
    │   └── mcp/                      # 新增: MCP组件
    │       ├── server-list.tsx
    │       ├── server-card.tsx
    │       ├── tool-list.tsx
    │       └── server-form.tsx
    └── stores/
        └── mcp-store.ts              # 新增: MCP状态管理
```

---

## 3. 实施步骤

### 阶段1: MCP工具适配器 (核心集成)

**目标**: 将MCP工具无缝集成到现有的工具系统中

#### 步骤1.1: 创建MCP工具适配器
- 文件: `agent_framework/deepseek_optimization/mcp_marketplace/adapter.py`
- 功能:
  - `MCPToolAdapter` 类继承 `BaseTool`
  - 将MCP工具定义转换为 `ToolDef`
  - 实现异步工具调用支持
  - 处理MCP工具的错误和超时

#### 步骤1.2: 创建MCP管理器
- 文件: `agent_framework/deepseek_optimization/mcp_marketplace/manager.py`
- 功能:
  - 统一管理MCP服务器和工具
  - 自动将活跃服务器的工具注册到 `ToolRegistry`
  - 提供工具调用的统一入口
  - 管理服务器生命周期

#### 步骤1.3: 更新模块导出
- 文件: `agent_framework/deepseek_optimization/mcp_marketplace/__init__.py`
- 添加新模块的导出

---

### 阶段2: MCP配置管理

**目标**: 支持通过配置文件管理MCP服务器

#### 步骤2.1: 创建MCP配置模块
- 文件: `agent_framework/deepseek_optimization/mcp_marketplace/config.py`
- 功能:
  - 定义MCP配置的数据结构
  - 支持从YAML文件加载配置
  - 支持环境变量替换
  - 配置验证

#### 步骤2.2: 更新主配置文件
- 文件: `config.yaml`
- 添加MCP配置节:
```yaml
mcp:
  enabled: true
  servers:
    - name: "filesystem"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "./data"]
      auto_start: true
    - name: "brave-search"
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-brave-search"]
      env:
        BRAVE_API_KEY: "${BRAVE_API_KEY}"
      auto_start: false
  default_timeout: 30
  max_concurrent_calls: 10
```

---

### 阶段3: MCP API端点

**目标**: 提供完整的MCP管理REST API

#### 步骤3.1: 创建MCP API路由
- 文件: `agent_framework/gateway/mcp_api.py`
- API端点:
  - `GET /api/mcp/servers` - 列出所有MCP服务器
  - `POST /api/mcp/servers` - 注册新服务器
  - `GET /api/mcp/servers/{id}` - 获取服务器详情
  - `PATCH /api/mcp/servers/{id}` - 更新服务器配置
  - `DELETE /api/mcp/servers/{id}` - 删除服务器
  - `POST /api/mcp/servers/{id}/start` - 启动服务器
  - `POST /api/mcp/servers/{id}/stop` - 停止服务器
  - `GET /api/mcp/servers/{id}/tools` - 获取服务器工具列表
  - `POST /api/mcp/tools/call` - 调用MCP工具
  - `GET /api/mcp/tools` - 列出所有可用工具
  - `GET /api/mcp/stats` - 获取MCP统计信息

#### 步骤3.2: 集成到主API
- 文件: `agent_framework/gateway/api.py`
- 添加MCP API路由

---

### 阶段4: 前端界面

**目标**: 提供用户友好的MCP管理界面

#### 步骤4.1: 创建MCP状态管理
- 文件: `user-client/src/stores/mcp-store.ts`
- 状态:
  - 服务器列表
  - 当前选中的服务器
  - 工具列表
  - 加载状态
  - 错误信息

#### 步骤4.2: 创建MCP组件
- 文件: `user-client/src/components/mcp/`
  - `server-list.tsx` - 服务器列表组件
  - `server-card.tsx` - 服务器卡片组件
  - `tool-list.tsx` - 工具列表组件
  - `server-form.tsx` - 服务器配置表单

#### 步骤4.3: 创建MCP页面
- 文件: `user-client/src/app/(dashboard)/mcp/page.tsx`
- 功能:
  - 服务器管理面板
  - 工具浏览器
  - 调用测试界面

#### 步骤4.4: 更新导航
- 文件: `user-client/src/components/layout/sidebar.tsx`
- 添加MCP导航项

---

### 阶段5: 集成与测试

#### 步骤5.1: Agent集成
- 修改 `ReActAgent` 支持MCP工具
- 确保工具调用正确路由到MCP服务器

#### 步骤5.2: 编写测试
- 文件: `tests/test_mcp_integration.py`
- 测试用例:
  - MCP服务器注册/注销
  - 工具发现和调用
  - 错误处理
  - 并发调用

---

## 4. 详细实现规范

### 4.1 MCPToolAdapter 实现规范

```python
class MCPToolAdapter(BaseTool):
    """
    将MCP工具适配为BaseTool接口
    """
    def __init__(
        self,
        mcp_tool: MCPTool,
        server_id: str,
        loader: MCPServerLoader,
    ):
        self.mcp_tool = mcp_tool
        self.server_id = server_id
        self.loader = loader
        self.name = f"mcp_{server_id}_{mcp_tool.name}"
        self.description = mcp_tool.description
        self.parameters = self._convert_parameters()
    
    def execute(self, **kwargs) -> Any:
        """同步执行（内部使用asyncio.run）"""
        return asyncio.run(self.execute_async(**kwargs))
    
    async def execute_async(self, **kwargs) -> Any:
        """异步执行MCP工具调用"""
        result = await self.loader.call_tool(
            self.server_id,
            self.mcp_tool.name,
            kwargs,
        )
        return result
```

### 4.2 MCPManager 实现规范

```python
class MCPManager:
    """
    MCP管理器 - 统一管理MCP服务器和工具
    """
    def __init__(self, tool_registry: ToolRegistry):
        self.registry = MCPServerRegistry()
        self.loader = MCPServerLoader(self.registry)
        self.tool_registry = tool_registry
        self._tool_adapters: Dict[str, MCPToolAdapter] = {}
    
    async def register_and_start(
        self,
        name: str,
        config: MCPServerConfig,
        auto_register_tools: bool = True,
    ) -> MCPServer:
        """注册并启动服务器，自动注册工具"""
        server = self.registry.register_server(name, config)
        await self.loader.start_server(server.id)
        
        if auto_register_tools:
            await self._register_tools(server.id)
        
        return server
    
    async def _register_tools(self, server_id: str):
        """将服务器工具注册到ToolRegistry"""
        server = self.registry.get_server(server_id)
        for tool in server.tools:
            adapter = MCPToolAdapter(tool, server_id, self.loader)
            self.tool_registry.register(adapter)
            self._tool_adapters[adapter.name] = adapter
```

### 4.3 API响应格式

```python
# 服务器列表响应
{
    "servers": [
        {
            "id": "uuid",
            "name": "filesystem",
            "status": "active",
            "tool_count": 5,
            "last_connected_at": "2026-05-16T10:00:00Z"
        }
    ],
    "total": 1
}

# 工具调用请求
{
    "server_id": "uuid",
    "tool_name": "read_file",
    "arguments": {
        "path": "/path/to/file.txt"
    }
}

# 工具调用响应
{
    "success": true,
    "result": {
        "content": "file content..."
    },
    "execution_time_ms": 150.5
}
```

---

## 5. 依赖和注意事项

### 5.1 新增依赖
- 无需新增Python依赖（使用现有的asyncio、pydantic等）

### 5.2 安全考虑
1. MCP服务器在子进程中运行，需要适当的权限控制
2. API端点需要认证保护
3. 工具调用需要超时控制
4. 敏感环境变量需要安全处理

### 5.3 性能考虑
1. 使用连接池管理MCP服务器连接
2. 工具调用结果可缓存
3. 并发调用需要限制

---

## 6. 文件变更清单

### 新增文件
| 文件路径 | 说明 |
|---------|------|
| `agent_framework/deepseek_optimization/mcp_marketplace/adapter.py` | MCP工具适配器 |
| `agent_framework/deepseek_optimization/mcp_marketplace/manager.py` | MCP管理器 |
| `agent_framework/deepseek_optimization/mcp_marketplace/config.py` | MCP配置 |
| `agent_framework/gateway/mcp_api.py` | MCP API路由 |
| `user-client/src/stores/mcp-store.ts` | MCP状态管理 |
| `user-client/src/components/mcp/server-list.tsx` | 服务器列表组件 |
| `user-client/src/components/mcp/server-card.tsx` | 服务器卡片组件 |
| `user-client/src/components/mcp/tool-list.tsx` | 工具列表组件 |
| `user-client/src/components/mcp/server-form.tsx` | 服务器表单组件 |
| `user-client/src/app/(dashboard)/mcp/page.tsx` | MCP管理页面 |
| `tests/test_mcp_integration.py` | MCP集成测试 |

### 修改文件
| 文件路径 | 变更说明 |
|---------|---------|
| `agent_framework/deepseek_optimization/mcp_marketplace/__init__.py` | 添加新模块导出 |
| `agent_framework/gateway/api.py` | 集成MCP API路由 |
| `agent_framework/config.py` | 添加MCP配置加载 |
| `config.yaml` | 添加MCP配置节 |
| `user-client/src/components/layout/sidebar.tsx` | 添加MCP导航项 |

---

## 7. 预期成果

完成本计划后，系统将具备以下能力：

1. **无缝集成**: MCP工具与现有工具系统完全集成，Agent可以透明地使用MCP工具
2. **便捷管理**: 通过API和UI管理MCP服务器
3. **灵活配置**: 支持通过配置文件预定义MCP服务器
4. **安全可控**: 完善的权限控制和错误处理
5. **易于扩展**: 支持动态添加新的MCP服务器
