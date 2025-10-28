# [IN_PROGRESS] Story 001: 定义ExecutionPlan核心Schema

**Story ID**: STORY-001
**Epic**: EPIC-001 - 行为约束系统
**Feature**: FEATURE-001 - ExecutionPlan Schema
**创建日期**: 2025-10-26
**负责人**: EvolvAI Team
**状态**: [IN_PROGRESS]
**优先级**: [P0]
**估算**: 5 Story Points

---

## 👤 用户故事

作为 **MCP工具开发者**，
我希望 **有一个标准的ExecutionPlan schema定义**，
以便 **统一约束所有工具的执行行为，从接口层面删除危险执行路径**。

---

## ✅ 验收标准

### 功能验收标准
- [ ] ExecutionPlan基类定义完成，包含以下字段：
  - [ ] `dry_run: bool` - 默认True
  - [ ] `validation: ValidationConfig` - 包含pre_conditions和expected_outcomes
  - [ ] `rollback: RollbackStrategy` - 必需字段，无默认值
  - [ ] `limits: ExecutionLimits` - 默认合理限制（10文件，50修改，30秒）
  - [ ] `batch: bool` - 默认False
- [ ] 所有字段使用Pydantic Field定义，包含description
- [ ] 每个字段有清晰的docstring说明用途

### 性能验证标准
- [ ] Schema实例化耗时<1ms
- [ ] 字段验证耗时<10ms

### 质量验证标准
- [ ] Mypy类型检查通过，无类型错误
- [ ] 测试覆盖率≥95%
- [ ] 所有公开API有docstring

---

## 📋 技术任务分解

### Task 1: 定义基础数据类型
- **Task ID**: TASK-001.1
- **描述**: 定义ExecutionLimits, ValidationConfig, RollbackStrategy辅助类
- **估算**: 2小时
- **状态**: [TODO]
- **负责人**: Dev Team

### Task 2: 实现ExecutionPlan主类
- **Task ID**: TASK-001.2
- **描述**: 实现ExecutionPlan主类，整合所有字段和验证逻辑
- **估算**: 3小时
- **状态**: [TODO]
- **负责人**: Dev Team

### Task 3: 编写单元测试
- **Task ID**: TASK-001.3
- **描述**: 覆盖所有字段的验证逻辑，包括边界条件和错误情况
- **估算**: 3小时
- **状态**: [TODO]
- **负责人**: Dev Team

---

## 🧪 测试用例

### 测试用例1: 默认值验证
```python
def test_execution_plan_defaults():
    """测试ExecutionPlan的默认值行为"""
    # Given: 只提供必需的rollback字段
    plan = ExecutionPlan(
        rollback=RollbackStrategy(strategy="git_revert")
    )

    # Then: 其他字段应该有合理的默认值
    assert plan.dry_run is True
    assert plan.batch is False
    assert plan.limits.max_files == 10
    assert plan.limits.max_changes == 50
    assert plan.limits.timeout_seconds == 30
```

### 测试用例2: 必需字段验证
```python
def test_execution_plan_requires_rollback():
    """测试rollback字段是必需的"""
    # Given: 不提供rollback字段
    # When: 尝试创建ExecutionPlan
    # Then: 应该抛出ValidationError
    with pytest.raises(ValidationError) as exc_info:
        ExecutionPlan()

    assert "rollback" in str(exc_info.value)
```

### 测试用例3: 字段边界验证
```python
def test_execution_limits_boundaries():
    """测试ExecutionLimits的边界验证"""
    # Given: 提供超出范围的值
    # When: 尝试创建ExecutionLimits
    # Then: 应该抛出ValidationError

    # max_files不能为0
    with pytest.raises(ValidationError):
        ExecutionLimits(max_files=0)

    # max_files不能超过100
    with pytest.raises(ValidationError):
        ExecutionLimits(max_files=101)

    # timeout不能为负数
    with pytest.raises(ValidationError):
        ExecutionLimits(timeout_seconds=-1)
```

### 测试用例4: JSON序列化
```python
def test_execution_plan_serialization():
    """测试ExecutionPlan的JSON序列化"""
    # Given: 一个完整的ExecutionPlan
    plan = ExecutionPlan(
        dry_run=False,
        rollback=RollbackStrategy(
            strategy="git_revert",
            commands=["git revert HEAD"]
        ),
        limits=ExecutionLimits(max_files=5, timeout_seconds=60)
    )

    # When: 序列化为JSON
    json_data = plan.model_dump_json()

    # Then: 应该能够反序列化回来
    restored_plan = ExecutionPlan.model_validate_json(json_data)
    assert restored_plan == plan
```

