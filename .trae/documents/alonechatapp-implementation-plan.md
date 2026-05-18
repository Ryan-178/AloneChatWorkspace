# AloneChat Desktop App 实现计划 / AloneChat Desktop App Implementation Plan

## 项目概述 / Project Overview

使用 **Tauri v2 + Next.js 16** 构建跨平台桌面应用，对标 Claude Cowork 和 OpenAI Codex App，集成现有的 `agent-framework` 后端。

Build cross-platform desktop application using **Tauri v2 + Next.js 16**, benchmarked against Claude Cowork and OpenAI Codex App, integrating existing `agent-framework` backend.

## 对标产品分析 / Benchmark Analysis

### Claude Cowork 特性

| 特性     | 说明                          | 我们需要实现            |
| ------ | --------------------------- | ----------------- |
| 自主任务执行 | 多步骤工作流自动执行                  | ✅ Agent ReAct 循环  |
| 文件访问   | 用户授权的文件夹访问                  | ✅ Tauri 文件系统 API  |
| 专业输出   | Excel, PPT, 文档生成            | ✅ 文件生成服务          |
| 子代理协调  | 复杂任务并行执行                    | ✅ Multi-Agent 架构  |
| 安全沙箱   | Apple VZVirtualMachine 隔离   | ✅ Tauri 沙箱 + 权限控制 |
| 应用集成   | Google Drive, Gmail, GitHub | ✅ MCP 服务器集成       |

### Codex CLI/App 特性

| 特性       | 说明                            | 我们需要实现                     |
| -------- | ----------------------------- | -------------------------- |
| 终端/桌面双模式 | CLI + Desktop App             | ✅ Tauri 桌面 + alonechat-cli |
| 三种审批模式   | suggest/auto-edit/full-auto   | ✅ 权限控制系统                   |
| MCP 支持   | Model Context Protocol        | ✅ 已有 MCP 集成                |
| 代码审查     | PR 分析和 Bug 检测                 | ✅ Code Agent 模式            |
| 规划追踪     | 任务分解和进度展示                     | ✅ Task Planner             |
| 多模型支持    | OpenAI, Azure, Gemini, Ollama | ✅ LiteLLM 集成               |

## 技术架构 / Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AloneChat Desktop App                     │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Tauri v2 (Rust Core)                    │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ File System │  │   Process   │  │   Network   │  │    │
│  │  │    API      │  │   Manager   │  │   Manager   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │  Clipboard  │  │   Dialog    │  │    Shell    │  │    │
│  │  │    API      │  │    API      │  │   Command   │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │ IPC                             │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Next.js 16 Frontend                     │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │   Chat UI   │  │  Agent UI   │  │  Task UI    │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │  Skills UI  │  │   MCP UI    │  │ Settings UI │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │ WebSocket/HTTP                  │
│                           ▼                                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Agent Framework (Python)                │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ MTC Agent   │  │ Code Agent  │  │ Multi Agent │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │    │
│  │  │ Task Manager│  │Skills Reg.  │  │ MCP Manager │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构 / Project Structure

