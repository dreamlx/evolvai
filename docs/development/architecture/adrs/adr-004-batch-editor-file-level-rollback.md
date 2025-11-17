# ADR-004: BatchEditor文件级回滚设计

**状态**: ✅ Accepted
**日期**: 2025-01-15
**决策者**: Claude Code (Expert Mode Analysis)
**相关Issue**: Story 2.2 - Batch Edit System
**相关代码**: `src/evolvai/tools/batch_editor.py`

---

## 背景

BatchEditor实现批量文件编辑功能，需要在编辑失败时提供自动回滚机制。有两种主要的回滚方案：
1. **Git回滚**：创建git commit作为回滚点，失败时`git reset --hard`
2. **文件级回滚**：为每个文件创建备份，失败时恢复备份

## 问题陈述

在开发环境中，批量编辑工具如何安全地回滚失败的操作，同时不影响用户的其他工作？

### 典型使用场景
```bash
# 开发者正常工作状态
$ git status
Modified: src/api.py        # 用户正在开发的功能
Modified: src/utils.py      # 用户正在开发的功能
Untracked: new_feature.py   # 用户新写的代码

# 使用BatchEditor重命名函数
$ batch_edit(pattern="oldFunc", replacement="newFunc", scope="*.py")
# 修改了3个文件

# 如果第2个文件写入失败...
# 需要回滚，但不能影响用户的api.py, utils.py, new_feature.py
```

## 决策

**选择方案2：文件级回滚**

在`FileChange`数据模型中为每个文件保存独立的`rollback_hash`，使用`RollbackManager.rollback_file_backup(hash, path)`精确恢复。

### 核心实现
```python
@dataclass
class FileChange:
    file_path: Path
    original_content: str
    new_content: str
    match_count: int
    rollback_hash: Optional[str] = None  # 文件级备份ID

def _create_backups(self, changes: list[FileChange]) -> str:
    """为每个文件创建独立备份"""
    for change in changes:
        result = self.rollback_manager.create_file_backup(str(change.file_path))
        change.rollback_hash = result.rollback_hash  # 保存精确hash
    return changes[0].rollback_hash if changes else None

def _rollback_changes(self, changes: list[FileChange]) -> None:
    """使用精确hash恢复每个文件"""
    for change in changes:
        if change.rollback_hash:
            self.rollback_manager.rollback_file_backup(
                change.rollback_hash,
                str(change.file_path)
            )  # 只恢复batch_edit修改的文件
```

## 考虑的方案

### 方案A：Git回滚 ❌

**实现**：
```python
def batch_edit():
    # 1. 创建git commit作为回滚点
    subprocess.run(['git', 'add', '-A'])
    subprocess.run(['git', 'commit', '-m', 'batch_edit checkpoint'])
    commit_hash = get_current_commit()

    # 2. 执行批量编辑
    try:
        apply_changes()
    except:
        # 3. 失败时git reset
        subprocess.run(['git', 'reset', '--hard', commit_hash])
```

**优势**：
- ✅ 原子性保证（git的事务特性）
- ✅ 单个commit hash管理所有文件
- ✅ 实现简单

**致命缺陷**：
- ❌ **会清除用户所有未提交修改**
  ```bash
  # 用户状态：有未提交修改（正常开发状态）
  Modified: api.py, utils.py
  Untracked: new_feature.py

  # batch_edit创建commit并失败
  $ git reset --hard commit_hash

  # 💥 灾难：用户的api.py, utils.py, new_feature.py全部丢失！
  ```

- ❌ 仅适用于CI/CD clean state
- ❌ 依赖外部系统（git）
- ❌ 破坏开发流程

**结论**：不安全，可能造成数据丢失

### 方案B：文件级回滚 ✅

**实现**：见"决策"部分

**优势**：
- ✅ **只恢复batch_edit修改的文件**
- ✅ **用户其他修改完全不受影响**
- ✅ 不依赖git（支持非git项目）
- ✅ 精确控制（使用明确ID，不猜测）
- ✅ 独立备份存储（`.serena/backups/`）

**劣势**：
- ⚠️ 需要修改FileChange数据模型
- ⚠️ 实现复杂度中等
- ⚠️ 非原子性（理论上可能部分文件恢复失败）

**结论**：安全可靠，适用于开发环境

