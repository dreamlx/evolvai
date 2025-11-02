# [IN_PROGRESS] Feature 001: ExecutionPlan Schema

**Feature ID**: FEATURE-001
**Epic**: EPIC-001 - 行为约束系统
**创建日期**: 2025-10-26
**负责人**: EvolvAI Team
**状态**: [IN_PROGRESS]
**优先级**: [P0]
**估算**: 2人天

---

## 📋 功能概述

### 功能描述
实现ExecutionPlan Pydantic模型作为所有工具操作的"宪法"。通过JSON Schema的强制验证，确保AI助手在调用工具时必须提供dry_run、validation、rollback等关键信息，从接口层面删除"盲目执行"的可能性。

### 业务价值
- **从接口删除风险路径**: AI无法绕过验证直接执行危险操作
- **提高首次成功率**: 强制dry_run预览，减少盲目尝试
- **可回滚性**: 所有操作都有rollback plan，降低错误成本
- **Token效率**: 减少因错误重试导致的token浪费

### 目标用户
- MCP工具开发者：使用ExecutionPlan包装工具调用
- AI助手：必须按ExecutionPlan schema构造工具调用

---

## 🎯 功能目标

### 主要目标
实现完整的ExecutionPlan Pydantic模型，包含：
1. **强制字段**: dry_run, validation, rollback, limits, batch
2. **类型验证**: 使用Pydantic validators确保数据合法性
3. **序列化支持**: JSON Schema导出用于MCP工具定义

### 次要目标
- 提供易用的builder模式API
- 生成清晰的错误提示信息
- 建立测试套件验证schema行为

---

## 📦 包含的Stories

### Story 1: 定义ExecutionPlan核心Schema
- **Story ID**: STORY-001
- **用户故事**: 作为MCP工具开发者，我希望有一个标准的ExecutionPlan schema，以便统一约束所有工具的执行行为
- **估算**: 5SP
- **状态**: [In Progress]
- **验收标准**:
  - [ ] ExecutionPlan基类定义完成（dry_run, validation, rollback字段）
  - [ ] 使用Pydantic Field定义必填字段和默认值
  - [ ] 所有字段有清晰的docstring说明

### Story 2: 实现Validation机制
- **Story ID**: STORY-002
- **用户故事**: 作为MCP工具开发者，我希望ExecutionPlan能自动验证字段合法性，以便在工具调用前就发现错误
- **估算**: 3SP
- **状态**: [Backlog]
- **验收标准**:
  - [ ] limits字段验证（max_files, max_changes, timeout）
  - [ ] validation字段验证（pre_conditions, expected_outcomes）
  - [ ] rollback字段验证（strategy, commands）

### Story 3: JSON Schema导出
- **Story ID**: STORY-003
- **用户故事**: 作为MCP服务开发者，我希望能导出ExecutionPlan的JSON Schema，以便在MCP工具定义中使用
- **估算**: 2SP
- **状态**: [Backlog]
- **验收标准**:
  - [ ] 支持model_json_schema()导出
  - [ ] 导出的schema包含所有字段说明
  - [ ] 与MCP协议格式兼容

---

## ✅ 验收标准

### 功能验收标准
- [ ] ExecutionPlan model定义完整，包含所有必需字段
- [ ] Pydantic验证器覆盖所有字段
- [ ] JSON Schema导出正确且完整
- [ ] 文档字符串完整清晰

### 性能验收标准
- [ ] Schema验证耗时<10ms
- [ ] JSON序列化耗时<5ms

### 质量验收标准
- [ ] 测试覆盖率≥95%
- [ ] Mypy类型检查通过
- [ ] 所有字段有docstring

---

## 🔧 技术要点

### 技术栈
- Python 3.11
- Pydantic 2.x
- typing for type hints

### 架构设计
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal

class ExecutionLimits(BaseModel):
    """执行限制配置"""
    max_files: int = Field(default=10, ge=1, le=100)
    max_changes: int = Field(default=50, ge=1, le=1000)
    timeout_seconds: int = Field(default=30, ge=1, le=300)

