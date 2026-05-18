# 本地原生 Office 工作区实施计划

## 目标
在 ChatAgent Workspace 中增加本地优先、原生体验的 Office 套件（类 Word / Excel / PowerPoint），支持离线编辑、Office 文件格式导入导出，并深度集成到现有聊天和工作区体系中。

## 现有架构分析

### 后端 (FastAPI + SQLAlchemy Async + PostgreSQL)
- **main.py**: 根应用，已注册 `agent` 和 `workspaces` 路由，使用全局异常处理器
- **models.py**: 现有模型 — User, Conversation, ConversationParticipant, Message, Group, GroupMember, AgentSession, AgentMessage, Workspace, WorkspaceMember
- **schemas.py**: Pydantic v2 模型，使用 `from_attributes = True`
- **database.py**: asyncpg + SQLAlchemy 2.0 async 引擎，declarative_base
- **auth.py**: JWT Bearer Token 认证，get_current_user 依赖
- **api.ts**: 前端统一 API 客户端，fetchWithAuth 封装

### 前端 (Next.js 16 + React 19 + Tailwind CSS v4 + Radix UI)
- **chat-layout.tsx**: 三栏布局（会话/群组/Agent），侧边栏 320px，主内容区 flex-1
- **package.json**: 无 dexie, 无 tiptap，使用 lucide-react 图标
- **tsconfig.json**: paths `@/*` 映射到 `./src/*`
- **globals.css**: CSS 变量主题系统（HSL），Tailwind v4 `@import "tailwindcss"`

### API 设计原则（来自 skill）
- 资源导向：名词复数，HTTP 方法表动作
- 错误标准化：`{"error": "Code", "message": "...", "details": {}}`
- 分页：`page`, `page_size`, 返回 `items`, `total`, `page`, `page_size`, `pages`
- 状态码：201 创建，204 删除，422 验证错误

---

## 阶段一：Office 文件基础设施

### Task 1.1: 后端 Office 文件转换服务

**新建文件:**
- `chat-app/backend/services/office_converter.py`
- `chat-app/backend/routers/files.py`
- `chat-app/backend/requirements-office.txt`

**修改文件:**
- `chat-app/backend/models.py` — 新增 FileRecord 模型
- `chat-app/backend/schemas.py` — 新增 FileRecord 相关 Schema
- `chat-app/backend/main.py` — 注册 files 路由

**设计决策:**
1. **OfficeConverter 类**: 纯工具类，不依赖数据库，支持 docx/xlsx/pptx ↔ JSON 双向转换
2. **FileRecord 模型字段**: `id`, `filename`, `stored_path`, `file_size`, `file_type` (document/spreadsheet/presentation/other), `uploader_id`, `preview_data` (JSONB/Text), `workspace_id`, `created_at`, `updated_at`
3. **文件存储**: 上传文件存 `chat-app/backend/uploads/` 子目录，按日期分文件夹避免单目录过大
4. **REST API 端点**:
   - `POST /api/files/upload` — multipart/form-data，返回 FileRecordResponse
   - `GET /api/files` — 列表，支持 `?file_type=` 过滤，`page`/`page_size` 分页
   - `GET /api/files/{id}` — 获取元数据
   - `GET /api/files/{id}/download` — 下载原始文件
   - `GET /api/files/{id}/preview` — 获取 JSON preview_data
   - `DELETE /api/files/{id}` — 删除文件记录+物理文件
   - `POST /api/files/{id}/convert` — 将上传的 Office 文件转换为内部 JSON
5. **错误响应格式**: 与现有代码一致 `{"error": "NotFound", "message": "...", "details": {}}`

**依赖:**
- `python-docx==1.1.2`
- `openpyxl==3.1.5`
- `python-pptx==0.6.23`

---

### Task 1.2: 前端文件浏览器与本地存储

