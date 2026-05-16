#### ChatAgent Workspace 前端重建 - 任务清单

## Phase 1: 基础框架

### Task 1.1: Next.js 项目初始化

- [ ] 创建 Next.js 16 项目（App Router）
- [ ] 配置 TypeScript 路径别名 `@/*`
- [ ] 安装并配置 Tailwind CSS v4
- [ ] 安装并配置 shadcn/ui
- [ ] 设置 CSS 变量主题系统
- [ ] 配置 ESLint 和 Prettier

### Task 1.2: 设计系统组件

- [ ] 创建 `src/lib/utils.ts`（cn 合并工具函数）
- [ ] 创建 `tailwind.config.ts` 设计系统配置
- [ ] 创建 `globals.css` MS Office 风格主题变量
- [ ] 创建基础 UI 组件库：
  - [ ] Button（Primary/Secondary/Ghost）
  - [ ] Input
  - [ ] Dropdown Menu
  - [ ] Modal/Dialog
  - [ ] Tabs
  - [ ] Avatar
  - [ ] Badge
  - [ ] Tooltip

### Task 1.3: 应用外壳布局

- [ ] 创建 `AppShell` 组件（三栏布局容器）
- [ ] 创建 `TopBar` 组件：
  - [ ] Logo + App Launcher 图标
  - [ ] 全局搜索框
  - [ ] 通知图标
  - [ ] 用户头像下拉菜单
- [ ] 创建 `NavBar` 组件：
  - [ ] 48px 固定宽度
  - [ ] 图标导航项（首页、文件、Office、设置）
  - [ ] Tooltip 提示
  - [ ] 工作区快捷入口
- [ ] 创建响应式布局逻辑

### Task 1.4: 路由系统

- [ ] 配置 Next.js App Router 结构
- [ ] 创建 `/` 首页重定向
- [ ] 创建 `/workspace/[workspaceId]` 路由
- [ ] 创建 `/workspace/[workspaceId]/files` 路由
- [ ] 创建 `/workspace/[workspaceId]/files/[fileId]` 路由
- [ ] 创建 `/workspace/[workspaceId]/settings` 路由

***

## Phase 2: 工作区系统

### Task 2.1: 工作区 API 客户端

- [ ] 创建 `src/lib/api.ts` 扩展
- [ ] 实现 `getWorkspaces()` - 获取工作区列表
- [ ] 实现 `createWorkspace(data)` - 创建工作区
- [ ] 实现 `getWorkspace(id)` - 获取工作区详情
- [ ] 实现 `updateWorkspace(id, data)` - 更新工作区
- [ ] 实现 `deleteWorkspace(id)` - 删除工作区
- [ ] 实现成员管理 API：
  - [ ] `getMembers(workspaceId)`
  - [ ] `inviteMember(workspaceId, data)`
  - [ ] `removeMember(workspaceId, userId)`
  - [ ] `updateMemberRole(workspaceId, userId, role)`

### Task 2.2: 工作区切换器

- [ ] 创建 `WorkspaceSwitcher` 组件
- [ ] 下拉选择器显示当前工作区
- [ ] 工作区列表（带图标）
- [ ] "创建工作区" 按钮
- [ ] 工作区设置快捷入口
- [ ] localStorage 持久化当前工作区

### Task 2.3: 工作区列表页面

- [ ] 创建 `WorkspaceListPage` 组件
- [ ] 网格布局展示工作区卡片
- [ ] 工作区卡片：图标 + 名称 + 成员数 + 操作按钮
- [ ] 新建工作区 Modal
- [ ] 删除工作区确认 Dialog

### Task 2.4: 工作区详情页

- [ ] 创建 `WorkspacePage` 组件
- [ ] 工作区 Header（名称 + 成员数 + 设置按钮）
- [ ] 快速入口：最近文件、收藏
- [ ] 工作区统计概览

### Task 2.5: 工作区设置面板

