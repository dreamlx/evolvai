# 🗑️ 代码删除清单 - Feature 2.2 重构

**目的**: 删除过度设计，专注核心价值
**原则**: AI时代，理解哪些该删比理解哪些该加更重要
**日期**: 2025-11-07

---

## 📊 删除概览

| 类型 | 文件数 | 代码行 | 理由 |
|------|--------|--------|------|
| 旧实现 | 2 | ~400行 | 架构错误，需重写 |
| 过度设计 | 部分 | ~150行 | YAGNI原则 |
| 错误测试 | 1 | ~370行 | 测试错误假设 |
| **总计** | ~3 | ~920行 | 减少40%代码量 |

---

## 🔴 Phase 1: 备份和标记（立即执行）

### 1.1 创建备份分支
```bash
git checkout -b archive/feature-2.2-old-implementation
git add .
git commit -m "archive: 备份Feature 2.2旧实现（Patch-First重构前）"
git push origin archive/feature-2.2-old-implementation
```

### 1.2 切回develop继续工作
```bash
git checkout develop
```

---

## 🟡 Phase 2: 删除过度设计代码（重构开始前）

### 2.1 删除safe_edit_batch（批量操作）

**文件**: `src/evolvai/area_detection/edit_wrapper.py`
**行数**: 177-220 (约43行)
**理由**: 产品定义未要求，Phase 3再考虑

**删除内容**:
```python
def safe_edit_batch(
    self,
    batch_edits: list[dict[str, Any]],
    continue_on_error: bool = False,
    max_parallel: int = 1
) -> list[dict[str, Any]]:
    """批量编辑操作（不需要）"""
    # ... 43行代码
```

**验证**:
```bash
grep -n "safe_edit_batch" src/evolvai/area_detection/edit_wrapper.py
# 应该找不到
```

---

### 2.2 删除mode参数系统（conservative/aggressive）

**文件**: `src/evolvai/area_detection/edit_wrapper.py`
**位置**: safe_edit()方法参数和逻辑
**理由**: 产品未要求，增加复杂度

**删除步骤**:
1. 删除`mode`参数（保留"safe"作为默认值即可）
2. 删除mode相关的if/else分支
3. 删除mode相关的配置验证

**影响的测试**:
- `test_safe_edit_mode_validation` - 整个测试删除

---

### 2.3 简化区域感知逻辑

**文件**: `src/evolvai/area_detection/edit_wrapper.py`
**理由**: 过度抽象，MVP简化

**保留**:
- 基础的语言检测（language参数）
- 文件路径验证

**删除**:
- 复杂的区域匹配逻辑
- area_selector的多种模式
- 过度详细的区域报告

---

### 2.4 删除safe_edit_mcp()方法假设

**文件**: `test/evolvai/area_detection/test_safe_edit_wrapper.py`
**位置**: test_safe_edit_mcp_interface
**理由**: 误解MCP集成方式

**正确理解**:
- safe_edit()通过Tool系统自动暴露
- 不需要单独的_mcp()包装方法
- MCP集成在`src/serena/tools/safe_tools.py`

---

## 🟢 Phase 3: 重写核心实现（Day 1-5）

### 3.1 重写safe_edit → propose_edit

**新文件**: `src/evolvai/tools/patch_editor.py`

**类结构**:
```python
class PatchEditor:
    """Patch-First编辑器"""

    def propose_edit(
        self,
        pattern: str,
        replacement: str,
        scope: str = "**/*",
        **kwargs
    ) -> ProposalResult:
        """生成patch，不修改文件"""
        pass

    def apply_edit(
        self,
        patch_id: str,
        execution_plan: Optional[ExecutionPlan] = None,
        **kwargs
    ) -> ApplyResult:
        """应用patch，Git worktree隔离"""
        pass
```

**删除旧的**:
- `SafeEditWrapper.safe_edit()` - 大部分逻辑重写
- 保留辅助方法（如果有用）

---

### 3.2 重写测试文件

**新文件**: `test/evolvai/tools/test_patch_editor.py`

**测试结构**（基于BDD场景）:
```python
class TestProposeEdit:
    def test_propose_single_file_edit_success(self):
        """Scenario 1"""
        pass

    def test_propose_multi_file_edit_with_scope(self):
        """Scenario 2"""
        pass


class TestApplyEdit:
    def test_apply_single_file_patch_success(self):
        """Scenario 3"""
        pass

    def test_apply_invalid_patch_id(self):
        """Scenario 4"""
        pass

    def test_apply_patch_conflict_rollback(self):
        """Scenario 5"""
        pass

    # ... 等等
```

