# ChatAgent Workspace 前端重建 - 检查清单

## Phase 1: 基础框架 ✓

### Task 1.1: Next.js 项目初始化
- [ ] Next.js 16 项目创建（App Router）
- [ ] TypeScript 路径别名 `@/*` 配置
- [ ] Tailwind CSS v4 安装和配置
- [ ] shadcn/ui 安装和初始化
- [ ] CSS 变量主题系统设置
- [ ] ESLint 和 Prettier 配置

### Task 1.2: 设计系统组件
- [ ] `src/lib/utils.ts` 工具函数
- [ ] `tailwind.config.ts` 设计配置
- [ ] `globals.css` Office 风格主题变量
- [ ] Button 组件（Primary/Secondary/Ghost）
- [ ] Input 组件
- [ ] Dropdown Menu 组件
- [ ] Modal/Dialog 组件
- [ ] Tabs 组件
- [ ] Avatar 组件
- [ ] Badge 组件
- [ ] Tooltip 组件

### Task 1.3: 应用外壳布局
- [ ] AppShell 三栏布局容器
- [ ] TopBar 组件
  - [ ] Logo + App Launcher
  - [ ] 全局搜索框
  - [ ] 通知图标
  - [ ] 用户头像下拉
- [ ] NavBar 组件
  - [ ] 48px 固定宽度
  - [ ] 图标导航项
  - [ ] Tooltip 提示
  - [ ] 工作区快捷入口
- [ ] 响应式布局逻辑

### Task 1.4: 路由系统
- [ ] Next.js App Router 结构
- [ ] `/` 首页重定向
- [ ] `/workspace/[workspaceId]` 路由
- [ ] `/workspace/[workspaceId]/files` 路由
- [ ] `/workspace/[workspaceId]/files/[fileId]` 路由
- [ ] `/workspace/[workspaceId]/settings` 路由

---

## Phase 2: 工作区系统 ✓

### Task 2.1: 工作区 API 客户端
- [ ] `getWorkspaces()`
- [ ] `createWorkspace(data)`
- [ ] `getWorkspace(id)`
- [ ] `updateWorkspace(id, data)`
- [ ] `deleteWorkspace(id)`
- [ ] `getMembers(workspaceId)`
- [ ] `inviteMember(workspaceId, data)`
- [ ] `removeMember(workspaceId, userId)`
- [ ] `updateMemberRole(workspaceId, userId, role)`

### Task 2.2: 工作区切换器
- [ ] WorkspaceSwitcher 组件
- [ ] 下拉选择器
- [ ] 工作区列表
- [ ] 创建工作区按钮
- [ ] localStorage 持久化

### Task 2.3: 工作区列表页面
- [ ] WorkspaceListPage 组件
- [ ] 工作区卡片网格
- [ ] 新建工作区 Modal
- [ ] 删除确认 Dialog

### Task 2.4: 工作区详情页
- [ ] WorkspacePage 组件
- [ ] Header 信息展示
- [ ] 快速入口
- [ ] 统计概览

### Task 2.5: 工作区设置面板
- [ ] WorkspaceSettingsModal 组件
- [ ] 基本信息 Tab
- [ ] 成员管理 Tab
  - [ ] 成员列表
  - [ ] 邀请成员表单
  - [ ] 修改角色下拉
  - [ ] 移除成员按钮
  - [ ] 角色图标

---

## Phase 3: 文件浏览器 ✓

### Task 3.1: 文件存储层
- [ ] Dexie.js 安装
- [ ] `src/lib/file-store.ts` 创建
- [ ] IndexedDB Schema 定义
- [ ] CRUD 操作方法
- [ ] 同步状态管理

### Task 3.2: 文件 API 客户端
- [ ] `uploadFile(file, workspaceId)`
- [ ] `listFiles(workspaceId, params)`
- [ ] `getFile(id)`
- [ ] `downloadFile(id)`
- [ ] `deleteFile(id)`
- [ ] `convertFile(id, format)`

### Task 3.3: 文件同步服务
- [ ] `src/lib/sync-service.ts`
- [ ] `syncAll()` 实现
- [ ] `startAutoSync(interval)`
- [ ] `syncDown()` 实现
- [ ] 冲突处理策略
- [ ] 启动时初始化

### Task 3.4: 文件浏览器 UI
- [ ] FileExplorer 组件
- [ ] 工具栏（视图切换、新建、排序、导入）
- [ ] 文件列表/网格视图
- [ ] 文件图标
- [ ] 右键上下文菜单
- [ ] Breadcrumb 导航
- [ ] 空状态提示
- [ ] Drag & Drop 支持

### Task 3.5: 文件操作
- [ ] 新建文件
- [ ] 重命名文件
- [ ] 复制/移动文件
- [ ] 删除文件确认
- [ ] 文件详情面板

---

## Phase 4: Office 编辑器 ✓

### Task 4.1: Office 通用布局
- [ ] OfficeLayout 组件
- [ ] 顶部标题栏
- [ ] 返回按钮
- [ ] 文件名编辑
- [ ] 保存状态指示
- [ ] 导出按钮
- [ ] MS Office 蓝主题

### Task 4.2: Word 文档编辑器

#### 依赖安装
- [ ] @tiptap/react
- [ ] @tiptap/starter-kit
- [ ] @tiptap/extension-underline
- [ ] @tiptap/extension-text-align
- [ ] @tiptap/extension-highlight
- [ ] @tiptap/extension-link
- [ ] @tiptap/extension-placeholder