**新建文件:**
- `chat-app/frontend/src/lib/file-store.ts` — Dexie.js IndexedDB 封装
- `chat-app/frontend/src/lib/file-api.ts` — 文件 API 客户端（扩展 api 对象）
- `chat-app/frontend/src/components/file-tree.tsx` — 文件树/列表组件
- `chat-app/frontend/src/components/file-explorer.tsx` — 文件浏览器主组件

**修改文件:**
- `chat-app/frontend/src/components/chat-layout.tsx` — 新增 "files" Tab

**设计决策:**
1. **IndexedDB Schema (Dexie.js)**:
   - 表 `files`: `id` (auto), `filename`, `fileType` (document|spreadsheet|presentation), `content` (JSON), `updatedAt`, `synced` (boolean), `remoteId` (nullable)
   - 版本 1
2. **file-api.ts 方法**:
   - `upload(file: File): Promise<FileRecord>`
   - `list(fileType?: string, page?: number): Promise<PaginatedResponse>`
   - `download(id: string): Promise<Blob>`
   - `remove(id: string): Promise<void>`
   - `convert(id: string): Promise<{content: any}>`
3. **FileExplorer 组件**:
   - 顶部工具栏：新建下拉菜单（文档/表格/演示）、导入按钮（input type=file）
   - 文件列表：图标 + 文件名 + 修改时间，点击打开编辑器
   - 空状态提示
4. **ChatLayout 修改**:
   - `activeTab` 扩展 `"conversations" | "groups" | "agent" | "files"`
   - 新增 Files 图标 Tab
   - `selectedType` 扩展 `"conversation" | "group" | "document" | "spreadsheet" | "presentation"`

**依赖安装:**
```bash
npm install dexie@4
```

---

### Task 1.3: 本地文件同步服务

**新建文件:**
- `chat-app/frontend/src/lib/sync-service.ts`

**设计决策:**
1. **SyncService 类**:
   - `syncAll(): Promise<void>` — 遍历 `files` 表中 `synced === false` 的记录，调用 API 上传，成功后更新 `synced = true` 和 `remoteId`
   - `startAutoSync(intervalMs = 30000): () => void` — 返回 stop 函数
   - `syncDown(): Promise<void>` — 从服务器拉取远程文件列表，合并到本地
2. **启动时机**: 在 `ChatPageContent` 的 `useEffect` 中，用户认证成功后启动
3. **冲突策略**: 以本地修改时间为准，本地较新则覆盖远程，反之拉取远程

---

## 阶段二：文档编辑器 (Word 风格)

### Task 2.1: TipTap 文档编辑器

**新建文件:**
- `chat-app/frontend/src/components/office/office-layout.tsx` — Office 通用布局壳
- `chat-app/frontend/src/components/office/document-editor.tsx` — 文档编辑器
- `chat-app/frontend/src/components/office/document-toolbar.tsx` — Ribbon 工具栏

**设计决策:**
1. **OfficeLayout**:
   - 顶部标题栏（48px 高）：返回按钮、文件类型图标、可编辑文件名（input）、保存状态指示、导出按钮
   - 主色调 MS Office 蓝 `#2564cf`
   - 画布背景 `#f3f3f3`
   - 接收 `fileId`, `fileType`, `title`, `children`, `onBack`, `onSave`, `onExport` props
2. **DocumentEditor**:
   - TipTap Editor 实例，`useEditor` hook
   - 编辑区 A4 尺寸（21cm × 29.7cm）白色背景，居中，阴影模拟纸张
   - `onUpdate` debounce 500ms 写入 IndexedDB
   - 加载时从 IndexedDB 读取 `content`（TipTap JSON）
   - 导出：调用 `POST /api/files/{id}/export?format=docx` 下载
3. **DocumentToolbar**:
   - Ribbon 风格分组：剪贴板（撤销/重做）、字体（加粗/斜体/下划线/删除线）、段落（对齐/列表/引用）、样式（标题 H1-H3）
   - 使用 lucide-react 图标
   - 每个按钮调用对应的 TipTap editor chain command