---

## 🔗 依赖关系

### 依赖的Story
无 - 这是Feature-001的第一个Story

### 阻塞的Story
- STORY-002: 实现Validation机制 - 需要本Story的基础定义
- STORY-003: JSON Schema导出 - 需要本Story的完整model

---

## 🎨 设计资源

### 数据结构设计
```python
# 文件位置: src/evolvai/schemas/execution_plan.py

from pydantic import BaseModel, Field, validator
from typing import List, Literal, Optional
from enum import Enum

class RollbackStrategyType(str, Enum):
    """回滚策略类型"""
    GIT_REVERT = "git_revert"
    FILE_BACKUP = "file_backup"
    MANUAL = "manual"

class ExecutionLimits(BaseModel):
    """执行限制配置"""
    max_files: int = Field(
        default=10,
        ge=1,
        le=100,
        description="最多处理的文件数量"
    )
    max_changes: int = Field(
        default=50,
        ge=1,
        le=1000,
        description="最多进行的修改次数"
    )
    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=300,
        description="执行超时时间（秒）"
    )

class ValidationConfig(BaseModel):
    """验证配置"""
    pre_conditions: List[str] = Field(
        default_factory=list,
        description="执行前必须满足的条件"
    )
    expected_outcomes: List[str] = Field(
        default_factory=list,
        description="预期的执行结果"
    )

class RollbackStrategy(BaseModel):
    """回滚策略"""
    strategy: RollbackStrategyType = Field(
        ...,
        description="回滚策略类型"
    )
    commands: List[str] = Field(
        default_factory=list,
        description="回滚命令列表"
    )

    @validator("commands")
    def validate_commands(cls, v, values):
        """验证回滚命令"""
        strategy = values.get("strategy")
        if strategy == RollbackStrategyType.MANUAL and not v:
            raise ValueError(
                "Manual rollback strategy requires commands"
            )
        return v

class ExecutionPlan(BaseModel):
    """执行计划宪法

    所有工具执行必须遵守的约束规范。
    """
    dry_run: bool = Field(
        default=True,
        description="是否先预览而不实际执行"
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="验证配置"
    )
    rollback: RollbackStrategy = Field(
        ...,
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

    class Config:
        json_schema_extra = {
            "example": {
                "dry_run": True,
                "rollback": {
                    "strategy": "git_revert",
                    "commands": []
                },
                "limits": {
                    "max_files": 10,
                    "max_changes": 50,
                    "timeout_seconds": 30
                }
            }
        }
```

---

## 🛡️ 风险与对策

| 风险 | 影响 | 对策 |
|------|------|------|
| Pydantic API变化 | Medium | 锁定Pydantic 2.x版本，添加版本兼容测试 |
| 默认值不合理 | High | 基于baseline测试调整默认值 |
| 验证规则过严 | Medium | 提供宽松模式（dev_mode），生产环境严格 |

---

## 📝 实现备注

### 设计决策
1. **为什么使用Enum而不是Literal？**
   - Enum提供更好的IDE支持和类型检查
   - 易于添加新的策略类型

2. **为什么limits有上限（max_files≤100）？**
   - 防止AI助手一次性操作过多文件导致性能问题
   - 强制分解大任务为小批次

3. **为什么pre_conditions和expected_outcomes是字符串列表？**
   - 灵活性：可以是自然语言描述或可执行断言
   - 可扩展：未来可以支持结构化验证规则

---

## 📊 进度追踪

### 开始日期
2025-10-27 09:00

### 预计完成日期
2025-10-27 17:00

### 实际完成日期
待完成

### 阻塞问题
无

---

## 📚 相关文档

- [Epic 001: 行为约束系统](./README.md)
- [Feature 001: ExecutionPlan Schema](./feature-001-execution-plan.md)
- [Task 001.1: 定义基础数据类型](../../../development/tasks/in-progress/task-001.1-base-types.md)
- [Pydantic官方文档](https://docs.pydantic.dev/)

---

**最后更新**: 2025-10-26
**更新人**: EvolvAI Team