**完全删除旧的**:
- `test/evolvai/area_detection/test_safe_edit_wrapper.py` (370行)

---

## 🔵 Phase 4: 清理相关文件（重构完成后）

### 4.1 更新导入语句

**文件**: 需要更新import的地方
```python
# 旧的
from evolvai.area_detection.edit_wrapper import SafeEditWrapper

# 新的
from evolvai.tools.patch_editor import PatchEditor
```

**查找需要更新的位置**:
```bash
grep -r "SafeEditWrapper" src/ test/
grep -r "safe_edit_wrapper" src/ test/
```

---

### 4.2 删除未使用的辅助类

**检查是否还在使用**:
- `EditValidator` - 可能可以简化
- `RollbackManager` - Git worktree后可能不需要
- `FeedbackSystem` - 如果只用于edit，可以内联

**命令**:
```bash
grep -r "EditValidator\|RollbackManager\|FeedbackSystem" src/
```

---

### 4.3 清理测试fixture

**文件**: `test/evolvai/area_detection/conftest.py`

**检查**:
- 是否有safe_edit专用的fixture
- 是否有过度复杂的mock setup

**原则**: 新测试应该尽量简单，少用fixture

---

## ✅ 验证清单

### 代码层面
- [ ] 旧实现已备份到archive分支
- [ ] safe_edit_batch已删除
- [ ] mode系统已简化
- [ ] safe_edit_mcp()假设已删除
- [ ] 新PatchEditor类已实现
- [ ] 新测试文件基于BDD场景

### 测试层面
- [ ] 旧测试文件已删除
- [ ] 新测试100%基于BDD场景
- [ ] 每个测试有Scenario注释
- [ ] 无over-engineering测试

### 质量层面
- [ ] `uv run poe format` 通过
- [ ] `uv run poe type-check` 通过
- [ ] `uv run poe lint` 通过
- [ ] 测试覆盖率 ≥ 90%

### 功能层面
- [ ] propose_edit可用
- [ ] apply_edit可用
- [ ] Git worktree隔离工作
- [ ] 冲突自动回滚
- [ ] MCP集成成功

---

## 📊 删除效果预测

### 代码行数对比

| 指标 | 旧实现 | 新实现 | 变化 |
|------|--------|--------|------|
| 核心代码 | ~400行 | ~250行 | -37% |
| 测试代码 | ~370行 | ~300行 | -19% |
| 总代码 | ~770行 | ~550行 | -29% |

### 复杂度对比

| 指标 | 旧实现 | 新实现 | 改进 |
|------|--------|--------|------|
| 方法数 | 15+ | 8 | -47% |
| 嵌套层级 | 4-5层 | 2-3层 | -40% |
| Mock复杂度 | 7/10 | 3/10 | -57% |
| 认知负担 | 高 | 低 | ⭐⭐⭐⭐ |

### 用户价值对比

| 功能 | 旧实现 | 新实现 |
|------|--------|--------|
| diff预览 | ❌ | ✅ |
| propose/apply分离 | ❌ | ✅ |
| Git隔离 | ❌ | ✅ |
| 原子性 | ❌ | ✅ |
| 批量操作 | ✅ (不需要) | ❌ (Phase 3) |
| 模式系统 | ✅ (伪需求) | ❌ |

---

## 🎯 删除原则

### 什么该删？

1. **过度设计的功能**
   - 产品定义未要求
   - 增加复杂度
   - 用户价值低

2. **架构错误的代码**
   - 违反核心设计原则
   - 无法修补，必须重写

3. **测试错误假设**
   - 测试不存在的方法
   - 测试伪需求

### 什么该保留？

1. **可复用的工具函数**
   - 文件扫描
   - 语言检测
   - diff生成

2. **有价值的测试场景**
   - 约束违规处理
   - 错误处理
   - 边界情况

3. **清晰的接口设计**
   - ExecutionPlan集成点
   - MCP工具定义
   - 审计日志接口

---

## 📝 删除日志

| 日期 | 删除内容 | 行数 | 执行人 |
|------|---------|------|--------|
| 2025-11-07 | [待执行] | | |

---

**最后更新**: 2025-11-07
**状态**: 📋 Ready for Execution
**下一步**: 开始Phase 1备份