**依赖安装:**
```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-underline @tiptap/extension-text-align @tiptap/extension-link @tiptap/extension-highlight @tiptap/extension-placeholder
```

---

## 阶段三：电子表格编辑器 (Excel 风格)

### Task 3.1: Canvas 表格引擎

**新建文件:**
- `chat-app/frontend/src/components/office/spreadsheet-editor.tsx` — 表格编辑器
- `chat-app/frontend/src/components/office/spreadsheet-toolbar.tsx` — 表格工具栏

**设计决策:**
1. **数据模型**:
   - `CellData: { value: string; formula?: string; style?: CellStyle }`
   - `SheetData: { name: string; cells: Record<string, CellData> }`
   - `SpreadsheetData: { sheets: SheetData[]; activeSheetIndex: number }`
2. **渲染**:
   - 不使用 Canvas API，使用 CSS Grid 渲染表格（性能足够，且易实现）
   - 100 行 × 26 列（A-Z），列宽 100px，行高 28px
   - 行号列和列标行 `position: sticky` 吸顶
   - 虚拟滚动：仅渲染可视区域 + 缓冲区（使用 IntersectionObserver 或固定渲染前 50 行）
3. **交互**:
   - 单击选中 → 显示蓝色边框
   - 双击或按 Enter → 进入编辑模式（input 覆盖在单元格上）
   - 方向键导航选中
   - 公式栏：顶部显示当前单元格地址（如 A1）和值，fx 前缀
4. **自动保存**: 每次 `onBlur` 或 1 秒 debounce 写入 IndexedDB
5. **公式引擎（基础）**: 仅支持 `=A1+B1` 简单引用，使用 `new Function` 安全计算（白名单校验）

---

## 阶段四：演示文稿编辑器 (PowerPoint 风格)

### Task 4.1: 幻灯片编辑器

**新建文件:**
- `chat-app/frontend/src/components/office/presentation-editor.tsx` — 演示编辑器主组件
- `chat-app/frontend/src/components/office/presentation-toolbar.tsx` — 演示工具栏
- `chat-app/frontend/src/components/office/slide-thumbnail.tsx` — 左侧缩略图面板
- `chat-app/frontend/src/components/office/slide-canvas.tsx` — 幻灯片画布

**设计决策:**
1. **数据模型**:
   - `SlideElement: { id: string; type: "text" | "shape"; x: number; y: number; width: number; height: number; content: string; style?: any }`
   - `SlideData: { id: string; elements: SlideElement[]; background?: string }`
   - `PresentationData: { slides: SlideData[]; activeSlideIndex: number }`
2. **SlideThumbnail**:
   - 左侧 192px 宽，#f3f3f3 背景
   - 顶部标题 + 新建幻灯片按钮
   - 每个缩略图 16:10 比例（192×120），选中蓝色边框
   - 右键/悬停显示删除按钮（至少保留 1 张）
3. **SlideCanvas**:
   - 960×540px 白色画布（16:9），居中，灰色背景
   - 文本框：点击添加，拖拽移动（mousedown/mousemove/mouseup），双击编辑
   - 选中元素显示蓝色边框 + 拖拽手柄
   - 使用绝对定位实现自由布局
4. **自动保存**: 每次操作后 debounce 1000ms 写入 IndexedDB

---

## 阶段五：Office 工作区集成

### Task 5.1: 统一编辑区路由与集成

**新建文件:**
- `chat-app/frontend/src/components/office/office-area.tsx` — 统一编辑区入口

**修改文件:**
- `chat-app/frontend/src/components/chat-layout.tsx` — 集成 Office 编辑区

**设计决策:**
1. **OfficeArea 组件**:
   - 接收 `fileId: string`, `fileType: "document" | "spreadsheet" | "presentation"`
   - 从 IndexedDB 加载文件数据和内容
   - 根据 `fileType` 分发到 DocumentEditor / SpreadsheetEditor / PresentationEditor
   - 加载中显示 spinner
   - `onBack` 回调清空 `selectedId` 和 `selectedType`
