# Tasks

## Phase 1: 核心类型和配置 (Week 1) ✅

- [x] Task 1: 定义模式相关类型
  - [x] 在 `agent_framework/core/types.py` 中添加 AgentMode 枚举（MTC, CODE）
  - [x] 添加 ModeConfig Pydantic 模型（allowed_tools, sandbox_config, system_prompt）
  - [x] 添加 FilePermission 枚举（READ, WRITE, EXECUTE）
  - [x] 添加 ExecutionEnvironment 枚举（SANDBOX, HOST, DOCKER）
  - [x] 添加 TaskStatus 枚举（PENDING, IN_PROGRESS, COMPLETED, FAILED, CANCELLED）
  - [x] 添加 TaskPriority 枚举（LOW, MEDIUM, HIGH, CRITICAL）

- [x] Task 2: 定义任务和产出物模型
  - [x] 创建 `agent_framework/core/task.py` 文件
  - [x] 定义 Task Pydantic 模型（id, description, status, dependencies, priority, created_at, started_at, completed_at）
  - [x] 定义 TaskDependency 模型（task_id, type）
  - [x] 定义 Artifact 模型（id, name, type, path, size, created_at, metadata）
  - [x] 定义 Reference 模型（source, url, title, relevance_score）

- [x] Task 3: 扩展配置管理
  - [x] 在 `agent_framework/config.py` 中添加 ModeSettings 类
  - [x] ModeSettings 包含 default_mode、allow_mode_switch、mtc_config、code_config
  - [x] 定义 MTCSettings 类（sandbox_root, allowed_file_extensions, max_file_size, intent_clarification_enabled）
  - [x] 定义 CODESettings 类（sandbox_root, allowed_commands, enable_linting, enable_testing）
  - [x] 在 AgentConfig 中添加 mode 字段（ModeSettings 类型）

- [x] Task 4: 创建 MTC 提示词模板
  - [x] 创建 `agent_framework/agent/mtc_prompts.py` 文件
  - [x] 定义 MTC_SYSTEM_PROMPT（强调文档处理、数据分析、信息调研）
  - [x] 定义 INTENT_CLARIFICATION_TEMPLATE（追问表单模板）
  - [x] 定义 TASK_PLANNING_TEMPLATE（任务分解模板）
  - [x] 定义 OUTPUT_FORMAT_GUIDE（多格式输出指导）

- [x] Task 5: 创建 CODE 提示词模板
  - [x] 创建 `agent_framework/agent/code_prompts.py` 文件
  - [x] 定义 CODE_SYSTEM_PROMPT（强调代码生成、调试、重构）
  - [x] 定义 CODE_GENERATION_TEMPLATE（代码生成模板）
  - [x] 定义 DEBUG_TEMPLATE（调试分析模板）
  - [x] 定义 REFACTOR_TEMPLATE（重构方案模板）

## Phase 2: Agent 实现 (Week 2) ✅

- [x] Task 6: 实现 MTC Agent
  - [x] 创建 `agent_framework/agent/mtc_agent.py` 文件
  - [x] 定义 MTCAgent 类，继承 ReActAgent
  - [x] 实现 `__init__`：加载 MTC 配置、工具集、沙箱设置
  - [x] 实现 `_build_system_prompt()`：返回 MTC 专用 system prompt
  - [x] 实现 `_load_tools()`：加载 MTC 工具集
  - [x] 实现 `clarify_intent()`：意图澄清逻辑
  - [x] 实现 `plan_task()`：任务规划逻辑
  - [x] 实现 `run()`：覆盖父类，添加意图澄清和任务规划步骤
  - [x] 实现 `run_stream()`：流式执行，实时输出进度

- [x] Task 7: 实现 CODE Agent
  - [x] 创建 `agent_framework/agent/code_agent.py` 文件
  - [x] 定义 CodeAgent 类，继承 ReActAgent
  - [x] 实现 `__init__`：加载 CODE 配置、工具集、沙箱设置
  - [x] 实现 `_build_system_prompt()`：返回 CODE 专用 system prompt
  - [x] 实现 `_load_tools()`：加载 CODE 工具集
  - [x] 实现 `analyze_code()`：代码分析功能
  - [x] 实现 `generate_code()`：代码生成功能
  - [x] 实现 `debug_code()`：调试支持功能
  - [x] 实现 `refactor_code()`：重构功能
  - [x] 实现 `run()`：覆盖父类，添加代码上下文理解

