# ChatAgent Workspace 前端重建计划

> **目标：** 基于现有后端（agent-framework gateway），重新构建一个完整的、类似 MS Office 365 的前端应用
>
> **参考：** Microsoft Office 365 的 UI/UX 设计风格
>
> **技术栈：** Next.js 16 + React 19 + Tailwind CSS v4 + shadcn/ui

---

## 一、MS Office 365 设计分析

### 1.1 核心布局结构

```
┌─────────────────────────────────────────────────────────────────┐
│  [Logo] App Launcher │ Search Bar │ Notifications │ User Menu │
├─────────────────────────────────────────────────────────────────┤
│ ┌──────┐ ┌────────────────────────────────────────────────────┐│
│ │      │ │  Command Ribbon / Toolbar                         ││
│ │ Nav  │ ├────────────────────────────────────────────────────┤│
│ │ Bar  │ │                                                    ││
│ │      │ │                                                    ││
│ │ 48px │ │              Main Content Area                      ││
│ │      │ │              (Document / Spreadsheet / etc.)       ││
│ │      │ │                                                    ││
│ │      │ │                                                    ││
│ └──────┘ └────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 设计语言

| 元素 | MS Office 365 风格 |
|------|-------------------|
| **主色调** | Office Blue `#2564cf` |
| **背景色** | 白色 `#ffffff`、浅灰 `#f3f3f3` |
| **文字色** | 深灰 `#1a1a1a`、中灰 `#606060` |
| **边框色** | `#e0e0e0` |
| **激活态** | `#2564cf` 蓝色高亮 |
| **悬停态** | `#f5f5f5` 浅灰背景 |
| **圆角** | 4px（按钮、卡片）、8px（模态框） |
| **阴影** | `0 2px 4px rgba(0,0,0,0.1)` |
| **字体** | Segoe UI（系统）、Inter（Web 备选） |

### 1.3 功能模块

1. **App Launcher** - 应用启动器（类似 Office 365 的 waffle menu）
2. **Command Bar** - 命令栏/Ribbon 工具栏
3. **File Explorer** - 文件资源管理器（类似 OneDrive）
4. **Document Editor** - Word 风格文档编辑器
5. **Spreadsheet Editor** - Excel 风格表格编辑器
6. **Presentation Editor** - PowerPoint 风格演示编辑器
7. **Workspace Switcher** - 工作区切换器
8. **Settings Panel** - 设置面板

---

## 二、技术架构

### 2.1 目录结构

```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx              # 根布局
│   │   ├── page.tsx                # 首页/重定向
│   │   └── workspace/
│   │       └── [workspaceId]/
│   │           ├── page.tsx         # 工作区主页
│   │           ├── files/
│   │           │   └── page.tsx     # 文件浏览器
│   │           └── settings/
│   │               └── page.tsx     # 工作区设置
│   ├── components/
│   │   ├── layout/
│   │   │   ├── app-shell.tsx       # 应用外壳
│   │   │   ├── top-bar.tsx         # 顶部栏
│   │   │   ├── nav-bar.tsx         # 左侧导航栏
│   │   │   ├── command-ribbon.tsx  # 命令/Ribbon栏
│   │   │   └── side-panel.tsx      # 侧边面板
│   │   ├── workspace/
│   │   │   ├── workspace-switcher.tsx
│   │   │   ├── workspace-header.tsx
│   │   │   └── member-list.tsx
│   │   ├── files/
│   │   │   ├── file-explorer.tsx
│   │   │   ├── file-toolbar.tsx
│   │   │   └── file-card.tsx
│   │   └── office/
│   │       ├── office-layout.tsx   # Office 通用布局
│   │       ├── document-editor.tsx  # Word 风格
│   │       ├── spreadsheet-editor.tsx # Excel 风格
│   │       ├── presentation-editor.tsx # PowerPoint 风格
│   │       └── components/
│   │           ├── ribbon-toolbar.tsx
│   │           ├── formula-bar.tsx
│   │           ├── slide-canvas.tsx
│   │           └── slide-thumbnails.tsx
│   ├── lib/
│   │   ├── api.ts                  # API 客户端
│   │   ├── file-store.ts           # IndexedDB 存储
│   │   ├── sync-service.ts         # 同步服务
│   │   └── utils.ts
│   └── types/
│       ├── workspace.ts
│       ├── file.ts
│       └── office.ts
```

### 2.2 核心组件设计

#### App Shell（应用外壳）
```tsx
interface AppShellProps {
  children: React.ReactNode;
}

// 三栏布局：
// - TopBar: 56px 高，固定顶部
// - NavBar: 48px 宽，固定左侧
// - Content: flex-1，自适应
```

#### Top Bar（顶部栏）
- 左侧：Logo + App Launcher 图标
- 中间：全局搜索框
- 右侧：通知图标 + 用户头像下拉菜单

#### Nav Bar（左侧导航栏）
- 48px 宽，图标 + tooltip
- 导航项：首页、文件、Office 应用、设置
- 底部：工作区切换快捷入口

