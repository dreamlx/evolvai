# Lesson 002: 工具级回滚 vs 系统级回滚

**日期**: 2025-01-15
**来源**: Story 2.2 - BatchEditor自动回滚设计
**相关ADR**: [ADR-004](../../development/architecture/adrs/adr-004-batch-editor-file-level-rollback.md)
**严重程度**: 🔴 Critical - 可能导致数据丢失

---

## 核心教训

**开发工具的回滚 ≠ 版本控制的回滚**

为开发环境设计的批量操作工具，**绝不应使用Git等系统级回滚**，因为会清除用户的其他未提交工作。

---

## 问题场景

### ❌ 错误做法：Git回滚
```python
def batch_edit():
    # 创建git commit作为回滚点
    subprocess.run(['git', 'commit', '-m', 'checkpoint'])

    try:
        apply_changes()
    except:
        # 💥 危险：会清除用户所有未提交修改！
        subprocess.run(['git', 'reset', '--hard', 'HEAD~1'])
```

### 实际后果
```bash
# 用户正常开发状态
$ git status
Modified: api.py           # 用户正在开发
Modified: utils.py         # 用户正在开发
Untracked: new_feature.py  # 用户新写的代码

# 使用batch_edit，执行失败
# Git回滚执行...

# 💥 灾难：api.py, utils.py, new_feature.py 全部丢失！
$ git status
On branch main
nothing to commit, working tree clean
```

---

## 正确做法

### ✅ 文件级精确回滚
```python
@dataclass
class FileChange:
    file_path: Path
    rollback_hash: str  # 每个文件独立的备份ID

def batch_edit():
    # 1. 为每个文件创建独立备份
    for change in changes:
        backup = create_file_backup(change.file_path)
        change.rollback_hash = backup.hash

    # 2. 执行操作
    try:
        apply_changes()
    except:
        # 3. 只恢复batch_edit修改的文件
        for change in changes:
            rollback_file_backup(
                change.rollback_hash,
                change.file_path
            )  # ✅ 用户其他工作不受影响
```

---

## 核心原则

### 1. 粒度原则
```
工具级回滚 > 系统级回滚

批量操作工具应该：
  ✅ 只恢复自己修改的资源
  ✅ 不影响用户的其他工作
  ✅ 提供精确控制

系统级回滚（Git/数据库事务）会：
  ❌ 影响所有资源
  ❌ 清除无关的修改
  ❌ 破坏开发流程
```

### 2. 隔离原则
```
工具只管理自己创建的资源
  ✅ 独立备份存储（.serena/backups/）
  ✅ 每个资源独立ID
  ✅ 精确恢复，不猜测
```

### 3. 安全原则
```
不依赖外部系统的clean state
  ✅ 假设用户有未提交修改
  ✅ 假设用户在开发过程中使用
  ✅ 工具失败不应影响其他工作
```

---

## 批量回滚的正确模式

### 设计模板
```python
# 1. 创建备份时：为每个资源保存独立rollback_id
for resource in resources:
    backup = create_backup(resource)
    resource.rollback_id = backup.id  # 关键！

# 2. 执行操作时：逐个处理，记录成功/失败
results = []
for resource in resources:
    try:
        result = process(resource)
        results.append(result)
    except Exception as e:
        results.append(error)

# 3. 回滚时：使用精确ID恢复每个资源
if any_failure(results):
    for resource in resources:
        if resource.rollback_id:
            restore_backup(
                resource.rollback_id,  # 精确ID
                resource.path
            )

# 4. 报告时：提供批次级rollback_id（用于展示/日志）
batch_id = resources[0].rollback_id  # 第一个资源的ID作为批次ID
```

### 关键洞察
```
批次操作 = 多个独立操作的集合

每个操作需要：
  - 独立的备份（rollback_id）
  - 独立的回滚能力
  - 独立的成功/失败状态

批次ID用于：
  - 关联操作（日志/UI展示）
  - 不是唯一的恢复凭证
```

---

## 适用场景

### 何时必须用文件级回滚
- ✅ 开发环境的批量操作工具
- ✅ IDE插件/编辑器扩展
- ✅ 代码重构工具
- ✅ 批量文件处理

### 何时可以考虑系统级回滚
- ⚠️ CI/CD环境（保证clean state）
- ⚠️ 生产部署（可控环境）
- ⚠️ 数据库迁移（事务隔离）

**前提条件**：
- 环境完全可控
- 保证clean state
- 有专门的测试/回滚流程

---

## 检查清单

设计批量操作工具时，问自己：

- [ ] 用户可能在dirty working directory下使用吗？
- [ ] 用户可能有其他未保存的工作吗？
- [ ] 工具失败时，应该只回滚工具的修改吗？
- [ ] 能否为每个资源保存独立的回滚ID？
- [ ] 回滚时能否精确恢复，不影响其他资源？

**如果任一问题答案为"是" → 使用文件级回滚**

---

## 相关案例

### 成功案例
- ✅ BatchEditor: 文件级rollback_hash
- ✅ VSCode Refactoring: 文件级undo stack
- ✅ IntelliJ Refactoring: Local History

### 失败案例
- ❌ Git-based auto-formatter（会清除未提交修改）
- ❌ Database migration with reset（丢失数据）

---

## 参考资料

- [ADR-004: BatchEditor文件级回滚设计](../../development/architecture/adrs/adr-004-batch-editor-file-level-rollback.md)
- [RollbackManager实现](../../../src/evolvai/area_detection/rollback_manager.py)
- [BatchEditor实现](../../../src/evolvai/tools/batch_editor.py)

---

**关键要点**：
> 为开发环境设计工具时，永远假设用户有未保存的工作。
> 工具只回滚自己的修改，不影响用户的其他工作。
> 这不是技术选择，是用户体验和数据安全的底线。
