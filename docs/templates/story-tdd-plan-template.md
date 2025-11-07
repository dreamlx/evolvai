# Story [编号] TDD 开发计划：[Story标题]

**Story ID**: STORY-[编号]
**Epic**: Epic-[编号] ([Phase/Feature名称])
**工期**: [X] 人天
**风险**: [🟢 低风险 | 🟡 中风险 | 🔴 高风险]
**依赖**: [前置Story编号或"无"]
**状态**: [PLANNING | IN_PROGRESS | COMPLETED]

---

## 📋 Story 目标

[简短描述这个Story要实现什么功能]

**核心原则**: [如：KISS原则、100%向后兼容等]

**交付物**：
1. [交付物1] - [简短描述]
2. [交付物2] - [简短描述]
3. [交付物3] - [简短描述]
...

---

## ⚠️ 风险评估

### [风险级别]风险因素

1. **[风险名称1]**：[风险描述]
   - **缓解**：[缓解措施]

2. **[风险名称2]**：[风险描述]
   - **缓解**：[缓解措施]

---

## 🎯 BDD场景与DoD映射

**关键场景总览**：

| BDD场景 | DoD标准 | 测试函数 | Cycle |
|---------|---------|----------|-------|
| "[场景名称1]" | F1 | `test_xxx` | Cycle 1 |
| "[场景名称2]" | Q1 | `test_yyy` | Cycle 2 |
| "[场景名称3]" | F2 | `test_zzz` | Cycle 3 |

**DoD验收标准**：
- **F1** - [功能完整性标准描述]
- **Q1** - [质量标准描述]
- **P1** - [性能标准描述]

---

## 🧪 TDD 开发策略

### Red-Green-Refactor 循环计划

采用**[策略名称，如：逐步集成]**策略，每个循环完成一个[单元，如：集成点]：

```
Cycle 1: [Cycle名称]
  Red → Green → Refactor → Commit

Cycle 2: [Cycle名称]
  Red → Green → Refactor → Commit

Cycle 3: [Cycle名称]
  Red → Green → Refactor → Commit

...
```

---

## 📁 测试文件结构

```
test/[路径]/
├── test_[模块1].py        # [描述]
├── test_[模块2].py        # [描述]
└── test_[模块3].py        # NEW - [描述]

src/[路径]/
├── [模块1].py              # [更新/已存在/NEW]
├── [模块2].py              # [更新/已存在/NEW]
└── [模块3].py              # [更新/已存在/NEW]
```

---

## 🔴 Cycle 1: [Cycle名称]

### 🚨 Task开始前检查清单（MANDATORY - 必须填写）

在写任何代码前，必须回答：

- [ ] **我已阅读完整Story文档**（包含所有BDD场景和DoD标准）
- [ ] **这个Cycle实现以下场景**：
  - [ ] Scenario: "[场景名称1]"
  - [ ] Scenario: "[场景名称2]"（如有）
- [ ] **这个Cycle满足DoD标准**：[F1/Q1/P1等]
- [ ] **测试文件位置确认**：`test/[路径]/test_[模块].py`

**如果以上任何一项为空 → 不要开始写代码！返回重新阅读Story文档**

---

### Red 阶段 - 编写测试

**测试文件**: `test/[路径]/test_[模块].py`

```python
"""Tests for [模块描述]."""

import pytest
from unittest.mock import Mock, patch

from [模块路径] import [类/函数]


class Test[功能描述]:
    """Test [功能描述]."""

    def test_[场景1描述](self):
        """[测试描述]

        Story: story-[编号]-[name].md Cycle 1
        Scenario: "[BDD场景名称]"
        DoD: [DoD标准]

        Given [前置条件]
        When [执行动作]
        Then [期望结果]
        """
        # Given: [前置条件描述]
        [设置代码]

        # When: [执行动作描述]
        result = [执行代码]

        # Then: [期望结果描述]
        assert [断言]

    def test_[场景2描述](self):
        """[测试描述]

        Story: story-[编号]-[name].md Cycle 1
        Scenario: "[BDD场景名称]"
        DoD: [DoD标准]

        Given [前置条件]
        When [执行动作]
        Then [期望结果]
        """
        # 测试实现
```

**期望结果**: 所有测试失败（Red），因为功能尚未实现。

---

### Green 阶段 - 实现最小代码

**[新建/更新]文件**: `src/[路径]/[模块].py`

```python
"""[模块描述]"""


class [类名]:
    """[类描述]

    [详细说明]
    """

    def [方法名](self, [参数]):
        """[方法描述]

        Args:
            [参数]: [参数描述]

        Returns:
            [返回值描述]

        Raises:
            [异常描述]
        """
        [实现代码]
```

