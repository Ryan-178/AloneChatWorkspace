# 本地原生 Office 工作区实现计划

**目标:** 在 ChatAgent Workspace 中增加本地优先、原生体验的 Office 套件（类 Word / Excel / PowerPoint），支持离线编辑、Office 文件格式导入导出，并深度集成到现有聊天和工作区体系中。

**架构策略:**
- **本地优先 (Local-First):** 核心编辑在浏览器 IndexedDB 完成，确保离线可用；网络可用时按需同步到后端
- **纯前端渲染引擎:** 文档/表格/幻灯片编辑器均为前端 SPA 组件，后端仅负责文件格式转换和持久化存储
- **MS Office 兼容:** 导入/导出标准 `.docx` / `.xlsx` / `.pptx` 格式，UI 布局和交互逻辑参照 Microsoft Office 桌面版
- **渐进增强:** 三个编辑器独立开发，每个完成后即可独立使用，互不阻塞

**技术栈:**
- 前端编辑器: TipTap (文档)、自定义 Canvas 引擎 (表格)、自定义 Slide 引擎 (演示)
- 文件格式: `python-docx` / `openpyxl` / `python-pptx` (后端转换)
- 本地存储: Dexie.js (IndexedDB 封装)
- 后端 API: FastAPI 文件上传/下载/转换端点
- UI 框架: 延续现有 Radix UI + Tailwind CSS 风格

---

## 阶段一：Office 文件基础设施

### Task 1.1: 后端 Office 文件转换服务

**文件:**
- 新建: `chat-app/backend/services/office_converter.py`
- 新建: `chat-app/backend/routers/files.py`
- 修改: `chat-app/backend/models.py` - 新增 FileRecord 模型
- 修改: `chat-app/backend/schemas.py` - 新增文件 Schema
- 修改: `chat-app/backend/main.py` - 注册文件路由
- 新建: `chat-app/backend/requirements-office.txt`

**内容:**
- 使用 `python-docx` / `openpyxl` / `python-pptx` 实现 Office 文件 ↔ JSON 双向转换
- `OfficeConverter` 类，支持 `.docx` / `.xlsx` / `.pptx` 三种格式的解析和导出
- `FileRecord` 模型: id, filename, stored_path, file_size, file_type (document/spreadsheet/presentation/other), uploader_id, preview_data (JSON), created_at
- 文件 REST API: `POST /api/files/upload`, `GET /api/files/`, `GET /api/files/{id}/download`, `DELETE /api/files/{id}`

### Task 1.2: 前端文件浏览器与本地存储

**文件:**
- 新建: `chat-app/frontend/src/lib/file-store.ts` - IndexedDB 存储层
- 新建: `chat-app/frontend/src/lib/file-api.ts` - 文件 API 客户端
- 新建: `chat-app/frontend/src/components/file-tree.tsx` - 文件树组件
- 新建: `chat-app/frontend/src/components/file-explorer.tsx` - 文件浏览器
- 修改: `chat-app/frontend/src/components/chat-layout.tsx` - 集成文件 Tab

**步骤:**
1. 安装 Dexie.js: `npm install dexie`
2. 实现 `FileDB` 继承 Dexie，files 表: id, filename, fileType, content (JSON), updatedAt, synced, remoteId
3. 文件树组件支持文件夹展开/收起、文件类型图标、选中高亮
4. 文件浏览器包含: 新建(文档/表格/演示)菜单、导入 Office 文件按钮、本地文件列表
5. 在聊天布局侧边栏新增"文件" Tab，切换显示 FileExplorer

### Task 1.3: 本地文件同步服务

**文件:**
- 新建: `chat-app/frontend/src/lib/sync-service.ts`

**内容:**
- `SyncService` 类: `syncAll()` 遍历未同步文件，调用 API 上传，更新 synced 状态
- `startAutoSync(intervalMs=30000)` 返回停止函数
- 在应用启动时调用 `syncService.startAutoSync()`

---

## 阶段二：文档编辑器 (Word 风格)

### Task 2.1: TipTap 文档编辑器

**文件:**
- 新建: `chat-app/frontend/src/components/office/office-layout.tsx` - Office 通用布局
- 新建: `chat-app/frontend/src/components/office/document-editor.tsx` - 文档编辑器
- 新建: `chat-app/frontend/src/components/office/document-toolbar.tsx` - 文档工具栏

**安装依赖:**
```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-underline @tiptap/extension-text-align @tiptap/extension-link @tiptap/extension-highlight
```

