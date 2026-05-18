# 上下文管理加强计划

## 背景

项目已有一套上下文管理系统，位于 `agent_framework/deepseek_optimization/context/` 目录下，包含：

- **MegaContextManager**: 100万上下文管理器
- **ContextCompressor**: AI驱动的上下文压缩器
- **MessageRanker**: 多维度消息重要性评估器
- **StructuredStorageEngine**: 结构化本地存储引擎
- **WindowManager**: 上下文窗口管理器
- **ContextFeedbackGenerator**: 上下文反馈生成器

## 现有问题分析

通过代码审查发现以下可改进点：

### 1. Token估算精度不足
- 当前使用简单的 `content_len // 4` 估算
- 未考虑不同语言的token密度差异
- 未考虑特殊token（代码块、链接等）

### 2. 缺乏跨会话上下文管理
- 当前上下文仅在单次会话内有效
- 无法恢复历史会话的上下文状态
- 缺少会话级别的上下文持久化

### 3. 压缩策略单一
- 仅支持"保留最后N条 + AI摘要早期消息"
- 未实现分层压缩策略
- 缺少渐进式压缩机制

### 4. 检索能力有限
- 仅支持关键词搜索
- 未利用向量嵌入进行语义检索
- 缺少时间范围、重要性等多条件检索

### 5. 缺少上下文预热机制
- 每次会话从零开始构建上下文
- 无法预加载相关历史上下文
- 缺少上下文缓存机制

### 6. 缺少上下文版本控制
- 无法回滚到之前的上下文状态
- 缺少上下文变更历史记录

## 实施计划

### Phase 1: 精确Token估算 (优先级: 高)

**目标**: 提高token估算精度，减少上下文溢出风险

**步骤**:
1. 创建 `token_estimator.py` - 精确Token估算器
   - 集成 tiktoken 库进行精确计算
   - 支持不同编码方案 (cl100k_base, p50k_base等)
   - 处理特殊内容类型（代码、Markdown、多语言文本）
   
2. 更新 `mega_context_manager.py`
   - 替换简单估算为精确估算
   - 添加token预算管理功能

3. 添加配置选项
   - 支持配置估算精度级别（快速/精确）
   - 支持配置不同模型的token限制

**文件变更**:
- 新建: `agent_framework/deepseek_optimization/context/token_estimator.py`
- 修改: `agent_framework/deepseek_optimization/context/mega_context_manager.py`
- 修改: `agent_framework/deepseek_optimization/context/__init__.py`

### Phase 2: 跨会话上下文管理 (优先级: 高)

**目标**: 支持跨会话的上下文持久化和恢复

**步骤**:
1. 创建 `session_manager.py` - 会话管理器
   - 会话创建、保存、加载、删除
   - 会话元数据管理（创建时间、最后活动、消息数等）
   - 会话搜索和列表

2. 创建 `context_snapshot.py` - 上下文快照
   - 保存完整的上下文状态
   - 支持增量快照
   - 快照压缩存储

3. 更新 `mega_context_manager.py`
   - 添加会话ID绑定
   - 支持从快照恢复
   - 自动保存机制

**文件变更**:
- 新建: `agent_framework/deepseek_optimization/context/session_manager.py`
- 新建: `agent_framework/deepseek_optimization/context/context_snapshot.py`
- 修改: `agent_framework/deepseek_optimization/context/mega_context_manager.py`

### Phase 3: 分层压缩策略 (优先级: 中)

**目标**: 实现更智能的多层次压缩策略

**步骤**:
1. 创建 `compression_strategy.py` - 压缩策略模块
   - 定义压缩策略接口
   - 实现多种策略：
     - `TailPreserveStrategy`: 保留尾部消息
     - `ImportanceBasedStrategy`: 基于重要性压缩
     - `SemanticClusterStrategy`: 语义聚类压缩
     - `HybridStrategy`: 混合策略

2. 更新 `context_compressor.py`
   - 支持策略选择和切换
   - 实现渐进式压缩
   - 添加压缩质量评估

3. 创建 `compression_analyzer.py` - 压缩分析器
   - 分析压缩效果
   - 生成压缩报告
   - 优化建议

**文件变更**:
- 新建: `agent_framework/deepseek_optimization/context/compression_strategy.py`
- 新建: `agent_framework/deepseek_optimization/context/compression_analyzer.py`
- 修改: `agent_framework/deepseek_optimization/context/context_compressor.py`

### Phase 4: 语义检索增强 (优先级: 中)

**目标**: 利用向量嵌入实现语义检索

**步骤**:
1. 创建 `semantic_retriever.py` - 语义检索器
   - 集成向量嵌入模型
   - 实现相似度搜索
   - 支持混合检索（关键词+语义）