```
alonechat-desktop/
├── src-tauri/                    # Tauri Rust 后端
│   ├── src/
│   │   ├── main.rs              # 主入口
│   │   ├── commands/            # Tauri 命令
│   │   │   ├── mod.rs
│   │   │   ├── file_ops.rs      # 文件操作
│   │   │   ├── shell.rs         # Shell 命令执行
│   │   │   ├── process.rs       # 进程管理
│   │   │   └── system.rs        # 系统信息
│   │   ├── plugins/             # Tauri 插件
│   │   │   ├── mod.rs
│   │   │   ├── workspace.rs     # 工作区管理
│   │   │   └── permissions.rs   # 权限控制
│   │   └── utils/
│   │       └── sandbox.rs       # 沙箱工具
│   ├── icons/                   # 应用图标
│   ├── Cargo.toml               # Rust 依赖
│   └── tauri.conf.json          # Tauri 配置
│
├── src/                         # Next.js 前端
│   ├── app/                     # App Router
│   │   ├── (auth)/              # 认证页面
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── (main)/              # 主应用
│   │   │   ├── layout.tsx       # 主布局
│   │   │   ├── page.tsx         # 首页/对话
│   │   │   ├── agent/           # Agent 对话
│   │   │   │   └── [session]/
│   │   │   ├── tasks/           # 任务管理
│   │   │   ├── skills/          # Skills 市场
│   │   │   ├── mcp/             # MCP 管理
│   │   │   ├── workspace/       # 工作区
│   │   │   └── settings/        # 设置
│   │   ├── layout.tsx
│   │   ├── globals.css
│   │   └── not-found.tsx
│   │
│   ├── components/
│   │   ├── ui/                  # shadcn/ui 组件
│   │   ├── layout/              # 布局组件
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   └── command-palette.tsx
│   │   ├── chat/                # 聊天组件
│   │   │   ├── message-list.tsx
│   │   │   ├── message-bubble.tsx
│   │   │   └── message-input.tsx
│   │   ├── agent/               # Agent 组件
│   │   │   ├── agent-chat.tsx
│   │   │   ├── thinking-block.tsx
│   │   │   ├── tool-call-card.tsx
│   │   │   ├── mode-switch.tsx
│   │   │   └── session-list.tsx
│   │   ├── tasks/               # 任务组件
│   │   ├── skills/              # Skills 组件
│   │   ├── mcp/                 # MCP 组件
│   │   └── common/              # 通用组件
│   │
│   ├── lib/
│   │   ├── tauri/               # Tauri API 封装
│   │   │   ├── index.ts
│   │   │   ├── file.ts          # 文件操作
│   │   │   ├── shell.ts         # Shell 命令
│   │   │   ├── process.ts       # 进程管理
│   │   │   └── dialog.ts        # 对话框
│   │   ├── api/                 # HTTP API 客户端
│   │   │   ├── client.ts
│   │   │   ├── auth.ts
│   │   │   ├── sessions.ts
│   │   │   ├── tasks.ts
│   │   │   ├── skills.ts
│   │   │   └── mcp.ts
│   │   ├── websocket/           # WebSocket 客户端
│   │   │   ├── gateway.ts
│   │   │   └── types.ts
│   │   ├── utils.ts
│   │   └── constants.ts
│   │
│   ├── stores/                  # Zustand 状态管理
│   │   ├── auth-store.ts
│   │   ├── agent-store.ts
│   │   ├── task-store.ts
│   │   ├── workspace-store.ts
│   │   └── ui-store.ts
│   │
│   ├── hooks/                   # 自定义 Hooks
│   │   ├── use-tauri.ts
│   │   ├── use-websocket.ts
│   │   ├── use-agent-session.ts
│   │   └── use-workspace.ts
│   │
│   └── types/                   # TypeScript 类型
│       ├── agent.ts
│       ├── task.ts
│       ├── skill.ts
│       ├── mcp.ts
│       └── tauri.ts
│
├── public/                      # 静态资源
├── next.config.ts               # Next.js 配置
├── tailwind.config.ts           # Tailwind 配置
├── package.json
└── tsconfig.json
```

## 实现步骤 / Implementation Steps

### Phase 1: 项目初始化 (P0)

#### 1.1 创建 Tauri + Next.js 项目

```bash
# 创建 Next.js 项目
npx create-next-app@latest alonechat-desktop --typescript --tailwind --eslint --app --no-src-dir --import-alias "@/*"

cd alonechat-desktop

# 安装 Tauri CLI
npm install -D @tauri-apps/cli@latest
npm install @tauri-apps/api@latest

# 初始化 Tauri
npx tauri init --ci \
  --app-name alonechat-desktop \
  --window-title "AloneChat Desktop" \
  --frontend-dist ../out \
  --dev-url http://localhost:3000 \
  --before-dev-command "npm run dev" \
  --before-build-command "npm run build"
```