- [ ] 创建 `WorkspaceSettingsModal` 组件
- [ ] Tab 1 - 基本信息（名称、描述、图标）
- [ ] Tab 2 - 成员管理：
  - [ ] 成员列表（头像 + 名称 + 邮箱 + 角色 Badge）
  - [ ] 邀请成员表单
  - [ ] 修改角色下拉
  - [ ] 移除成员按钮
  - [ ] 角色图标（owner 皇冠、admin 盾牌、member 用户）

***

## Phase 3: 文件浏览器

### Task 3.1: 文件存储层

- [ ] 安装 Dexie.js：`npm install dexie@4`
- [ ] 创建 `src/lib/file-store.ts`
- [ ] 定义 IndexedDB Schema：
  - [ ] `files` 表：id, filename, fileType, content, updatedAt, synced, remoteId
- [ ] 实现 CRUD 操作方法
- [ ] 实现同步状态管理

### Task 3.2: 文件 API 客户端

- [ ] 扩展 `src/lib/api.ts`
- [ ] 实现 `uploadFile(file, workspaceId)` - 上传文件
- [ ] 实现 `listFiles(workspaceId, params)` - 文件列表
- [ ] 实现 `getFile(id)` - 获取文件元数据
- [ ] 实现 `downloadFile(id)` - 下载文件
- [ ] 实现 `deleteFile(id)` - 删除文件
- [ ] 实现 `convertFile(id, format)` - 转换格式

### Task 3.3: 文件同步服务

- [ ] 创建 `src/lib/sync-service.ts`
- [ ] 实现 `syncAll()` - 遍历未同步文件并上传
- [ ] 实现 `startAutoSync(interval)` - 自动同步定时器
- [ ] 实现 `syncDown()` - 从服务器拉取文件
- [ ] 冲突处理策略（以本地时间为准）
- [ ] 在应用启动时初始化同步服务

### Task 3.4: 文件浏览器 UI

- [ ] 创建 `FileExplorer` 组件
- [ ] 顶部工具栏：
  - [ ] 视图切换（网格/列表）
  - [ ] 新建下拉菜单（文档/表格/演示）
  - [ ] 排序选项
  - [ ] 导入按钮
- [ ] 文件列表/网格：
  - [ ] 文件类型图标
  - [ ] 文件名 + 修改时间
  - [ ] 选中高亮
  - [ ] 右键上下文菜单
- [ ] Breadcrumb 路径导航
- [ ] 空状态提示
- [ ] Drag & Drop 上传支持

### Task 3.5: 文件操作

- [ ] 新建文件（创建空白 Office 文档）
- [ ] 重命名文件（inline 编辑）
- [ ] 复制/移动文件
- [ ] 删除文件（确认 Dialog）
- [ ] 文件详情面板

***

## Phase 4: Office 编辑器

### Task 4.1: Office 通用布局

- [ ] 创建 `OfficeLayout` 组件
- [ ] 顶部标题栏（48px）：
  - [ ] 返回按钮
  - [ ] 文件类型图标
  - [ ] 可编辑文件名
  - [ ] 保存状态指示
  - [ ] 导出按钮
- [ ] MS Office 蓝主色调 `#2564cf`
- [ ] 画布背景 `#f3f3f3`

### Task 4.2: Word 文档编辑器

#### 4.2.1 依赖安装

```bash
npm install @tiptap/react @tiptap/starter-kit @tiptap/extension-underline @tiptap/extension-text-align @tiptap/extension-highlight @tiptap/extension-link @tiptap/extension-placeholder
```

#### 4.2.2 文档编辑器核心

- [ ] 创建 `DocumentEditor` 组件
- [ ] TipTap Editor 实例配置
- [ ] A4 纸张尺寸（21cm × 29.7cm）白色背景
- [ ] 富文本内容加载（从 IndexedDB）
- [ ] 自动保存（debounce 500ms）
- [ ] 内容更新保存逻辑