#### 文档编辑器核心
- [ ] DocumentEditor 组件
- [ ] TipTap 配置
- [ ] A4 纸张尺寸
- [ ] 内容加载
- [ ] 自动保存
- [ ] 保存逻辑

#### Ribbon 工具栏
- [ ] DocumentToolbar 组件
- [ ] Tab 分组
- [ ] 剪贴板组
- [ ] 字体组
- [ ] 段落组
- [ ] 样式组
- [ ] TipTap commands 集成

#### 导出功能
- [ ] 导出 DOCX
- [ ] 导出 HTML
- [ ] 导出 PDF（可选）

### Task 4.3: Excel 表格编辑器

#### 表格数据模型
- [ ] CellData 类型
- [ ] SheetData 类型
- [ ] SpreadsheetData 类型

#### 表格渲染
- [ ] SpreadsheetEditor 组件
- [ ] CSS Grid 布局
- [ ] 行列固定
- [ ] 虚拟滚动

#### 单元格交互
- [ ] 单击选中
- [ ] 双击编辑
- [ ] 方向键导航
- [ ] 剪贴板操作

#### 公式栏
- [ ] FormulaBar 组件
- [ ] 单元格地址显示
- [ ] 内容/公式显示

#### Sheet 管理
- [ ] Sheet 标签栏
- [ ] 切换 Sheet
- [ ] 新建 Sheet
- [ ] 重命名 Sheet
- [ ] 删除 Sheet

#### 公式引擎
- [ ] safe-formula-evaluator.ts
- [ ] 运算符支持
- [ ] 内置函数（SUM, AVERAGE 等）
- [ ] 单元格引用
- [ ] 循环引用检测

#### 表格工具栏
- [ ] SpreadsheetToolbar 组件
- [ ] 撤销/重做
- [ ] 字体格式
- [ ] 对齐方式
- [ ] 边框样式
- [ ] 填充颜色
- [ ] 行/列操作

### Task 4.4: PowerPoint 演示编辑器

#### 幻灯片数据模型
- [ ] SlideElement 类型
- [ ] SlideData 类型
- [ ] PresentationData 类型

#### 缩略图面板
- [ ] SlideThumbnails 组件
- [ ] 缩略图列表
- [ ] 选中高亮
- [ ] 新建/删除
- [ ] 拖拽排序

#### 幻灯片画布
- [ ] SlideCanvas 组件
- [ ] 画布渲染
- [ ] 文本框添加/编辑
- [ ] 形状添加
- [ ] 元素选中
- [ ] 拖拽移动
- [ ] 调整大小
- [ ] 层级管理
- [ ] 删除元素

#### 演示工具栏
- [ ] PresentationToolbar 组件
- [ ] Tab 分组
- [ ] 幻灯片操作
- [ ] 元素操作

#### 演示编辑器
- [ ] PresentationEditor 组件
- [ ] 幻灯片管理
- [ ] 自动保存

### Task 4.5: Office Area 入口
- [ ] OfficeArea 组件
- [ ] fileType 分发
- [ ] 加载状态
- [ ] 错误处理
- [ ] onBack 回调

---

## Phase 5: 集成与优化 ✓

### Task 5.1: WebSocket 集成
- [ ] WebSocket 客户端
- [ ] 连接认证
- [ ] 消息处理
- [ ] 心跳机制
- [ ] 重连逻辑

### Task 5.2: 用户认证
- [ ] 登录页面
- [ ] 注册页面
- [ ] JWT 存储
- [ ] 路由守卫
- [ ] 登出功能

### Task 5.3: 性能优化
- [ ] 组件懒加载
- [ ] 图片优化
- [ ] 虚拟列表
- [ ] 缓存策略

### Task 5.4: 响应式适配
- [ ] 移动端布局
- [ ] 平板适配
- [ ] 触摸支持

### Task 5.5: 国际化
- [ ] i18n 配置
- [ ] 中文语言包
- [ ] 英文语言包

---

## 质量检查清单

### UI/UX 检查
- [ ] 所有按钮有 hover 状态
- [ ] 所有图标使用 SVG（非 emoji）
- [ ] 颜色对比度符合 WCAG 标准
- [ ] Focus 状态可见（键盘导航）
- [ ] 加载状态显示
- [ ] 错误状态提示
- [ ] 空状态设计
- [ ] 动画流畅（150-300ms）
- [ ] 响应式断点正确

### 功能检查
- [ ] 表单验证正常
- [ ] 数据持久化正常
- [ ] 撤销/重做正常
- [ ] 快捷键正常工作
- [ ] 右键菜单正常
- [ ] 拖拽操作正常
- [ ] 文件上传/下载正常
- [ ] 导出功能正常

### 代码质量检查
- [ ] TypeScript 类型完整
- [ ] 组件 props 有类型定义
- [ ] 无 any 类型滥用
- [ ] 错误边界处理
- [ ] 异步操作正确处理
- [ ] 资源正确清理（useEffect cleanup）

### 性能检查
- [ ] 首屏加载 < 3s
- [ ] 组件渲染无明显卡顿
- [ ] 大列表无内存泄漏
- [ ] 图片懒加载生效
- [ ] 无不必要的重渲染

### 安全检查
- [ ] XSS 防护（用户输入转义）
- [ ] CSRF 防护
- [ ] 敏感信息不暴露在前端
- [ ] 越权访问防护
- [ ] 文件上传类型验证