#### Command Ribbon（命令栏）
- 参考 Office Ribbon 设计
- Tab 切换：开始、插入、布局、审阅等
- 分组按钮 + 下拉菜单
- 上下文敏感（根据当前编辑内容显示不同工具）

---

## 三、API 设计（基于现有后端扩展）

### 3.1 工作区 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/workspaces | 获取工作区列表 |
| POST | /api/workspaces | 创建工作区 |
| GET | /api/workspaces/{id} | 获取工作区详情 |
| PUT | /api/workspaces/{id} | 更新工作区 |
| DELETE | /api/workspaces/{id} | 删除工作区 |
| GET | /api/workspaces/{id}/members | 获取成员列表 |
| POST | /api/workspaces/{id}/members | 邀请成员 |
| DELETE | /api/workspaces/{id}/members/{userId} | 移除成员 |

### 3.2 文件 API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/files | 获取文件列表 |
| POST | /api/files/upload | 上传文件 |
| GET | /api/files/{id} | 获取文件元数据 |
| GET | /api/files/{id}/download | 下载文件 |
| GET | /api/files/{id}/preview | 获取预览数据 |
| DELETE | /api/files/{id} | 删除文件 |
| POST | /api/files/{id}/convert | 转换文件格式 |
| POST | /api/files/{id}/export | 导出为指定格式 |

### 3.3 错误响应格式

```json
{
  "error": "ErrorCode",
  "message": "人类可读的错误信息",
  "details": {}
}
```

---

## 四、功能模块详细设计

### 4.1 工作区系统

**功能：**
- 创建、编辑、删除工作区
- 邀请成员、设置角色（owner/admin/member）
- 工作区级别资源隔离
- 工作区图标和主题色自定义

**UI：**
- WorkspaceSwitcher：下拉选择器，显示当前工作区名称
- 工作区设置 Modal：Tab 切换（基本信息/成员管理）
- 成员列表：头像 + 名称 + 邮箱 + 角色 Badge

### 4.2 文件浏览器（类似 OneDrive）

**功能：**
- 文件列表：网格/列表视图切换
- 文件类型图标：文档、表格、演示、其他
- 新建文件：创建空白文档/表格/演示
- 上传文件：支持 drag & drop
- 文件操作：重命名、复制、移动、删除
- 搜索过滤：按名称、类型、日期筛选

**UI：**
- 顶部工具栏：视图切换、新建按钮、排序选项
- 文件网格：图标 + 文件名 + 修改时间
- 右键菜单：上下文操作
- Breadcrumb：路径导航

### 4.3 Word 风格文档编辑器

**功能：**
- 富文本编辑：加粗、斜体、下划线、删除线
- 段落格式：对齐、缩进、行高
- 标题样式：H1、H2、H3
- 列表：有序、无序、任务列表
- 插入：链接、图片、表格
- 查找替换
- 字数统计
- 导出：DOCX、PDF、HTML

**Ribbon 工具栏：**
```
开始        插入        布局        审阅        视图
─────────────────────────────────────────────────────
剪贴板      图片       页面设置    拼写检查    大纲视图
字体       表格       段落        批注        缩放
段落       链接                  修订        全屏
样式       签名

[撤销] [重做] │ 文档标题 │ [保存] [导出]
```

**技术实现：**
- TipTap 编辑器核心
- 扩展：StarterKit, Underline, TextAlign, Highlight, Link, Placeholder
- A4 纸张尺寸：21cm × 29.7cm
- IndexedDB 本地存储
- 实时协作（未来扩展）

### 4.4 Excel 风格表格编辑器

**功能：**
- 单元格编辑：双击/Enter 编辑
- 公式支持：SUM, AVERAGE, VLOOKUP 等
- 格式设置：字体、颜色、对齐、边框
- 行/列操作：插入、删除、调整大小
- Sheet 管理：多 Sheet 切换
- 数据验证
- 图表插入（未来扩展）

**UI 布局：**
```
┌──────────────────────────────────────────────────────────────┐
│ [Ribbon: 开始 | 公式 | 数据 | 视图]                          │
├──────────────────────────────────────────────────────────────┤
│ fx │ =SUM(A1:A10)                              │ 100        │  ← 公式栏
├────┬────┬────┬────┬────┬────┬─────────────────────────────────┤
│    │ A  │ B  │ C  │ D  │ E  │ ...                              │
├────┼────┼────┼────┼────┼────┼─────────────────────────────────┤
│ 1  │    │    │    │    │    │                                  │
├────┼────┼────┼────┼────┼────┼─────────────────────────────────┤
│ 2  │    │    │    │    │    │                                  │
├────┼────┼────┼────┼────┼────┼─────────────────────────────────┤
│... │    │    │    │    │    │                                  │
├────┴────┴────┴────┴────┴────┴─────────────────────────────────┤
│ Sheet1 │ Sheet2 │ Sheet3 │ [+]                               │
└───────────────────────────────────────────────────────────────┘
```