### 方案C：简化测试期望 ❌

**实现**：测试只验证rollback_id存在，不验证实际回滚

**结论**：逃避问题，失去自动回滚的核心价值

## 决策理由

### 核心原则

**工具级回滚 > 系统级回滚（粒度原则）**
```
开发工具的回滚 ≠ 版本控制的回滚

批量编辑工具应该：
  ✅ 只恢复自己修改的文件
  ✅ 不影响用户的其他工作
  ✅ 不依赖外部系统的clean state

Git回滚会：
  ❌ 清除所有未提交修改
  ❌ 丢失用户的工作成果
  ❌ 破坏开发流程
```

### 设计原则

1. **粒度原则**：工具级回滚 > 系统级回滚
2. **隔离原则**：只管理自己创建的资源
3. **安全原则**：不依赖外部系统clean state
4. **精确原则**：使用明确ID而非智能猜测

### 用户场景分析

**批量编辑工具的典型用户**：
- 身份：正在开发的程序员
- 典型状态：dirty working directory（有未提交修改）
- 使用场景：重构、批量重命名、格式化

**错误假设**：
- ❌ 用户在clean state下使用（CI/CD视角）
- ❌ 用户会先提交所有修改再使用工具

**正确假设**：
- ✅ 用户在开发过程中随时使用
- ✅ 用户有多个未提交的工作
- ✅ 工具失败不应影响其他工作

## 实施结果

### 测试验证
- ✅ `test_auto_rollback_on_partial_failure` 通过
- ✅ 9/9 tests passing (100%)
- ✅ 所有其他测试保持通过

### 安全性保证
- ✅ 用户的其他未提交修改完全不受影响
- ✅ 每个文件独立备份ID，精确恢复
- ✅ 备份存储在`.serena/backups/`，独立管理
- ✅ 单个文件回滚失败不影响其他文件

### 代码修改
- 文件：`src/evolvai/tools/batch_editor.py`
- 变更：+27/-10 lines
- 提交：`716907c`

## 批量回滚的正确模式

基于这次分析，确立了批量操作回滚的最佳实践：

```
1. 创建备份时：为每个资源保存独立rollback_id
2. 执行操作时：逐个处理，记录成功/失败
3. 回滚时：使用精确ID恢复每个资源
4. 报告时：提供批次级rollback_id（用于展示/日志）
```

**关键洞察**：
- 批次操作 = 多个独立操作的集合
- 每个操作需要独立的回滚能力
- 批次ID用于关联，不是唯一的恢复凭证

## 影响范围

### 正面影响
- ✅ 开发环境安全使用批量编辑
- ✅ 不依赖git，支持所有项目
- ✅ 精确回滚，可预测行为

### 负面影响
- ⚠️ FileChange数据结构变更（内部API）
- ⚠️ 实现复杂度略增

### 风险缓解
- 内部数据结构变更，不影响公共API
- 完整测试覆盖（9/9 tests）
- 向后兼容（BatchEditResult.rollback_id仍可用）

## 经验教训

### 1. 工具设计要考虑实际使用场景
- 批量编辑工具的用户：正在开发的程序员
- 典型状态：dirty working directory
- 错误假设：clean state（CI/CD视角）

### 2. 自动化工具的安全边界
- 只管理自己创建的资源
- 不干涉用户的其他工作
- 提供精确控制，不做"智能猜测"

### 3. 系统性分析的价值
- 理解"为什么" > 解决"是什么"
- 考虑长期影响 > 短期通过测试
- 用户洞察 > 技术可行性

## 参考资料

- [Story 2.2 Implementation Plan](../../sprints/current/story-2.2-implementation-plan.md)
- [RollbackManager Implementation](../../../src/evolvai/area_detection/rollback_manager.py)
- [Test Suite](../../../test/evolvai/tools/test_batch_editor.py)
- Commit: `716907c` - Precise file-level rollback

## 后续行动

- ✅ 实施文件级回滚
- ✅ 验证所有测试通过
- ✅ 文档化决策（本ADR）
- 📋 考虑在其他批量操作工具中应用此模式
- 📋 监控实际使用中的回滚成功率

---

**Status**: ✅ Accepted
**Last Updated**: 2025-01-15
**Next Review**: 2025-02-15（或Story 2.2完成后）