#### 1.2 配置 Next.js 静态导出

**文件:** **`next.config.ts`**

```typescript
import type { NextConfig } from "next"

const isProd = process.env.NODE_ENV === 'production'
const internalHost = process.env.TAURI_DEV_HOST || 'localhost'

const nextConfig: NextConfig = {
  output: 'export',
  images: { unoptimized: true },
  assetPrefix: isProd ? undefined : `http://${internalHost}:3000`,
  trailingSlash: true,
}

export default nextConfig
```

#### 1.3 配置 Tauri

**文件:** **`src-tauri/tauri.conf.json`**

```json
{
  "identifier": "com.alonechat.desktop",
  "build": {
    "frontendDist": "../out",
    "devUrl": "http://localhost:3000",
    "beforeDevCommand": "npm run dev",
    "beforeBuildCommand": "npm run build"
  },
  "app": {
    "security": {
      "csp": null,
      "assetProtocol": {
        "enable": true,
        "scope": {
          "allow": ["$RESOURCE/**", "$APP/**"]
        }
      }
    },
    "windows": [
      {
        "title": "AloneChat Desktop",
        "width": 1200,
        "height": 800,
        "minWidth": 800,
        "minHeight": 600,
        "resizable": true,
        "fullscreen": false
      }
    ]
  }
}
```

#### 1.4 安装前端依赖

```bash
# UI 组件
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu @radix-ui/react-tabs
npm install @radix-ui/react-scroll-area @radix-ui/react-separator @radix-ui/react-tooltip
npm install @radix-ui/react-avatar @radix-ui/react-slot @radix-ui/react-checkbox
npm install lucide-react class-variance-authority clsx tailwind-merge
npm install zustand @tanstack/react-query
npm install next-themes sonner cmdk
npm install markdown-it highlight.js
```

### Phase 2: Tauri Rust 后端 (P0)

#### 2.1 文件操作命令

**文件:** **`src-tauri/src/commands/file_ops.rs`**

```rust
use tauri::State;
use std::fs;
use std::path::PathBuf;