2. 更新 `storage_engine.py`
   - 添加向量索引
   - 支持向量存储
   - 多条件检索API

3. 创建 `context_indexer.py` - 上下文索引器
   - 增量索引更新
   - 索引优化
   - 索引统计

**文件变更**:
- 新建: `agent_framework/deepseek_optimization/context/semantic_retriever.py`
- 新建: `agent_framework/deepseek_optimization/context/context_indexer.py`
- 修改: `agent_framework/deepseek_optimization/context/storage_engine.py`

### Phase 5: 上下文预热与缓存 (优先级: 中)

**目标**: 减少冷启动时间，提高响应速度

**步骤**:
1. 创建 `context_cache.py` - 上下文缓存
   - LRU缓存实现
   - 缓存预热
   - 缓存失效策略

2. 创建 `context_preloader.py` - 上下文预加载器
   - 基于用户历史预测预加载内容
   - 基于时间模式预加载
   - 智能预加载策略

3. 更新 `mega_context_manager.py`
   - 集成缓存层
   - 支持预加载触发

**文件变更**:
- 新建: `agent_framework/deepseek_optimization/context/context_cache.py`
- 新建: `agent_framework/deepseek_optimization/context/context_preloader.py`
- 修改: `agent_framework/deepseek_optimization/context/mega_context_manager.py`

### Phase 6: 上下文版本控制 (优先级: 低)

**目标**: 支持上下文状态回滚和历史追踪

**步骤**:
1. 创建 `context_versioning.py` - 上下文版本控制
   - 版本创建和存储
   - 版本回滚
   - 版本差异计算
   - 版本合并

2. 创建 `change_history.py` - 变更历史
   - 记录所有上下文变更
   - 变更可视化
   - 变更搜索

**文件变更**:
- 新建: `agent_framework/deepseek_optimization/context/context_versioning.py`
- 新建: `agent_framework/deepseek_optimization/context/change_history.py`

### Phase 7: 配置与监控 (优先级: 中)

**目标**: 提供灵活配置和完善的监控能力

**步骤**:
1. 创建 `context_config.py` - 上下文配置
   - 集中管理所有配置项
   - 支持动态配置更新
   - 配置验证

2. 创建 `context_monitor.py` - 上下文监控
   - 性能指标收集
   - 健康检查
   - 告警机制

3. 更新配置文件
   - 添加上下文管理相关配置
   - 支持环境变量覆盖

**文件变更**:
- 新建: `agent_framework/deepseek_optimization/context/context_config.py`
- 新建: `agent_framework/deepseek_optimization/context/context_monitor.py`
- 修改: `agent_framework/configs/models.yaml` (或创建新的配置文件)

### Phase 8: 测试与文档 (优先级: 高)

**目标**: 确保代码质量和可维护性

**步骤**:
1. 编写单元测试
   - 为所有新模块编写测试
   - 提高现有测试覆盖率

2. 编写集成测试
   - 端到端场景测试
   - 性能基准测试

3. 更新文档
   - API文档
   - 使用示例
   - 架构说明

**文件变更**:
- 新建: `tests/test_context_management.py`
- 新建: `tests/test_token_estimator.py`
- 新建: `tests/test_session_manager.py`
- 修改: `examples/deepseek_comprehensive.py`

## 实施顺序

```
Phase 1 (Token估算) ──┬──> Phase 2 (跨会话管理)
                      │
                      ├──> Phase 3 (压缩策略)
                      │
                      └──> Phase 4 (语义检索)
                                 │
                                 v
                      Phase 5 (预热缓存) ──> Phase 6 (版本控制)
                                 │
                                 v
                      Phase 7 (配置监控) ──> Phase 8 (测试文档)
```

## 预期收益

1. **Token精度提升**: 减少90%以上的上下文溢出错误
2. **会话恢复**: 支持历史会话无缝恢复，提升用户体验
3. **压缩效率**: 压缩比提升30-50%，保留更多关键信息
4. **检索速度**: 语义检索响应时间<100ms
5. **冷启动优化**: 预热后首响时间减少50%
6. **可维护性**: 完善的版本控制和监控能力

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| tiktoken依赖增加 | 部署复杂度 | 提供降级方案，使用估算模式 |
| 向量存储空间增长 | 存储成本 | 实现增量索引和定期清理 |
| 预热资源消耗 | 内存压力 | 可配置预热策略和资源限制 |
| 版本存储膨胀 | 磁盘空间 | 自动压缩和过期清理 |

## 注意事项

1. 所有新功能需要保持向后兼容
2. 配置项需要有合理的默认值
3. 关键操作需要记录日志
4. 大文件操作需要异步处理
5. 需要考虑多进程/分布式场景
