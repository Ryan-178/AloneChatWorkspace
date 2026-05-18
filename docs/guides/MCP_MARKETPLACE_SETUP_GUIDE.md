
# DeepSeek MCP 市场 - 安装和使用指南

## ✅ 已完成的工作

### 1. 核心模块 (agent-framework)
- ✅ `types.py` - 完整的 MCP 类型定义
- ✅ `registry.py` - MCP 服务器注册表
- ✅ `client.py` - MCP 协议客户端
- ✅ `loader.py` - 服务器加载器和生命周期管理
- ✅ `__init__.py` - 模块入口

### 2. 后端 API (chat-app/backend)
- ✅ `models/mcp_marketplace.py` - 数据库模型
- ✅ `schemas/mcp_marketplace.py` - API 数据验证
- ✅ `routers/mcp_marketplace.py` - RESTful API 路由
- ✅ 集成到 `main.py` - 添加路由
- ✅ 数据库迁移文件

## 🚀 快速开始

### 步骤 1: 数据库设置

#### 1. 确保 PostgreSQL 正在运行
```bash
# Windows
net start postgresql-x64-15  # 或您的版本

# macOS/Linux
brew services start postgresql
# 或
sudo systemctl start postgresql
```

#### 2. 创建数据库（如果尚未创建）
```sql
CREATE DATABASE chatapp;
```

#### 3. 运行数据库迁移
```bash
cd chat-app/backend

# 激活虚拟环境（如果有）
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 运行迁移
alembic upgrade head
```

### 步骤 2: 安装依赖

```bash
cd chat-app/backend
pip install -r requirements.txt
```

### 步骤 3: 启动服务器

```bash
cd chat-app/backend
uvicorn main:app --reload
```

服务器将在 http://localhost:8000 上运行

### 步骤 4: 访问 API 文档

打开浏览器访问: http://localhost:8000/docs

## 📡 API 使用示例

### 1. 创建 MCP 服务器
```http
POST /api/v1/mcp-marketplace/servers
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "name": "Filesystem MCP",
  "description": "Access local filesystem",
  "version": "1.0.0",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:\\path\\to\\files"],
  "env": {},
  "timeout": 30
}
```

### 2. 列出所有服务器
```http
GET /api/v1/mcp-marketplace/servers
Authorization: Bearer YOUR_TOKEN
```

### 3. 启动服务器
```http
POST /api/v1/mcp-marketplace/servers/{server_id}/action
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "action": "start"
}
```

### 4. 列出服务器工具
```http
GET /api/v1/mcp-marketplace/servers/{server_id}/tools
Authorization: Bearer YOUR_TOKEN
```

### 5. 调用工具
```http
POST /api/v1/mcp-marketplace/servers/{server_id}/tools/call
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN

{
  "tool_name": "read_file",
  "arguments": {
    "path": "/path/to/file.txt"
  }
}
```

## 📋 数据库表结构

### `mcp_servers` 表
| 字段 | 类型 | 描述 |
|------|------|
| id | UUID | 主键 |
| user_id | UUID | 用户 ID（外键） |
| name | VARCHAR(200) | 服务器名称 |
| description | TEXT | 描述 |
| version | VARCHAR(50) | 版本号 |
| command | VARCHAR(500) | 启动命令 |
| args | JSON | 命令参数 |
| env | JSON | 环境变量 |
| cwd | VARCHAR(500) | 工作目录 |
| timeout | INTEGER | 超时时间(秒) |
| status | VARCHAR(20) | 状态: inactive/active/error/starting/stopping |
| error_message | TEXT | 错误信息 |
| tools | JSON | 可用工具 |
| last_connected_at | TIMESTAMP | 最后连接时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

## 🔧 故障排除

### 问题: Alembic 迁移失败
如果遇到异步驱动问题，修改 `alembic.ini`：
```ini
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/chatapp
```
（去掉 `+asyncpg`）

### 问题: 服务器无法连接 MCP 服务器
- 检查命令是否正确
- 验证环境变量
- 查看错误消息

## 📝 开发路线图

- [ ] 前端界面
- [ ] 工具调用历史记录
- [ ] MCP 服务器发现
- [ ] 用户权限管理
- [ ] 服务器健康检查

## 📞 帮助

如有问题，请检查 API 文档或查看服务器日志！