#### 4.2.3 Ribbon 工具栏

- [ ] 创建 `DocumentToolbar` 组件
- [ ] Tab 分组：开始、插入、布局、审阅、视图
- [ ] 剪贴板组：撤销、重做、剪切、复制、粘贴
- [ ] 字体组：加粗、斜体、下划线、删除线、字体、字号、颜色
- [ ] 段落组：对齐（左/中/右/两端）、缩进、列表（有序/无序）
- [ ] 样式组：标题 H1-H3、引用、正文
- [ ] 每个按钮调用对应 TipTap command

#### 4.2.4 导出功能

- [ ] 导出为 DOCX 格式
- [ ] 导出为 HTML 格式
- [ ] 导出为 PDF 格式（未来）

### Task 4.3: Excel 表格编辑器

#### 4.3.1 表格数据模型

- [ ] `CellData`: { value: string; formula?: string; style?: CellStyle }
- [ ] `SheetData`: { name: string; cells: Record\<string, CellData> }
- [ ] `SpreadsheetData`: { sheets: SheetData\[]; activeSheetIndex: number }

#### 4.3.2 表格渲染组件

- [ ] 创建 `SpreadsheetEditor` 组件
- [ ] CSS Grid 布局（100行 × 26列）
- [ ] 列宽 100px，行高 28px
- [ ] 固定行号列和列标题行（sticky）
- [ ] 虚拟滚动（IntersectionObserver）

#### 4.3.3 单元格交互

- [ ] 单击选中（蓝色边框）
- [ ] 双击/Enter 进入编辑模式
- [ ] 方向键导航
- [ ] 选中区域高亮
- [ ] 剪贴板操作（Ctrl+C/V/X）

#### 4.3.4 公式栏

- [ ] 创建 `FormulaBar` 组件
- [ ] 显示当前单元格地址（如 A1）
- [ ] 显示单元格内容/公式
- [ ] fx 前缀图标

#### 4.3.5 Sheet 管理

- [ ] Sheet 标签栏（底部）
- [ ] Sheet 切换
- [ ] 新建 Sheet
- [ ] 重命名 Sheet
- [ ] 删除 Sheet（至少保留 1 个）

#### 4.3.6 公式引擎

- [ ] 创建 `safe-formula-evaluator.ts`
- [ ] 支持运算符：+, -, \*, /, ^, %
- [ ] 支持函数：SUM, AVERAGE, COUNT, MAX, MIN, IF
- [ ] 支持单元格引用：A1, B2:C5
- [ ] 循环引用检测

#### 4.3.7 表格工具栏

- [ ] 创建 `SpreadsheetToolbar` 组件
- [ ] 撤销/重做
- [ ] 字体格式（加粗、斜体、颜色）
- [ ] 对齐方式
- [ ] 边框样式
- [ ] 填充颜色
- [ ] 行/列插入/删除

### Task 4.4: PowerPoint 演示编辑器

#### 4.4.1 幻灯片数据模型

- [ ] `SlideElement`: { id, type, x, y, width, height, content, style }
- [ ] `SlideData`: { id, elements, background }
- [ ] `PresentationData`: { slides, activeSlideIndex }

#### 4.4.2 幻灯片缩略图面板

- [ ] 创建 `SlideThumbnails` 组件
- [ ] 左侧 192px 宽
- [ ] 灰色背景 `#f3f3f3`
- [ ] 缩略图 16:10 比例（192×120）
- [ ] 选中蓝色边框
- [ ] 新建幻灯片按钮
- [ ] 删除幻灯片（右键/悬停）
- [ ] 拖拽排序

#### 4.4.3 幻灯片画布

- [ ] 创建 `SlideCanvas` 组件
- [ ] 960×540px 白色画布（16:9）
- [ ] 灰色背景居中显示
- [ ] 文本框添加/编辑
- [ ] 形状添加（矩形、圆形、线条）
- [ ] 元素选中（蓝色边框）
- [ ] 拖拽移动（mousedown/mousemove/mouseup）
- [ ] 调整大小手柄
- [ ] 元素层级（置于顶层/底层）
- [ ] 删除元素（Delete 键）