#[tauri::command]
pub async fn read_file(path: String) -> Result<String, String> {
    fs::read_to_string(&path).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn write_file(path: String, content: String) -> Result<(), String> {
    fs::write(&path, content).map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn list_directory(path: String) -> Result<Vec<String>, String> {
    let entries = fs::read_dir(&path).map_err(|e| e.to_string())?;
    let files: Vec<String> = entries
        .filter_map(|e| e.ok())
        .map(|e| e.file_name().to_string_lossy().to_string())
        .collect();
    Ok(files)
}

#[tauri::command]
pub async fn delete_file(path: String) -> Result<(), String> {
    let path = PathBuf::from(&path);
    if path.is_dir() {
        fs::remove_dir_all(&path).map_err(|e| e.to_string())
    } else {
        fs::remove_file(&path).map_err(|e| e.to_string())
    }
}
```

#### 2.2 Shell 命令执行

**文件:** **`src-tauri/src/commands/shell.rs`**

```rust
use std::process::Command;

#[tauri::command]
pub async fn execute_command(
    command: String,
    args: Vec<String>,
    cwd: Option<String>,
) -> Result<CommandResult, String> {
    let mut cmd = Command::new(&command);
    cmd.args(&args);
    
    if let Some(dir) = cwd {
        cmd.current_dir(dir);
    }
    
    let output = cmd.output().map_err(|e| e.to_string())?;
    
    Ok(CommandResult {
        stdout: String::from_utf8_lossy(&output.stdout).to_string(),
        stderr: String::from_utf8_lossy(&output.stderr).to_string(),
        success: output.status.success(),
        code: output.status.code(),
    })
}

#[derive(serde::Serialize)]
pub struct CommandResult {
    pub stdout: String,
    pub stderr: String,
    pub success: bool,
    pub code: Option<i32>,
}
```

#### 2.3 权限控制插件

**文件:** **`src-tauri/src/plugins/permissions.rs`**

```rust
use std::collections::HashSet;
use std::sync::Mutex;

pub struct PermissionManager {
    allowed_paths: Mutex<HashSet<String>>,
    allowed_commands: Mutex<HashSet<String>>,
}

impl PermissionManager {
    pub fn new() -> Self {
        Self {
            allowed_paths: Mutex::new(HashSet::new()),
            allowed_commands: Mutex::new(HashSet::new()),
        }
    }
    
    pub fn grant_path(&self, path: String) {
        self.allowed_paths.lock().unwrap().insert(path);
    }
    
    pub fn revoke_path(&self, path: &str) {
        self.allowed_paths.lock().unwrap().remove(path);
    }
    
    pub fn is_path_allowed(&self, path: &str) -> bool {
        self.allowed_paths.lock().unwrap().contains(path)
    }
    
    pub fn grant_command(&self, command: String) {
        self.allowed_commands.lock().unwrap().insert(command);
    }
    
    pub fn is_command_allowed(&self, command: &str) -> bool {
        self.allowed_commands.lock().unwrap().contains(command)
    }
}
```

### Phase 3: 前端基础设施 (P0)

#### 3.1 Tauri API 封装

**文件:** **`src/lib/tauri/index.ts`**

```typescript
import { invoke } from '@tauri-apps/api/core'

export const tauri = {
  file: {
    read: (path: string) => invoke<string>('read_file', { path }),
    write: (path: string, content: string) => invoke<void>('write_file', { path, content }),
    listDirectory: (path: string) => invoke<string[]>('list_directory', { path }),
    delete: (path: string) => invoke<void>('delete_file', { path }),
  },
  shell: {
    execute: (command: string, args: string[], cwd?: string) => 
      invoke<CommandResult>('execute_command', { command, args, cwd }),
  },
  dialog: {
    open: (options?: OpenDialogOptions) => invoke<string | string[]>('open_dialog', { options }),
    save: (options?: SaveDialogOptions) => invoke<string>('save_dialog', { options }),
  },
}

interface CommandResult {
  stdout: string
  stderr: string
  success: boolean
  code: number | null
}
```

#### 3.2 API 客户端

**文件:** **`src/lib/api/client.ts`**

```typescript
const API_BASE = 'http://localhost:18789'

export class ApiClient {
  private token: string | null = null
  
  setToken(token: string) {
    this.token = token
  }
  
  clearToken() {
    this.token = null
  }
  
  async request<T>(method: string, path: string, data?: unknown): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`
    }
    
    const response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: data ? JSON.stringify(data) : undefined,
    })
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`)
    }
    
    return response.json()
  }
}

export const api = new ApiClient()
```

#### 3.3 WebSocket 客户端

**文件:** **`src/lib/websocket/gateway.ts`**

```typescript
const WS_URL = 'ws://localhost:18789'

export class GatewayWebSocket {
  private ws: WebSocket | null = null
  private handlers: Map<string, Set<(msg: GatewayMessage) => void>> = new Map()
  
  async connect(token: string, sessionId?: string): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(WS_URL)
      
      this.ws.onopen = () => {
        this.ws!.send(JSON.stringify({
          type: 'connect',
          token,
          session_id: sessionId,
        }))
        resolve()
      }
      
      this.ws.onmessage = (event) => {
        const msg = JSON.parse(event.data) as GatewayMessage
        this.handleMessage(msg)
      }
      
