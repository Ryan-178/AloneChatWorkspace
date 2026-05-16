# Skills.sh 市场接入实施计划

## 目标
将 skills.sh 网站的 skill 接入到现有的 skill 市场系统中，实现远程 skill 的搜索、浏览和安装功能。

## 现有系统分析

### 后端结构
- `agent_framework/tools/skills_marketplace.py` - 本地 skill 市场管理
- `agent_framework/tools/skills_registry.py` - skill 注册表
- `agent_framework/gateway/api.py` - REST API 端点

### 前端结构
- `user-client/src/lib/api/skills.ts` - skill API 客户端
- `user-client/src/app/(dashboard)/skills/page.tsx` - skill 市场页面
- `user-client/src/types/skill.ts` - skill 类型定义

### Skills.sh API 端点
根据调研，skills.sh 提供以下 API：
- `https://skills.sh/api/search?q=<query>` - 搜索 skill
- `https://skills.sh/api/skills/search` - 技能名称匹配
- skill 详情页格式: `https://skills.sh/<owner>/<repo>/<skill-name>`

## 实施步骤

### 步骤 1: 创建 Skills.sh API 客户端 (后端)
**文件**: `agent_framework/tools/skills_sh_client.py`

创建一个 HTTP 客户端类，负责与 skills.sh API 通信：
- `search(query: str)` - 搜索远程 skill
- `get_skill_details(owner: str, repo: str, skill_name: str)` - 获取 skill 详情
- `get_trending()` - 获取热门 skill
- `get_skill_content(github_url: str)` - 从 GitHub 获取 SKILL.md 内容

### 步骤 2: 扩展 SkillsMarketplace 类
**文件**: `agent_framework/tools/skills_marketplace.py`

在现有 `SkillsMarketplace` 类中添加：
- `_remote_client: SkillsShClient` - skills.sh 客户端实例
- `search_remote(query: str)` - 搜索远程 skill
- `get_remote_skill(skill_id: str)` - 获取远程 skill 详情
- `install_from_remote(skill_id: str)` - 从远程安装 skill
- `list_trending()` - 获取热门 skill 列表

### 步骤 3: 扩展 API 端点
**文件**: `agent_framework/gateway/api.py`

添加新的 REST API 端点：
- `GET /api/skills/remote/search?q=<query>` - 搜索远程 skill
- `GET /api/skills/remote/trending` - 获取热门远程 skill
- `GET /api/skills/remote/<owner>/<repo>/<skill_name>` - 获取远程 skill 详情
- `POST /api/skills/remote/install` - 从远程安装 skill

### 步骤 4: 扩展前端类型定义
**文件**: `user-client/src/types/skill.ts`

添加新的类型定义：
- `RemoteSkill` - 远程 skill 类型（包含 owner, repo, installs, stars 等）
- `RemoteSkillInstallRequest` - 远程安装请求类型

### 步骤 5: 扩展前端 API 客户端
**文件**: `user-client/src/lib/api/skills.ts`

添加新的 API 方法：
- `searchRemote(query: string)` - 搜索远程 skill
- `getTrending()` - 获取热门 skill
- `getRemoteSkill(owner, repo, skillName)` - 获取远程 skill 详情
- `installFromRemote(skillId: string)` - 从远程安装

### 步骤 6: 更新前端 UI
**文件**: `user-client/src/app/(dashboard)/skills/page.tsx`

更新 skill 市场页面：
- 添加"本地/远程"切换标签
- 显示远程 skill 列表（包含安装数、star 数）
- 添加安装按钮
- 添加搜索远程 skill 功能

## API 设计规范

### 远程 Skill 数据结构
```typescript
interface RemoteSkill {
  id: string              // owner/repo/skill-name 格式
  name: string            // skill 名称
  description: string     // 描述
  owner: string           // GitHub owner
  repo: string            // GitHub 仓库名
  installs: number        // 安装数
  stars: number           // GitHub stars
  topic?: string          // 分类主题
  url: string             // skills.sh 链接
  github_url: string      // GitHub 链接
  security_audits?: SecurityAudit[]
}
```

### API 响应格式
```typescript
// GET /api/skills/remote/search?q=react
{
  skills: RemoteSkill[],
  total: number,
  query: string
}

// GET /api/skills/remote/trending
{
  skills: RemoteSkill[],
  period: "24h" | "7d" | "all"
}

// POST /api/skills/remote/install
{
  skill_id: string,  // owner/repo/skill-name
  global?: boolean   // 是否全局安装
}
```

## 技术要点

1. **HTTP 客户端**: 使用 `httpx` 进行异步 HTTP 请求
2. **缓存策略**: 对远程 skill 列表进行适当缓存，减少 API 调用
3. **错误处理**: 处理网络错误、API 限流等情况
4. **安全考虑**: 验证 skill 来源，显示安全审计状态

## 预期成果

1. 用户可以在 skill 市场页面搜索 skills.sh 上的远程 skill
2. 用户可以查看远程 skill 的详情（安装数、stars、描述等）
3. 用户可以一键安装远程 skill 到本地
4. 前端 UI 清晰区分本地 skill 和远程 skill
