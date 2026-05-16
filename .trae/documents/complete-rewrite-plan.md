
# Complete Project Rewrite Plan

## Overview

基于截图展示的"More Than Coding"界面，完全重写整个项目，包括前端、后端和数据库，确保纯DeepSeek集成。

---

## Phase 1: Architecture Design

### 1.1 Technology Stack Selection

**Frontend:**
- Next.js 15+ (App Router)
- React 19
- TypeScript 5.5+
- Tailwind CSS 4
- shadcn/ui components
- Lucide Icons
- Zustand (State Management)
- React Query (Data Fetching)

**Backend:**
- FastAPI
- SQLAlchemy 2.0 (ORM)
- PostgreSQL (Database)
- Redis (Caching)
- Pydantic 2.0
- WebSocket Support

**Database:**
- PostgreSQL 16+

**AI Integration:**
- DeepSeek API (Pure Text Model)
- LiteLLM (Unified Interface)

---

## Phase 2: Database Design

### 2.1 Core Tables

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    avatar_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workspaces Table
CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES users(id),
    icon VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Workspace Members
CREATE TABLE workspace_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) DEFAULT 'member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(workspace_id, user_id)
);

-- Files Table
CREATE TABLE files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    content JSONB,
    file_size BIGINT,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    synced BOOLEAN DEFAULT TRUE,
    remote_id VARCHAR(255)
);

-- Tasks Table
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    priority VARCHAR(20) DEFAULT 'medium',
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    created_by UUID REFERENCES users(id),
    assigned_to UUID REFERENCES users(id),
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Skills Table
CREATE TABLE skills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    icon VARCHAR(100),
    category VARCHAR(50),
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Chat Messages Table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id),
    content TEXT NOT NULL,
    role VARCHAR(20) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation History Table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Conversation Messages (Linked)
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES chat_messages(id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL
);
```

---

## Phase 3: Frontend Implementation

### 3.1 Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── globals.css
│   │   ├── (auth)/
│   │   │   ├── login/
│   │   │   └── register/
│   │   └── (app)/
│   │       ├── layout.tsx
│   │       ├── workspace/
│   │       │   └── [workspaceId]/
│   │       │       ├── page.tsx
│   │       │       ├── files/
│   │       │       ├── tasks/
│   │       │       └── chat/
│   │       └── settings/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppShell.tsx
│   │   │   ├── TopBar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── SidebarItem.tsx
│   │   ├── chat/
│   │   │   ├── ChatInput.tsx
│   │   │   ├── ChatMessage.tsx
│   │   │   └── ChatContainer.tsx
│   │   ├── skills/
│   │   │   ├── SkillCard.tsx
│   │   │   └── SkillGrid.tsx
│   │   ├── files/
│   │   │   ├── FileExplorer.tsx
│   │   │   ├── FileCard.tsx
│   │   │   └── DocumentEditor.tsx
│   │   └── ui/
│   │       └── (shadcn components)
│   ├── lib/
│   │   ├── api.ts
│   │   ├── store.ts
│   │   └── utils.ts
│   ├── types/
│   │   ├── index.ts
│   │   ├── user.ts
│   │   ├── workspace.ts
│   │   ├── file.ts
│   │   └── chat.ts
│   └── hooks/
│       ├── useWorkspace.ts
│       ├── useChat.ts
│       └── useFiles.ts
├── package.json
└── tailwind.config.js
```

### 3.2 Core Components

**AppShell.tsx** - Main application layout with sidebar and top bar
**Sidebar.tsx** - Navigation sidebar with workspace selector
**ChatContainer.tsx** - AI chat interface with DeepSeek integration
**SkillCard.tsx** - Skill cards for "Web Reading", "Research Analysis", etc.
**FileExplorer.tsx** - File management interface
**DocumentEditor.tsx** - Rich text document editor

### 3.3 State Management

**Zustand Store:**