**Office 通用布局 (office-layout.tsx):**
- 顶部标题栏: 返回按钮、文件类型图标、文件名、保存/导出按钮
- 使用 MS Office 蓝色 (#2564cf) 作为主色调
- 浅灰色背景 (#f3f3f3) 模拟 Office 界面

**文档编辑器 (document-editor.tsx):**
- 基于 TipTap 的 WYSIWYG 编辑器
- 编辑区为 A4 纸张尺寸 (21cm × 29.7cm) 白色背景，居中显示在灰色画布上
- 自动保存: `onUpdate` 时将 HTML 内容写入 IndexedDB
- 导出: 调用后端 API 将 HTML 转换为 .docx 格式下载

**文档工具栏 (document-toolbar.tsx):**
- Ribbon 风格工具栏: 撤销/重做、加粗/斜体/下划线/删除线、左中右两端对齐、有序/无序列表/引用、标题选择器
- 分隔线分组，hover 高亮效果

---

## 阶段三：电子表格编辑器 (Excel 风格)

### Task 3.1: Canvas 表格引擎

**文件:**
- 新建: `chat-app/frontend/src/components/office/spreadsheet-editor.tsx` - 表格编辑器
- 新建: `chat-app/frontend/src/components/office/spreadsheet-toolbar.tsx` - 表格工具栏

**表格引擎实现:**
- 100 行 × 26 列 (A-Z) 的网格，列宽 100px，行高 28px
- 行号 (1-100) 和列标 (A-Z) 固定头部，滚动时吸顶
- 单元格选择: 单击选中，双击进入编辑模式
- 键盘导航: 方向键移动选中单元格，Enter 进入编辑，Escape 退出
- 公式栏: 显示当前选中单元格地址 (如 A1) 和编辑值，fx 前缀
- Sheet 标签: 底部显示 Sheet1，蓝色下划线高亮当前 Sheet
- 自动保存: 每次单元格修改后写入 IndexedDB

**表格工具栏 (spreadsheet-toolbar.tsx):**
- 撤销/重做、字体选择器、字号选择器、加粗/斜体、对齐方式、填充颜色
- MS Excel 风格灰色背景 (#f8f8f8)

---

## 阶段四：演示文稿编辑器 (PowerPoint 风格)

### Task 4.1: 幻灯片编辑器

**文件:**
- 新建: `chat-app/frontend/src/components/office/presentation-editor.tsx` - 演示编辑器
- 新建: `chat-app/frontend/src/components/office/presentation-toolbar.tsx` - 演示工具栏
- 新建: `chat-app/frontend/src/components/office/slide-thumbnail.tsx` - 缩略图面板
- 新建: `chat-app/frontend/src/components/office/slide-canvas.tsx` - 幻灯片画布

**幻灯片缩略图面板 (slide-thumbnail.tsx):**
- 左侧 192px 宽，灰色背景 (#f3f3f3)
- 顶部"幻灯片"标题 + 新建按钮
- 每个缩略图 16:10 比例，选中时蓝色边框 (#2564cf)
- 支持删除按钮（至少保留一张）

**幻灯片画布 (slide-canvas.tsx):**
- 960×540px 白色画布，居中显示在灰色背景中
- 文本框: 支持添加、拖拽移动 (mousedown/mousemove/mouseup)、双击编辑文本
- 选中时蓝色边框

**演示编辑器主组件 (presentation-editor.tsx):**
- 管理幻灯片列表和当前索引
- 新增/删除幻灯片操作
- 修改后自动保存到 IndexedDB

---

## 阶段五：Office 工作区集成

### Task 5.1: 统一编辑区路由

**文件:**
- 新建: `chat-app/frontend/src/components/office/office-area.tsx` - 统一编辑区入口
- 修改: `chat-app/frontend/src/components/chat-layout.tsx` - 集成 Office 编辑区

**OfficeArea 组件:**
- 根据 fileType 分发到 DocumentEditor / SpreadsheetEditor / PresentationEditor
- 从 IndexedDB 加载文件数据
- 加载中显示提示

**ChatLayout 修改:**
- 扩展 selectedType 类型: `"conversation" | "group" | "document" | "spreadsheet" | "presentation"`
- 当 selectedType 为 Office 类型时，渲染 OfficeArea 替代 ChatArea
- OfficeArea 的 onBack 回调清空选中状态

---

## 执行顺序与依赖关系

| 任务 | 依赖 | 预计工时 |
|------|------|----------|
| Task 1.1 后端文件服务 | 无 | ~3h |
| Task 1.2 前端文件浏览器 | Task 1.1 | ~3h |
| Task 1.3 本地同步服务 | Task 1.2 | ~1h |
| Task 2.1 文档编辑器 | Task 1.2 | ~4h |
| Task 3.1 表格编辑器 | Task 1.2 | ~4h |
| Task 4.1 演示编辑器 | Task 1.2 | ~4h |
| Task 5.1 Office 集成 | Task 2.1, 3.1, 4.1 | ~2h |

**总计:** ~21 小时

---

## 设计原则

1. **本地优先:** 所有编辑操作在浏览器 IndexedDB 完成，网络仅用于同步和文件格式转换
2. **MS Office 参照:** UI 布局遵循 Ribbon 工具栏 + 文档画布模式，快捷键（Ctrl+B/I/U）保持一致
3. **渐进可用:** 每个编辑器完成后独立可用，不互相阻塞
4. **文件格式标准化:** 所有编辑器内部使用 JSON 作为中间格式，导入/导出时转换为 Office 标准格式
5. **聊天集成:** 文件可像消息一样通过聊天发送，接收方直接在工作区打开编辑

---

## 架构图示

```
┌─────────────────────────────────────────────────────────┐
│                   浏览器 (Frontend)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐      │
│  │ File     │  │ Office   │  │ IndexedDB        │      │
│  │ Explorer │──│ Editor   │──│ (本地优先存储)    │      │
│  └──────────┘  └──────────┘  └────────┬─────────┘      │
│                                       │                  │
│                               ┌───────▼────────┐        │
│                               │ Sync Service   │        │
│                               │ (自动同步引擎)  │        │
│                               └───────┬────────┘        │
└───────────────────────────────────────┼──────────────────┘
                                        │ HTTP
┌───────────────────────────────────────▼──────────────────┐
│                   服务器 (Backend)                        │
│  ┌──────────────┐  ┌──────────────────┐                 │
│  │ File API     │──│ OfficeConverter  │                 │
│  │ (上传/下载)  │  │ (docx/xlsx/pptx) │                 │
│  └──────┬───────┘  └──────────────────┘                 │
│         │                                                 │
│  ┌──────▼───────┐                                       │
│  │ PostgreSQL   │                                       │
│  │ (FileRecord) │                                       │
│  └──────────────┘                                       │
└──────────────────────────────────────────────────────────┘
```
