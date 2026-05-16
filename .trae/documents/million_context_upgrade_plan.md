# 100万上下文升级与智能本地存储系统 - 技术实施计划

## 1. 需求分析与现状总结

### 1.1 核心变更
- **上下文容量提升**：从128K升级到 **100万 tokens**
- **智能存储机制**：重要内容保留在上下文，非重要内容本地结构化存储
- **实时反馈机制**：在对话中明确指示细枝末节内容的存储位置

### 1.2 现有代码基础
- 已有 `WindowManager` 和 `ContextCompressor` 模块
- 现有窗口管理使用简单的LRU策略
- 压缩仅采用简单摘要方式

---

## 2. 系统架构调整

### 2.1 新架构层次
```
┌─────────────────────────────────────────────────────────────────────────┐
│                    100万上下文管理系统 (MegaContextSystem)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  活跃上下文窗口 (Active Context)  - 200K-800K 可调               │  │
│  │  → 系统消息、最近对话、重要主题、高价值内容                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  结构化本地存储 (Structured Local Storage)                       │  │
│  │  → 对话片段、按主题分类、元数据索引、文件持久化                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  智能重要性评估器 (Intelligent Importance Evaluator)             │  │
│  │  → 语义重要性评分、主题识别、价值判断、衰减机制                    │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  上下文反馈系统 (Context Feedback System)                        │  │
│  │  → 存储位置指示、引用格式、文件信息、可检索提示                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流设计
```
用户消息 → 重要性评估 → [重要→存入活跃窗口]
                     → [非重要→结构化本地存储]
                     → 生成上下文反馈标记
                     → 组装完整对话上下文 → DeepSeek API
```

---

## 3. 核心模块设计

### 3.1 需要新建的文件

#### 文件1: `context/message_ranker.py`
- **职责**：消息重要性评估器
- **功能**：
  - 多维度评分（语义重要性、时间衰减、用户标记、主题相关性）
  - 重要性分类（CRITICAL, IMPORTANT, NORMAL, LOW, TRIVIAL）
  - 可配置权重系统

#### 文件2: `context/storage_engine.py`
- **职责**：结构化本地存储引擎
- **功能**：
  - 按主题/时间/重要性分类存储
  - JSONL/Parquet文件格式
  - 索引和快速检索
  - 存储反馈标记生成

#### 文件3: `context/mega_context_manager.py`
- **职责**：100万上下文主管理器
- **功能**：
  - 协调活跃窗口和本地存储
  - 实时调整策略
  - 完整上下文反馈生成

#### 文件4: `context/feedback_generator.py`
- **职责**：上下文反馈生成器
- **功能**：
  - 生成结构化的存储位置指示
  - 文件引用格式化
  - 可检索提示生成

### 3.2 需要修改的文件

1. **`context/window_manager.py`** - 最大容量升级到100万，新增重要性感知策略
2. **`context/context_compressor.py`** - 升级为智能压缩而非简单摘要
3. **`llm/model_config.py`** - 更新 `DEEPSEEK_CONTEXT_WINDOWS` 到100万
4. **`deepseek_optimization/__init__.py`** - 导出新模块

---

## 4. 数据结构设计

### 4.1 消息重要性评分
```python
@dataclass
class MessageImportance:
    score: float  # 0.0-1.0
    category: ImportanceCategory  # CRITICAL/IMPORTANT/NORMAL/LOW/TRIVIAL
    reasoning: str
    topics: List[str]
    timestamp: datetime
    decay_rate: float = 0.01
```

### 4.2 结构化存储条目
```python
@dataclass
class StoredMessage:
    id: str
    original_message: Dict[str, Any]
    importance: MessageImportance
    storage_path: Path
    storage_topic: str
    archived_at: datetime
    retrieval_key: str
```

### 4.3 上下文反馈标记
```python
@dataclass
class ContextFeedback:
    total_messages: int
    in_context_count: int
    archived_count: int
    archived_files: List[Path]
    topic_index: Dict[str, int]
    summary: str
    insertion_point: str
```

---

## 5. 本地存储方案

### 5.1 存储结构
```
data/
└── context_archive/
    ├── 2025-05-14/
    │   ├── topic_programming.jsonl
    │   ├── topic_business.jsonl
    │   └── general_archive.jsonl
    ├── index.json
    └── metadata.json
```

### 5.2 文件格式
- **JSONL**：可读性好，易于调试
- **索引系统**：快速定位消息
- **元数据**：统计信息、时间范围、主题分类

---

## 6. 实施步骤

### 阶段1：基础升级（1小时）
- 更新 `model_config.py` 中的上下文窗口到100万
- 修改现有模块的硬编码限制
- 配置参数调整

### 阶段2：重要性评估器（2小时）
- 创建 `message_ranker.py`
- 实现多维度评分算法
- 测试和校准

### 阶段3：结构化存储引擎（2.5小时）
- 创建 `storage_engine.py`
- 实现文件管理系统
- 索引和检索机制

### 阶段4：100万上下文管理器（3小时）
- 创建 `mega_context_manager.py`
- 实现核心协调逻辑
- 集成现有组件

### 阶段5：反馈系统（1.5小时）
- 创建 `feedback_generator.py`
- 实现存储位置指示
- 格式化输出

### 阶段6：集成与测试（2小时）
- 完整集成
- 端到端测试
- 性能优化

---

## 7. 成功标准

1. ✅ 上下文容量正常工作在100万
2. ✅ 重要消息自动识别并保留
3. ✅ 非重要消息自动本地结构化存储
4. ✅ 对话中明确显示存储位置指示
5. ✅ 系统响应速度无明显下降
6. ✅ 存储文件结构清晰可检索

---

## 8. 潜在风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 存储文件过大 | 中 | 自动分片和归档策略 |
| 重要性误判 | 高 | 用户反馈机制，可手动调整 |
| 性能下降 | 中 | 异步存储，索引优化 |