**技术实现：**
- CSS Grid 渲染（100行 × 26列）
- 单元格坐标：A1 到 Z100
- 公式引擎：安全 eval + 函数白名单
- 虚拟滚动（可视区域渲染）
- IndexedDB 存储

### 4.5 PowerPoint 风格演示编辑器

**功能：**
- 幻灯片管理：新建、删除、复制、排序
- 元素编辑：文本框、形状、图片
- 布局模板：标题页、内容页、结束页
- 动画效果（未来扩展）
- 演讲者备注
- 幻灯片放映模式
- 导出：PPTX、PDF

**UI 布局：**
```
┌──────────────────────────────────────────────────────────────┐
│ [Ribbon: 开始 | 插入 | 动画 | 幻灯片放映 | 视图]              │
├────────────┬─────────────────────────────────────────────────┤
│ 缩略图     │                                                  │
│ ┌────┐    │                                                  │
│ │ 1  │    │                                                  │
│ └────┘    │              幻灯片画布                           │
│ ┌────┐    │              960 × 540 px                        │
│ │ 2  │    │              (16:9 比例)                          │
│ └────┘    │                                                  │
│ ┌────┐    │                                                  │
│ │ 3  │    │                                                  │
│ └────┘    │                                                  │
│ [+ 添加]   │                                                  │
└────────────┴─────────────────────────────────────────────────┘
```

**技术实现：**
- React 组件树管理幻灯片
- 绝对定位实现自由布局
- 拖拽调整元素位置/大小
- IndexedDB 存储

---

## 五、页面路由设计

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Redirect to `/workspace/default` | 首页重定向 |
| `/workspace/:workspaceId` | WorkspacePage | 工作区主页 |
| `/workspace/:workspaceId/files` | FileExplorerPage | 文件浏览器 |
| `/workspace/:workspaceId/files/:fileId` | OfficeEditorPage | Office 编辑器 |
| `/workspace/:workspaceId/settings` | WorkspaceSettingsPage | 工作区设置 |

---

## 六、设计系统

### 6.1 颜色变量

```css
:root {
  /* Primary */
  --office-blue: #2564cf;
  --office-blue-light: #3b6cd4;
  --office-blue-dark: #1e4db0;

  /* Background */
  --bg-primary: #ffffff;
  --bg-secondary: #f3f3f3;
  --bg-tertiary: #e8e8e8;

  /* Text */
  --text-primary: #1a1a1a;
  --text-secondary: #606060;
  --text-muted: #8a8a8a;

  /* Border */
  --border-light: #e0e0e0;
  --border-medium: #c0c0c0;

  /* Status */
  --success: #107c10;
  --warning: #ff8c00;
  --error: #d13438;

  /* Ribbon */
  --ribbon-bg: #f3f3f3;
  --ribbon-border: #e0e0e0;
}
```

### 6.2 组件规范

| 组件 | 圆角 | 阴影 | 边框 |
|------|------|------|------|
| Button Primary | 4px | none | none |
| Button Secondary | 4px | none | 1px solid #e0e0e0 |
| Card | 8px | 0 2px 4px rgba(0,0,0,0.1) | none |
| Modal | 8px | 0 8px 32px rgba(0,0,0,0.2) | none |
| Input | 4px | none | 1px solid #e0e0e0 |
| Dropdown | 4px | 0 4px 12px rgba(0,0,0,0.15) | 1px solid #e0e0e0 |

---

## 七、实施阶段

### Phase 1: 基础框架（1-2天）
- Next.js 项目初始化
- Tailwind CSS + shadcn/ui 配置
- 应用外壳布局（AppShell, TopBar, NavBar）
- 主题系统和设计变量

### Phase 2: 工作区系统（1-2天）
- 工作区切换器
- 工作区列表和详情页
- 成员管理 UI
- 工作区设置面板

### Phase 3: 文件浏览器（2-3天）
- 文件列表/网格视图
- 文件操作（新建、上传、删除、重命名）
- 文件搜索和过滤
- IndexedDB 本地存储

### Phase 4: Office 编辑器（5-7天）
- Word 文档编辑器（TipTap）
- Excel 表格编辑器（CSS Grid + 公式引擎）
- PowerPoint 演示编辑器（幻灯片画布）
- Ribbon 工具栏
- 文件导入/导出

### Phase 5: 集成与优化（2-3天）
- 与后端 WebSocket 集成
- 实时协作（未来扩展）
- 性能优化
- 响应式适配

---

## 八、技术依赖

```json
{
  "dependencies": {
    "next": "^16.0.0",
    "react": "^19.0.0",
    "@tiptap/react": "^2.x",
    "@tiptap/starter-kit": "^2.x",
    "@tiptap/extension-underline": "^2.x",
    "@tiptap/extension-text-align": "^2.x",
    "@tiptap/extension-highlight": "^2.x",
    "@tiptap/extension-link": "^2.x",
    "@tiptap/extension-placeholder": "^2.x",
    "dexie": "^4.0.0",
    "lucide-react": "^0.400.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "tailwind-merge": "^2.3.0"
  }
}
```