class ValidationConfig(BaseModel):
    """验证配置"""
    pre_conditions: List[str] = Field(default_factory=list)
    expected_outcomes: List[str] = Field(default_factory=list)

class RollbackStrategy(BaseModel):
    """回滚策略"""
    strategy: Literal["git_revert", "file_backup", "manual"]
    commands: List[str] = Field(default_factory=list)

class ExecutionPlan(BaseModel):
    """执行计划宪法"""
    dry_run: bool = Field(
        default=True,
        description="是否先预览而不实际执行"
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="验证配置"
    )
    rollback: RollbackStrategy = Field(
        ...,  # 必需字段
        description="回滚策略，必须提供"
    )
    limits: ExecutionLimits = Field(
        default_factory=ExecutionLimits,
        description="执行限制"
    )
    batch: bool = Field(
        default=False,
        description="是否批量执行"
    )
```

### 技术难点
- **字段验证平衡**: 既要严格验证，又要保持易用性
  - 解决方案：提供合理默认值，只对关键字段强制要求
- **向后兼容**: schema演进时保持兼容
  - 解决方案：使用Optional字段，严格的版本管理

### API设计
```python
# 基础用法
plan = ExecutionPlan(
    rollback=RollbackStrategy(strategy="git_revert")
)

# Builder模式
plan = (
    ExecutionPlan.builder()
    .with_dry_run(True)
    .with_timeout(60)
    .with_rollback("git_revert")
    .build()
)

# JSON Schema导出
schema = ExecutionPlan.model_json_schema()
```

---

## 🔗 依赖关系

### 依赖的Feature
无 - 这是Epic-001的第一个Feature

### 被依赖的Feature
- FEATURE-002: safe_search - 需要使用ExecutionPlan
- FEATURE-003: safe_edit - 需要使用ExecutionPlan
- FEATURE-004: safe_exec - 需要使用ExecutionPlan

### 外部依赖
- Pydantic 2.x - 核心依赖
- Python 3.11+ - 类型提示支持

---

## 📊 时间线

### 预计时间
- **开始日期**: 2025-10-27
- **结束日期**: 2025-10-28
- **总工作量**: 2人天

### 里程碑
- [ ] Story-001完成：核心schema定义 - 2025-10-27 14:00
- [ ] Story-002完成：验证机制 - 2025-10-27 18:00
- [ ] Story-003完成：JSON Schema导出 - 2025-10-28 12:00
- [ ] 测试套件完成 - 2025-10-28 16:00

---

## 🛡️ 风险与对策

### 技术风险
| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| Pydantic版本不兼容 | Medium | Low | 锁定Pydantic 2.x版本 | Team |
| 验证规则过于严格 | High | Medium | 提供escape hatch，允许高级用户绕过 | Team |

### 进度风险
| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| 测试覆盖不足 | Medium | Low | TDD开发，测试先行 | Team |

---

## 🧪 测试策略

### 测试范围
- ExecutionPlan所有字段的验证逻辑
- JSON Schema导出的正确性
- 边界条件和错误处理

### 测试类型
- [x] 单元测试 - 每个validator独立测试
- [x] 集成测试 - 完整schema的序列化/反序列化
- [ ] 性能测试 - 验证和序列化性能
- [ ] 文档测试 - docstring示例可运行

### 测试覆盖率目标
- 核心模块: 95%
- 整体: 90%

---

## 📝 实现备注

### 设计决策
1. **为什么rollback是必需字段？**
   - 强制AI思考回滚策略，避免"执行后再说"的模式
   - 降低错误操作的风险成本

2. **为什么dry_run默认为True？**
   - 安全优先：默认预览，需要明确确认才实际执行
   - 减少盲目执行导致的token浪费

3. **为什么limits有默认值？**
   - 平衡安全和易用性
   - 合理默认值覆盖大部分场景

---

## 📚 相关文档

- [Epic 001](./README.md)
- [Story 001](./story-001-execution-plan-schema.md)
- [Story 002](./story-002-validation-logic.md)
- [ADR-001: 为什么选择Pydantic](../../../development/architecture/adrs/001-pydantic-for-schemas.md)

---

**最后更新**: 2025-10-26
**更新人**: EvolvAI Team