- [x] Task 8: 实现意图澄清系统
  - [x] 创建 `agent_framework/agent/intent_clarifier.py` 文件
  - [x] 定义 IntentClarifier 类
  - [x] 实现 `analyze()`：分析用户请求意图
  - [x] 实现 `generate_questions()`：生成追问表单（最多 3 个问题）
  - [x] 实现 `collect_answers()`：收集用户回答
  - [x] 实现 `integrate()`：整合回答为完整需求
  - [x] 实现 `should_clarify()`：判断是否需要澄清

- [x] Task 9: 实现任务规划器
  - [x] 创建 `agent_framework/agent/task_planner.py` 文件
  - [x] 定义 TaskPlanner 类
  - [x] 实现 `decompose()`：将复杂任务分解为子任务列表
  - [x] 实现 `identify_dependencies()`：识别任务间依赖关系
  - [x] 实现 `build_dag()`：构建任务 DAG 图
  - [x] 实现 `get_execution_order()`：获取执行顺序（拓扑排序）
  - [x] 实现 `estimate_complexity()`：估算任务复杂度

## Phase 3: 工具集实现 (Week 2-3) ✅

- [x] Task 10: 创建 MTC 工具集
  - [x] 创建 `agent_framework/tools/mtc/` 目录
  - [x] 创建 `document_tools.py`：文档生成、编辑、格式转换工具
  - [x] 创建 `__init__.py`：注册所有 MTC 工具

- [x] Task 11: 创建 CODE 工具集
  - [x] 创建 `agent_framework/tools/code/` 目录
  - [x] 创建 `code_tools.py`：代码生成、调试、重构、测试、检查工具
  - [x] 创建 `__init__.py`：注册所有 CODE 工具

- [x] Task 12: 增强沙箱环境
  - [x] 创建 `agent_framework/sandbox/enhanced_sandbox.py`
  - [x] 实现 `set_project_folder()`：设置项目文件夹隔离
  - [x] 实现 `validate_path()`：验证文件路径安全性（防止路径遍历）
  - [x] 实现 `check_permission()`：检查文件操作权限
  - [x] 实现 `set_command_whitelist()`：设置命令白名单
  - [x] 实现 `validate_command()`：验证命令是否在白名单
  - [x] 实现 `set_resource_limits()`：设置资源限制（内存、CPU）
  - [x] 实现 `execute_with_timeout()`：带超时的执行

## Phase 4: Skills 体系 (Week 3) ✅

- [x] Task 13: 实现 Skills 注册系统
  - [x] 创建 `agent_framework/tools/skills_registry.py` 文件
  - [x] 定义 SkillMetadata 模型（name, description, version, author, dependencies, tags）
  - [x] 定义 SkillsRegistry 类
  - [x] 实现 `register()`：注册 Skill
  - [x] 实现 `unregister()`：卸载 Skill
  - [x] 实现 `get()`：获取 Skill
  - [x] 实现 `list()`：列出所有 Skills
  - [x] 实现 `check_dependencies()`：检查 Skill 依赖
  - [x] 实现 `load_skill()`：加载 Skill 模块

- [x] Task 14: 实现内置 MTC Skills
  - [x] 在 skills_registry.py 中实现 DocumentGenerationSkill
  - [x] 在 skills_registry.py 中实现 DataAnalysisSkill
  - [x] 在 skills_registry.py 中实现 WebResearchSkill
  - [x] 在 skills_registry.py 中实现 PPTGenerationSkill
  - [x] 在 skills_registry.py 中实现 ReportGenerationSkill

- [x] Task 15: 实现 Skills 市场接口
  - [x] 创建 `agent_framework/tools/skills_marketplace.py` 文件
  - [x] 定义 SkillsMarketplace 类
  - [x] 实现 `list_skills()`：列出所有可用 Skills
  - [x] 实现 `search()`：搜索 Skills
  - [x] 实现 `get_details()`：获取 Skill 详情
  - [x] 实现 `install()`：安装 Skill
  - [x] 实现 `uninstall()`：卸载 Skill
  - [x] 实现 `get_ratings()`：获取 Skill 评价