      this.ws.onerror = reject
    })
  }
  
  subscribe(channel: string) {
    this.ws?.send(JSON.stringify({
      action: 'subscribe',
      params: { channel },
    }))
  }
  
  sendMessage(body: string, type = 'message') {
    this.ws?.send(JSON.stringify({ type, body }))
  }
  
  onMessage(type: string | '*', handler: (msg: GatewayMessage) => void): () => void {
    const key = type === '*' ? '*' : type
    if (!this.handlers.has(key)) {
      this.handlers.set(key, new Set())
    }
    this.handlers.get(key)!.add(handler)
    return () => this.handlers.get(key)?.delete(handler)
  }
  
  private handleMessage(msg: GatewayMessage) {
    this.handlers.get(msg.type)?.forEach(h => h(msg))
    this.handlers.get('*')?.forEach(h => h(msg))
  }
  
  disconnect() {
    this.ws?.close()
    this.ws = null
  }
}
```

### Phase 4: Agent 对话模块 (P1) - 核心功能

#### 4.1 Agent Chat 组件

**文件:** **`src/components/agent/agent-chat.tsx`**

```typescript
'use client'

import { useState, useEffect, useRef } from 'react'
import { useAgentStore } from '@/stores/agent-store'
import { MessageBubble } from './message-bubble'
import { ThinkingBlock } from './thinking-block'
import { ToolCallCard } from './tool-call-card'
import { MessageInput } from './message-input'
import { ModeSwitch } from './mode-switch'
import { ScrollArea } from '@/components/ui/scroll-area'

export function AgentChat({ sessionId }: { sessionId: string }) {
  const { messages, mode, sendMessage, setMode } = useAgentStore()
  const scrollRef = useRef<HTMLDivElement>(null)
  
  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: 'smooth',
    })
  }, [messages])
  
  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b">
        <h2 className="font-semibold">Agent 对话</h2>
        <ModeSwitch mode={mode} onModeChange={setMode} />
      </div>
      
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        {messages.map((msg) => (
          <div key={msg.id}>
            {msg.type === 'thinking' ? (
              <ThinkingBlock content={msg.content} />
            ) : msg.type === 'acting' ? (
              <ToolCallCard toolCall={msg.metadata} />
            ) : (
              <MessageBubble message={msg} />
            )}
          </div>
        ))}
      </ScrollArea>
      
      <div className="p-4 border-t">
        <MessageInput onSend={sendMessage} />
      </div>
    </div>
  )
}
```

#### 4.2 Thinking Block 组件

**文件:** **`src/components/agent/thinking-block.tsx`**

```typescript
'use client'

import { useState } from 'react'
import { ChevronDown, ChevronRight, Brain } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