2. **ChatLayout 修改**:
   - `selectedType` 扩展为 `"conversation" | "group" | "document" | "spreadsheet" | "presentation"`
   - 主内容区逻辑：
     - `activeTab === "agent"` → AgentPanel
     - `selectedType` 为 Office 类型 → OfficeArea
     - `selectedId` 存在 → ChatArea
     - 否则 → 空状态
   - 文件浏览器中点击文件时设置 `selectedType` 和 `selectedId`

---

## 执行顺序与依赖关系

| 任务 | 依赖 | 说明 |
|------|------|------|
| Task 1.1 后端文件服务 | 无 | 新增模型、路由、转换器 |
| Task 1.2 前端文件浏览器 | Task 1.1 | Dexie + 文件列表 UI |
| Task 1.3 本地同步服务 | Task 1.2 | SyncService，应用启动时初始化 |
| Task 2.1 文档编辑器 | Task 1.2 | TipTap + OfficeLayout |
| Task 3.1 表格编辑器 | Task 1.2 | CSS Grid 表格引擎 |
| Task 4.1 演示编辑器 | Task 1.2 | 幻灯片画布 + 缩略图 |
| Task 5.1 Office 集成 | Task 2.1, 3.1, 4.1 | OfficeArea + ChatLayout 改造 |

---

## 文件清单汇总

### 后端新建
1. `chat-app/backend/services/office_converter.py`
2. `chat-app/backend/routers/files.py`
3. `chat-app/backend/requirements-office.txt`

### 后端修改
4. `chat-app/backend/models.py` — 添加 FileRecord
5. `chat-app/backend/schemas.py` — 添加 FileRecord schemas
6. `chat-app/backend/main.py` — 注册 files router

### 前端新建
7. `chat-app/frontend/src/lib/file-store.ts`
8. `chat-app/frontend/src/lib/file-api.ts`
9. `chat-app/frontend/src/lib/sync-service.ts`
10. `chat-app/frontend/src/components/file-tree.tsx`
11. `chat-app/frontend/src/components/file-explorer.tsx`
12. `chat-app/frontend/src/components/office/office-layout.tsx`
13. `chat-app/frontend/src/components/office/document-editor.tsx`
14. `chat-app/frontend/src/components/office/document-toolbar.tsx`
15. `chat-app/frontend/src/components/office/spreadsheet-editor.tsx`
16. `chat-app/frontend/src/components/office/spreadsheet-toolbar.tsx`
17. `chat-app/frontend/src/components/office/presentation-editor.tsx`
18. `chat-app/frontend/src/components/office/presentation-toolbar.tsx`
19. `chat-app/frontend/src/components/office/slide-thumbnail.tsx`
20. `chat-app/frontend/src/components/office/slide-canvas.tsx`
21. `chat-app/frontend/src/components/office/office-area.tsx`

### 前端修改
22. `chat-app/frontend/src/components/chat-layout.tsx`
23. `chat-app/frontend/src/lib/api.ts` — 扩展 api.files
24. `chat-app/frontend/package.json` — 添加依赖

---

## 设计原则与约束

1. **本地优先**: 所有编辑操作先写 IndexedDB，网络仅用于同步和格式转换
2. **MS Office 参照**: Ribbon 工具栏 + 文档画布模式，快捷键保持一致
3. **渐进可用**: 每个编辑器独立可用，不互相阻塞
4. **文件格式标准化**: 内部 JSON 中间格式，导入/导出时转换 Office 标准格式
5. **聊天集成**: 文件可像消息一样发送，接收方直接在工作区打开编辑
6. **API 一致性**: 错误响应、分页、认证方式与现有代码完全一致
7. **无虚构数据**: 所有字段、枚举、示例均来自真实代码或合理推导