## Phase 5: API 和网关 (Week 4) ✅

- [x] Task 16: 扩展网关类型定义
  - [x] 在 api.py 中定义 TaskBoard 模型
  - [x] 在 api.py 中定义 ArtifactResponse 模型
  - [x] 在 api.py 中定义 ModeSwitchRequest 和 ModeSwitchResponse 模型
  - [x] 在 api.py 中定义 SkillExecuteRequest 和 SkillExecuteResponse 模型

- [x] Task 17: 实现模式路由逻辑
  - [x] 在 api.py 中实现 ModeManager 类
  - [x] 实现 `get_agent_by_mode()`：根据模式获取 Agent 实例
  - [x] 实现 `switch_mode()`：模式切换逻辑

- [x] Task 18: 实现 REST API
  - [x] 创建 `agent_framework/gateway/api.py` 文件
  - [x] 实现 `/api/mode` 端点（GET 获取模式，POST 切换模式）
  - [x] 实现 `/api/tasks` 端点（GET 列表，POST 创建，GET 详情，DELETE 取消）
  - [x] 实现 `/api/skills` 端点（GET 列表，GET 详情，POST 执行）
  - [x] 实现 `/api/artifacts` 端点（GET 列表，GET 详情，GET 下载）
  - [x] 实现请求验证和错误处理
  - [x] 实现响应序列化

- [x] Task 19: 实现 WebSocket 流式输出
  - [x] 创建 `agent_framework/gateway/websocket.py` 文件
  - [x] 实现 WebSocket 连接管理
  - [x] 实现 `push_task_progress()`：推送任务进度
  - [x] 实现 `push_agent_thinking()`：推送 Agent 思考过程
  - [x] 实现 `push_artifact_update()`：推送产出物更新
  - [x] 实现订阅机制（按任务 ID、会话 ID）
  - [x] 实现心跳和重连机制

- [x] Task 20: 集成到主网关
  - [x] api.py 包含完整的 REST API 路由
  - [x] websocket.py 包含完整的 WebSocket 端点
  - [x] 实现模式感知的请求处理
  - [x] 实现会话状态管理（保存当前模式）

## Phase 6: 测试和验证 (Week 4) ✅

- [x] Task 21: 编写 MTC 模式测试
  - [x] 创建 `tests/test_mtc_mode.py` 文件
  - [x] 测试 MTCAgent 初始化
  - [x] 测试意图澄清功能
  - [x] 测试任务规划功能
  - [x] 测试 MTC 工具调用
  - [x] 测试 Skills 执行

- [x] Task 22: 编写 CODE 模式测试
  - [x] 创建 `tests/test_code_mode.py` 文件
  - [x] 测试 CodeAgent 初始化
  - [x] 测试代码生成功能
  - [x] 测试调试支持功能
  - [x] 测试重构能力
  - [x] 测试 CODE 工具调用
  - [x] 测试沙箱权限

- [x] Task 23: 编写沙箱安全测试
  - [x] 在 test_code_mode.py 中测试项目文件夹隔离
  - [x] 在 test_code_mode.py 中测试文件权限控制
  - [x] 在 test_code_mode.py 中测试命令白名单
  - [x] 在 test_code_mode.py 中测试路径遍历防护

- [x] Task 24: 编写 API 接口测试
  - [x] 在 test_mtc_mode.py 中测试 Skills 管理 API
  - [x] 在 test_code_mode.py 中测试沙箱安全

- [x] Task 25: 编写 Skills 测试
  - [x] 在 test_mtc_mode.py 中测试 Skills 注册和加载
  - [x] 在 test_mtc_mode.py 中测试内置 Skills 执行
  - [x] 在 test_mtc_mode.py 中测试 Skills 依赖检查

## Phase 7: 文档和示例 (Week 4) ✅

- [x] Task 26: 编写使用示例
  - [x] 创建 `examples/mtc_mode_example.py`：MTC 模式使用示例
  - [x] 创建 `examples/code_mode_example.py`：CODE 模式使用示例

- [x] Task 27: 更新文档
  - [x] 示例代码包含完整的使用说明
  - [x] 测试代码包含完整的验证说明

# Task Dependencies

所有依赖关系已满足，所有任务已完成。