export function ThinkingBlock({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(true)
  
  return (
    <Card className="my-2 bg-muted/50">
      <div 
        className="flex items-center gap-2 p-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        {expanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        <Brain className="h-4 w-4 text-primary" />
        <span className="font-medium">思考过程</span>
        <Badge variant="secondary" className="ml-auto">Thinking</Badge>
      </div>
      {expanded && (
        <CardContent className="pt-0 text-sm text-muted-foreground">
          <pre className="whitespace-pre-wrap">{content}</pre>
        </CardContent>
      )}
    </Card>
  )
}
```

#### 4.3 Mode Switch 组件

**文件:** **`src/components/agent/mode-switch.tsx`**

```typescript
'use client'

import { AgentMode } from '@/types/agent'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { Zap, Code } from 'lucide-react'

export function ModeSwitch({ 
  mode, 
  onModeChange 
}: { 
  mode: AgentMode
  onModeChange: (mode: AgentMode) => void 
}) {
  return (
    <ToggleGroup 
      type="single" 
      value={mode} 
      onValueChange={(v) => v && onModeChange(v as AgentMode)}
      className="border rounded-lg p-1"
    >
      <ToggleGroupItem value="MTC" className="gap-2">
        <Zap className="h-4 w-4" />
        <span>MTC</span>
      </ToggleGroupItem>
      <ToggleGroupItem value="CODE" className="gap-2">
        <Code className="h-4 w-4" />
        <span>CODE</span>
      </ToggleGroupItem>
    </ToggleGroup>
  )
}
```

### Phase 5: 工作区模块 (P1)

#### 5.1 工作区管理

**文件:** **`src/stores/workspace-store.ts`**

```typescript
import { create } from 'zustand'
import { tauri } from '@/lib/tauri'

interface Workspace {
  path: string
  name: string
  files: string[]
}

interface WorkspaceStore {
  workspaces: Workspace[]
  currentWorkspace: Workspace | null
  
  addWorkspace: (path: string) => Promise<void>
  removeWorkspace: (path: string) => void
  setCurrentWorkspace: (workspace: Workspace | null) => void
  refreshFiles: () => Promise<void>
}

export const useWorkspaceStore = create<WorkspaceStore>((set, get) => ({
  workspaces: [],
  currentWorkspace: null,
  
  addWorkspace: async (path) => {
    const files = await tauri.file.listDirectory(path)
    const workspace: Workspace = {
      path,
      name: path.split('/').pop() || path,
      files,
    }
    set((state) => ({
      workspaces: [...state.workspaces, workspace],
    }))
  },
  
  removeWorkspace: (path) => {
    set((state) => ({
      workspaces: state.workspaces.filter((w) => w.path !== path),
      currentWorkspace: state.currentWorkspace?.path === path ? null : state.currentWorkspace,
    }))
  },
  
  setCurrentWorkspace: (workspace) => set({ currentWorkspace: workspace }),
  
  refreshFiles: async () => {
    const { currentWorkspace } = get()
    if (!currentWorkspace) return
    
    const files = await tauri.file.listDirectory(currentWorkspace.path)
    set((state) => ({
      currentWorkspace: { ...currentWorkspace, files },
      workspaces: state.workspaces.map((w) =>
        w.path === currentWorkspace.path ? { ...w, files } : w
      ),
    }))
  },
}))
```

### Phase 6: 任务管理模块 (P1)

#### 6.1 Task Store

**文件:** **`src/stores/task-store.ts`**

```typescript
import { create } from 'zustand'
import { api } from '@/lib/api/client'
import type { Task, TaskStatus } from '@/types/task'

interface TaskStore {
  tasks: Task[]
  currentTask: Task | null
  isLoading: boolean
  
  fetchTasks: (status?: TaskStatus) => Promise<void>
  createTask: (description: string, priority?: string) => Promise<Task>
  cancelTask: (taskId: string) => Promise<void>
  setCurrentTask: (task: Task | null) => void
}

export const useTaskStore = create<TaskStore>((set, get) => ({
  tasks: [],
  currentTask: null,
  isLoading: false,
  
  fetchTasks: async (status) => {
    set({ isLoading: true })
    try {
      const params = status ? `?status=${status}` : ''
      const data = await api.request<{ tasks: Task[] }>('GET', `/api/tasks${params}`)
      set({ tasks: data.tasks, isLoading: false })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },
  
  createTask: async (description, priority = 'medium') => {
    const task = await api.request<Task>('POST', '/api/tasks', { description, priority })
    set((state) => ({ tasks: [task, ...state.tasks] }))
    return task
  },
  
  cancelTask: async (taskId) => {
    await api.request('DELETE', `/api/tasks/${taskId}`)
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== taskId),
      currentTask: state.currentTask?.id === taskId ? null : state.currentTask,
    }))
  },
  
  setCurrentTask: (task) => set({ currentTask: task }),
}))
```

### Phase 7: Skills 和 MCP 模块 (P2)

#### 7.1 Skills Store

**文件:** **`src/stores/skill-store.ts`**

```typescript
import { create } from 'zustand'
import { api } from '@/lib/api/client'
import type { Skill } from '@/types/skill'

interface SkillStore {
  skills: Skill[]
  categories: string[]
  selectedCategory: string | null
  
  fetchSkills: (category?: string, query?: string) => Promise<void>
  executeSkill: (skillName: string, context: Record<string, unknown>) => Promise<unknown>
  setCategory: (category: string | null) => void
}