```typescript
// src/lib/store.ts
import { create } from 'zustand'

interface AppState {
  user: User | null
  currentWorkspace: Workspace | null
  workspaces: Workspace[]
  files: FileRecord[]
  chatMessages: ChatMessage[]
  isLoading: boolean
  
  setUser: (user: User | null) => void
  setCurrentWorkspace: (workspace: Workspace | null) => void
  addMessage: (message: ChatMessage) => void
  setFiles: (files: FileRecord[]) => void
}

export const useAppStore = create&lt;AppState&gt;((set) =&gt; ({
  user: null,
  currentWorkspace: null,
  workspaces: [],
  files: [],
  chatMessages: [],
  isLoading: false,
  
  setUser: (user) =&gt; set({ user }),
  setCurrentWorkspace: (workspace) =&gt; set({ currentWorkspace: workspace }),
  addMessage: (message) =&gt; set((state) =&gt; ({ 
    chatMessages: [...state.chatMessages, message] 
  })),
  setFiles: (files) =&gt; set({ files }),
}))
```

---

## Phase 4: Backend Implementation

### 4.1 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── workspaces.py
│   │   │   ├── files.py
│   │   │   ├── tasks.py
│   │   │   ├── skills.py
│   │   │   └── chat.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── deepseek_service.py
│   │   ├── file_service.py
│   │   └── workspace_service.py
│   └── websocket/
│       ├── __init__.py
│       └── manager.py
├── requirements.txt
└── .env.example
```

### 4.2 Core API Endpoints

**Authentication:**
- POST /api/v1/auth/login
- POST /api/v1/auth/register
- POST /api/v1/auth/logout
- GET /api/v1/auth/me

**Workspaces:**
- GET /api/v1/workspaces
- POST /api/v1/workspaces
- GET /api/v1/workspaces/{id}
- PUT /api/v1/workspaces/{id}
- DELETE /api/v1/workspaces/{id}

**Files:**
- GET /api/v1/workspaces/{id}/files
- POST /api/v1/workspaces/{id}/files
- GET /api/v1/files/{id}
- PUT /api/v1/files/{id}
- DELETE /api/v1/files/{id}

**Chat:**
- POST /api/v1/chat/message
- GET /api/v1/chat/history
- WebSocket /ws/chat/{workspace_id}

**Skills:**
- GET /api/v1/skills
- POST /api/v1/skills/{id}/execute

---

## Phase 5: DeepSeek Integration

### 5.1 DeepSeek Service Implementation

```python
# backend/app/services/deepseek_service.py
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

class DeepSeekService:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = "https://api.deepseek.com/v1"
        self.model = "deepseek-chat"
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -&gt; Dict[str, Any]:
        """Send chat completion request to DeepSeek"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """Stream chat completion from DeepSeek"""
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True
                }
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield data
    
    async def execute_skill(
        self,
        skill_name: str,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -&gt; str:
        """Execute a specific skill using DeepSeek"""
        
        skill_prompts = {
            "web_reading": """你是一个网页阅读专家。请帮助用户：
1. 理解网页内容
2. 提取关键信息
3. 总结核心要点

用户输入：{user_input}
上下文：{context}

请用清晰、结构化的方式回复。""",
            
            "research_analysis": """你是一个调研分析专家。请帮助用户：
1. 分析研究问题
2. 提供数据支持
3. 给出建议结论

用户输入：{user_input}
上下文：{context}

请用专业、系统的方式回复。""",
            
            "data_mining": """你是一个数据挖掘专家。请帮助用户：
1. 分析数据模式
2. 发现数据洞察
3. 提供数据可视化建议

用户输入：{user_input}
上下文：{context}

请用数据驱动的方式回复。""",
            
            "file_management": """你是一个文档处理专家。请帮助用户：
1. 编辑和优化文档
2. 分析文档内容
3. 提供文档改进建议

用户输入：{user_input}
上下文：{context}

