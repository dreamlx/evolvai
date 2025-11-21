# Epic-006: Intelligent Memory System

## 状态

Draft - 待深入讨论

## 背景

### 现状

1. **上游 Serena Memories 已废弃**
   - 简单文件存储，缺乏独特价值
   - 已标记 deprecation warnings
   - 建议用 docs/ 替代

2. **之前的设计 (serena-intelligent-memory-redesign.md)**
   - 定位为"AI工具箱优化器"
   - 四大组件：工具偏好、环境偏好、编码规范、项目上下文
   - 需要结合新战略重新评估

3. **新的需求**
   - 知识图谱支持
   - RAG（检索增强生成）
   - 遗忘机制
   - 与 TPST 分析集成

### 战略定位

Memory 系统应该是 EvolvAI "更聪明使用工具" 战略的核心支撑：
- 不是通用知识存储
- 而是工具使用优化引擎

## 初步架构设想

```
┌─────────────────────────────────────────────────┐
│       EvolvAI Intelligent Memory System         │
├─────────────────────────────────────────────────┤
│                                                 │
│  Layer 3: 自适应学习 (Adaptive Learning)         │
│  • 遗忘机制 (时间衰减 + 重要性权重)               │
│  • TPST 模式学习                                │
│  • 约束自适应调整                                │
│                                                 │
│  Layer 2: 智能检索 (Knowledge Graph + RAG)      │
│  • 实体关系图谱 (项目结构、依赖)                  │
│  • 向量检索 (相似问题查找)                       │
│  • 语义搜索                                     │
│                                                 │
│  Layer 1: 基础存储 (Core Storage)               │
│  • 工具使用历史                                 │
│  • 环境偏好配置                                 │
│  • 约束配置                                     │
│  • 编码规范                                     │
│                                                 │
└─────────────────────────────────────────────────┘
```

## 待讨论问题

### 技术选型

1. **知识图谱**
   - Neo4j（重量级）
   - 简单 JSON Graph（轻量级）
   - NetworkX + JSON 持久化

2. **向量存储（RAG）**
   - ChromaDB
   - FAISS
   - 简单 numpy 实现

3. **遗忘算法**
   - 指数时间衰减
   - LRU 变体
   - 重要性加权

### 核心问题

1. **与 TPST 的集成方式**
   - Memory 是 TPST 的数据源？
   - 还是独立系统？

2. **与现有工具的关系**
   - 替代 Serena Memories？
   - 还是并行存在？

3. **存储位置**
   - 项目本地 (.serena/memory/)？
   - 用户全局 (~/.evolvai/memory/)？
   - 混合模式？

4. **隐私和安全**
   - 代码片段存储
   - 敏感信息过滤

## 预期 Features（待细化）

- Feature 6.1: 基础存储层重构
- Feature 6.2: 知识图谱集成
- Feature 6.3: RAG 检索实现
- Feature 6.4: 遗忘机制
- Feature 6.5: TPST 数据集成
- Feature 6.6: 迁移工具（从旧 Memories）

## 依赖

- Epic-005: 战略定位（已完成初步定义）
- Epic-001: TPST 分析（数据来源）

## 相关资源

- [之前的设计文档](../../../archive/upstream-legacy/serena-intelligent-memory-redesign.md)
- [Memory 反思文档](../../../archive/upstream-legacy/memory-reflection-and-redesign.md)

---

**创建日期**: 2024-11-21
**状态**: Draft - 待深入讨论
**Owner**: TBD

**注意**: 此 Epic 需要专门的讨论会议来确定技术选型和详细设计。