**注意事项**：
- ✅ **按照测试中的接口实现**（函数名、参数顺序、参数名必须一致）
- ❌ **不要"优化"接口** - 如果测试接口不合理，先修改测试
- ✅ **实现最简单能通过测试的代码**

**期望结果**: 测试通过（Green）。

---

### Refactor 阶段 - 优化代码

1. 确保类型提示完整（mypy strict 通过）
2. 添加详细的 docstrings
3. 优化 import 顺序
4. 添加日志记录（DEBUG 级别）
5. 代码格式化：`uv run poe format`
6. 类型检查：`uv run poe type-check`

---

### Commit

```bash
git add [文件列表]
git commit -m "feat(epic[X]-story[Y]-cycle1): [Cycle名称]

- [完成事项1]
- [完成事项2]
- [完成事项3]
- [测试数量] tests added

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## 🔴 Cycle 2: [Cycle名称]

### 🚨 Task开始前检查清单（MANDATORY）

- [ ] 我已阅读Cycle 2定义
- [ ] 这个Cycle实现场景：[列出场景]
- [ ] DoD标准：[标准编号]

---

### Red 阶段 - 编写测试

[测试代码]

### Green 阶段 - 实现代码

[实现代码]

### Refactor 阶段

[重构清单]

### Commit

[提交命令]

---

## 🔴 Cycle N: [重复Cycle结构]

[继续添加Cycle，直到完成所有功能]

---

## 📊 Story [编号] 验收标准

### 功能完整性

- [ ] [功能点1] - [描述]
- [ ] [功能点2] - [描述]
- [ ] [功能点3] - [描述]

### 测试覆盖率

- [ ] [X-Y] tests total
- [ ] 100% code coverage for [核心模块]
- [ ] All [场景类型] scenarios tested
- [ ] [特殊要求，如：向后兼容性验证]

### 性能指标

- [ ] [性能指标1]: [目标值]
- [ ] [性能指标2]: [目标值]
- [ ] [性能指标3]: [目标值]

### 代码质量

- [ ] 100% mypy strict compliance
- [ ] RUFF + BLACK formatting
- [ ] Comprehensive docstrings
- [ ] Clear error messages

---

## 📝 Story [编号] 完成报告模板

```markdown
# Story [编号] Completion Report

**Status**: ✅ COMPLETED
**Date**: [completion date]
**Branch**: feature/epic[X]-story[Y]-[name]
**Merged to**: develop

## Summary

Story [编号] successfully [实现内容摘要].

## Deliverables

1. ✅ [交付物1] - [完成情况]
2. ✅ [交付物2] - [完成情况]
3. ✅ [交付物3] - [完成情况]

## Key Achievements

- [成就1]
- [成就2]
- [成就3]

## Performance Metrics

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| [指标1] | [目标] | [实际] | ✅/⚠️/❌ |
| [指标2] | [目标] | [实际] | ✅/⚠️/❌ |

## Test Results

- Total tests: [数量]
- Passed: [通过率]%
- Coverage: [覆盖率]%
- Performance: [评价]

## Next Steps

- Story [下一个]: [标题]
- Branch: feature/epic[X]-story[Y+1]-[name]
```

---

**Last Updated**: [日期]
**Status**: [TEMPLATE]
**Next Action**: 复制此模板创建具体Story的TDD计划

---

## 📚 相关文档

- [BDD测试模板](bdd-test-template.md) - 测试编写规范
- [TDD重构指南](../testing/standards/tdd-refactoring-guidelines.md) - KISS原则
- [Definition of Done](../development/standards/definition-of-done.md) - 验收标准
- [CLAUDE.md](../../CLAUDE.md) - 强制检查点

---

## 💡 使用说明

### 创建新Story TDD计划

```bash
# 1. 复制模板
cp docs/templates/story-tdd-plan-template.md docs/development/sprints/current/story-X.Y-tdd-plan.md

# 2. 填写所有[占位符]
# 3. 完成"BDD场景与DoD映射"表格
# 4. 为每个Cycle填写"Task开始前检查清单"
```

### 关键原则

1. **Task开始前检查清单必须填写** - 防止盲目开发
2. **所有测试必须标注Story/Scenario/DoD** - 防止过度设计
3. **按测试接口实现** - 防止接口不匹配
4. **找不到映射就停止** - 询问用户而非猜测

---

**维护者**: EvolvAI Team
**反馈渠道**: GitHub Issues