请用实用的方式回复。"""
        }
        
        prompt = skill_prompts.get(skill_name, skill_prompts["web_reading"])
        formatted_prompt = prompt.format(
            user_input=user_input,
            context=context or "无额外上下文"
        )
        
        messages = [
            {"role": "system", "content": "你是 More Than Coding AI 助手，专业、高效、乐于助人。"},
            {"role": "user", "content": formatted_prompt}
        ]
        
        result = await self.chat_completion(messages)
        return result["choices"][0]["message"]["content"]

deepseek_service = DeepSeekService()
```

---

## Phase 6: UI/UX Implementation

### 6.1 Main Dashboard Layout

Based on the screenshot, implement:

1. **Top Bar**
   - Application logo "MTC"
   - Menu buttons (File, Edit, Help)
   - Window controls (Minimize, Maximize, Close)

2. **Left Sidebar**
   - "新建任务" button
   - Navigation items: "技能", "自动化", "任务列表"
   - Workspace list with expandable folders
   - User profile section at bottom

3. **Main Content Area**
   - Welcome section with "More Than Coding" title
   - Skill cards grid:
     - 网页读取 (Web Reading)
     - 调研分析 (Research Analysis)
     - 数据挖掘 (Data Mining)
     - 文件管理 (File Management)
   - Chat input area at bottom with model selector

4. **Color Scheme**
   - Primary: Purple/Blue gradient (#7c3aed to #2563eb)
   - Background: Light gray (#f3f4f6)
   - Cards: White with subtle shadows
   - Accents: Clean, modern design

### 6.2 Component Implementation

```tsx
// src/components/layout/AppShell.tsx
"use client";

import { useState } from "react";
import { TopBar } from "./TopBar";
import { Sidebar } from "./Sidebar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    &lt;div className="flex flex-col h-screen bg-gray-100"&gt;
      &lt;TopBar /&gt;
      &lt;div className="flex flex-1 overflow-hidden"&gt;
        &lt;Sidebar 
          collapsed={sidebarCollapsed}
          onToggle={() =&gt; setSidebarCollapsed(!sidebarCollapsed)}
        /&gt;
        &lt;main className="flex-1 overflow-auto"&gt;
          {children}
        &lt;/main&gt;
      &lt;/div&gt;
    &lt;/div&gt;
  );
}
```

---

## Phase 7: Implementation Checklist

### Frontend
- [ ] Project setup with Next.js 15
- [ ] Configure Tailwind CSS and shadcn/ui
- [ ] Create core layout components
- [ ] Implement state management with Zustand
- [ ] Build main dashboard with skill cards
- [ ] Implement chat interface with streaming
- [ ] Create file explorer component
- [ ] Add authentication pages
- [ ] Set up API client and React Query

### Backend
- [ ] Initialize FastAPI project
- [ ] Configure database with SQLAlchemy
- [ ] Implement user authentication
- [ ] Create workspace management API
- [ ] Build file management endpoints
- [ ] Implement chat API with DeepSeek
- [ ] Add WebSocket support
- [ ] Create skill execution endpoints

### Database
- [ ] Design database schema
- [ ] Set up PostgreSQL
- [ ] Create migration scripts
- [ ] Seed initial data (default skills)

### Integration
- [ ] DeepSeek API integration
- [ ] Frontend-backend integration
- [ ] WebSocket real-time chat
- [ ] File upload and management

### Testing
- [ ] Unit tests for backend
- [ ] Integration tests
- [ ] End-to-end tests
- [ ] Performance testing

---

## Phase 8: Deployment

### Local Development
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

### Environment Variables

```env
# Backend .env
DATABASE_URL=postgresql://user:pass@localhost/mtc_db
REDIS_URL=redis://localhost:6379
DEEPSEEK_API_KEY=your_deepseek_api_key
SECRET_KEY=your_secret_key

# Frontend .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Next Steps

1. Review and approve this plan
2. Start Phase 1: Project Setup
3. Implement core architecture
4. Build features incrementally
5. Test and refine