#### 4.4.4 演示工具栏

- [ ] 创建 `PresentationToolbar` 组件
- [ ] Tab 分组：开始、插入、动画、幻灯片放映、视图
- [ ] 幻灯片操作：新建、删除、复制
- [ ] 元素操作：文本框、形状、图片
- [ ] 动画效果（未来扩展）

#### 4.4.5 演示编辑器主组件

- [ ] 创建 `PresentationEditor` 组件
- [ ] 管理幻灯片列表和当前索引
- [ ] 新增/删除幻灯片
- [ ] 自动保存到 IndexedDB

### Task 4.5: Office Area 统一入口

- [ ] 创建 `OfficeArea` 组件
- [ ] 根据 fileType 分发到对应编辑器
- [ ] 加载状态显示
- [ ] 错误处理
- [ ] onBack 回调清空选中

***

## Phase 5: 集成与优化

### Task 5.1: 后端 WebSocket 集成

- [ ] 创建 WebSocket 客户端服务
- [ ] 连接认证（JWT token）
- [ ] 消息发送/接收处理
- [ ] 心跳机制
- [ ] 重连逻辑

### Task 5.2: 用户认证流程

- [ ] 登录页面
- [ ] 注册页面
- [ ] JWT token 存储
- [ ] 路由守卫（未登录重定向）
- [ ] 登出功能

### Task 5.3: 性能优化

- [ ] 组件懒加载（Next.js dynamic）
- [ ] 图片优化（next/image）
- [ ] 虚拟列表（文件列表大时）
- [ ] 缓存策略

### Task 5.4: 响应式适配

- [ ] 移动端布局调整
- [ ] 平板适配
- [ ] 触摸交互支持

### Task 5.5: 国际化（未来）

- [ ] i18n 框架配置
- [ ] 中文语言包
- [ ] 英文语言包

***

## 任务依赖关系

```
Phase 1 (基础框架)
├── Task 1.1 ─┬─→ Task 1.2 ─┬─→ Task 1.3 ─┬─→ Task 1.4
              │              │              │
              └──────────────┴──────────────┘

Phase 2 (工作区系统) 依赖 Phase 1
├── Task 2.1 ─→ Task 2.2
├── Task 2.1 ─→ Task 2.3
├── Task 2.1 ─→ Task 2.4
└── Task 2.1, 2.4 ─→ Task 2.5

Phase 3 (文件浏览器) 依赖 Phase 2
├── Task 3.1 ─→ Task 3.2 ─→ Task 3.3
├── Task 3.2 ─→ Task 3.4 ─→ Task 3.5
└── Task 3.1, 3.4 ─→ Task 3.5

Phase 4 (Office 编辑器) 依赖 Phase 3
├── Task 4.1 ─┬─→ Task 4.2
├── Task 4.1 ─┴─→ Task 4.3
├── Task 4.1 ─┴─→ Task 4.4
└── Task 4.2, 4.3, 4.4 ─→ Task 4.5

Phase 5 (集成与优化) 依赖 Phase 4
├── Task 5.1 ─→ Task 5.2
├── Task 5.3 ─┬─→ Task 5.4 ─→ Task 5.5
└── Task 5.4 ─┘
```

***

## 执行优先级

1. **P0 - 核心功能**
   - Phase 1 全部（基础框架）
   - Phase 2 Task 2.1-2.2（工作区切换器）
2. **P1 - 主要功能**
   - Phase 2 Task 2.3-2.5（工作区管理）
   - Phase 3 全部（文件浏览器）
3. **P2 - Office 编辑器**
   - Phase 4 全部（Word/Excel/PowerPoint 编辑器）
4. **P3 - 增强功能**
   - Phase 5 全部（集成与优化）