export const useSkillStore = create<SkillStore>((set) => ({
  skills: [],
  categories: [],
  selectedCategory: null,
  
  fetchSkills: async (category, query) => {
    const params = new URLSearchParams()
    if (category) params.set('category', category)
    if (query) params.set('query', query)
    
    const data = await api.request<{ skills: Skill[], categories: string[] }>(
      'GET', `/api/skills?${params}`
    )
    set({ skills: data.skills, categories: data.categories })
  },
  
  executeSkill: async (skillName, context) => {
    const result = await api.request<{ success: boolean, result?: unknown, error?: string }>(
      'POST', '/api/skills/execute', { skill_name: skillName, context }
    )
    if (!result.success) throw new Error(result.error)
    return result.result
  },
  
  setCategory: (category) => set({ selectedCategory: category }),
}))
```

### Phase 8: 设置和认证模块 (P2)

#### 8.1 认证 Store

**文件:** **`src/stores/auth-store.ts`**

```typescript
import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { api } from '@/lib/api/client'
import type { User } from '@/types/auth'

interface AuthStore {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  refreshToken: () => Promise<void>
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (username, password) => {
        const data = await api.request<{ access_token: string, user: User }>(
          'POST', '/api/auth/login', { username, password }
        )
        api.setToken(data.access_token)
        set({ user: data.user, token: data.access_token, isAuthenticated: true })
      },
      
      register: async (username, email, password) => {
        const data = await api.request<{ access_token: string, user: User }>(
          'POST', '/api/auth/register', { username, email, password }
        )
        api.setToken(data.access_token)
        set({ user: data.user, token: data.access_token, isAuthenticated: true })
      },
      
      logout: () => {
        api.clearToken()
        set({ user: null, token: null, isAuthenticated: false })
      },
      
      refreshToken: async () => {
        const { token } = get()
        if (!token) return
        
        const data = await api.request<{ access_token: string }>(
          'POST', '/api/auth/refresh'
        )
        api.setToken(data.access_token)
        set({ token: data.access_token })
      },
    }),
    { name: 'auth-storage' }
  )
)
```

## 设计规范 / Design Specifications

### 配色方案

```css
:root {
  --primary: #2563EB;      /* Trust Blue */
  --secondary: #3B82F6;    /* Light Blue */
  --cta: #F97316;          /* Orange CTA */
  --background: #F8FAFC;
  --text: #1E293B;
  --border: #E2E8F0;
  --muted: #64748B;
  --accent: #10B981;
  --destructive: #EF4444;
}

.dark {
  --background: #0F172A;
  --text: #F1F5F9;
  --border: #334155;
  --muted: #94A3B8;
}
```

### UI 风格

* **主风格**: Soft UI Evolution + Minimalism

* **次要风格**: Glassmorphism, Micro-interactions

* **动画**: 200-300ms ease-out transitions

* **响应式**: Desktop-first (800px-1920px)

## 开发命令 / Development Commands

```bash
# 开发模式
npm run tauri dev

# 构建
npm run tauri build

# 仅构建前端
npm run build

# Rust 代码检查
cargo clippy --manifest-path=src-tauri/Cargo.toml
```

## 预估工作量 / Estimated Effort

| Phase | 模块              | 预估时间   |
| ----- | --------------- | ------ |
| 1     | 项目初始化           | 1-2 小时 |
| 2     | Tauri Rust 后端   | 3-4 小时 |
| 3     | 前端基础设施          | 2-3 小时 |
| 4     | Agent 对话模块      | 5-6 小时 |
| 5     | 工作区模块           | 2-3 小时 |
| 6     | 任务管理模块          | 2-3 小时 |
| 7     | Skills 和 MCP 模块 | 2-3 小时 |
| 8     | 设置和认证模块         | 1-2 小时 |

**总计**: 约 18-26 小时

## 依赖关系 / Dependencies

```
Phase 1 (项目初始化)
    ↓
Phase 2 (Tauri Rust) ← Phase 3 (前端基础设施) ← 可并行
    ↓
Phase 4 (Agent 对话) ← 核心功能
    ↓
Phase 5 (工作区) ← Phase 6 (任务) ← Phase 7 (Skills/MCP) ← 可并行
    ↓
Phase 8 (设置/认证)
```

