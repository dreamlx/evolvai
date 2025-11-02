# Git Workflow - EvolvAI项目Git工作流

**Purpose**: Define Git workflow, branch strategy, and remote management for EvolvAI project.

**Last Updated**: 2025-11-02
**Version**: 1.0
**Status**: [APPROVED]

---

## Overview - 概述

EvolvAI是从Serena fork的独立项目，采用标准GitFlow工作流，同时保持与上游Serena的选择性同步能力。

**核心原则**:
- 🎯 **独立演进**: EvolvAI有自己的产品路线和架构设计
- 🔄 **选择性同步**: 从Serena上游cherry-pick有价值的改进
- 📋 **标准GitFlow**: 使用Git社区标准的工作流和命名约定
- 🔒 **保护主分支**: main/develop分支通过PR合并，不直接push

---

## Remote Configuration - Remote配置

### Standard Setup

```bash
# EvolvAI主仓库 (有push权限)
origin     https://github.com/dreamlx/evolvai.git

# Serena上游仓库 (仅pull)
upstream   https://github.com/oraios/serena.git
```

**命名约定原因**:
- `origin` - Git标准，指向你自己的主仓库
- `upstream` - Fork标准，指向上游项目
- 符合Git社区最佳实践和工具默认行为

### Verification

```bash
# 查看remote配置
git remote -v

# 应该显示
# origin     https://github.com/dreamlx/evolvai.git (fetch)
# origin     https://github.com/dreamlx/evolvai.git (push)
# upstream   https://github.com/oraios/serena.git (fetch)
# upstream   https://github.com/oraios/serena.git (push)
```

### Initial Setup (如果需要重新配置)

```bash
# 如果remote配置不正确，重新设置
git remote rename origin upstream
git remote add origin https://github.com/dreamlx/evolvai.git

# 验证
git remote -v
```

---

## Branch Strategy - 分支策略

### Branch Structure

```
origin/main              # 生产分支 (稳定发布版本)
    ↓
origin/develop           # 开发主线 (集成开发中的功能)
    ↓
feature/*                # 功能分支 (独立功能开发)
    ↓
[local work]             # 本地开发和测试
```

### Branch Types

**主分支** (长期存在):

1. **main** - 生产分支
   - 用途: 发布稳定版本
   - 保护: 仅通过PR从develop合并
   - Tag: 每次发布打tag (v1.0.0, v1.1.0)
   - Tracking: `origin/main`

2. **develop** - 开发主线
   - 用途: 集成所有开发中的功能
   - 保护: 仅通过PR从feature分支合并
   - 状态: 可能不稳定，但应该可运行
   - Tracking: `origin/develop`

**临时分支** (短期存在):

3. **feature/*** - 功能分支
   - 命名: `feature/{epic-num}-{story-num}-{short-desc}`
   - 示例: `feature/phase-2.5-tpst-framework`
   - 生命周期: 创建 → 开发 → 测试 → 合并到develop → 删除
   - Tracking: 通常不track remote (本地开发)

4. **hotfix/*** - 紧急修复分支
   - 命名: `hotfix/{issue-desc}`
   - 从main分支创建
   - 合并回main AND develop
   - 立即打tag和发布

5. **archive/*** - 归档分支
   - 用途: 保存历史设计或实验性代码
   - 示例: `archive/serena-memory-redesign`
   - 不合并回主线，仅保留历史参考

---

## Daily Workflow - 日常工作流

### Starting New Feature

```bash
# 1. 确保develop是最新的
git checkout develop
git pull origin develop

# 2. 创建feature分支
git checkout -b feature/epic1-story2-new-feature

# 3. 开发和提交
# ... make changes ...
git add .
git commit -m "feat(epic1): implement story 2 - new feature"

# 4. 定期push到origin (可选，用于备份)
git push origin feature/epic1-story2-new-feature
```

### Committing Changes

**Commit Message Format** (Conventional Commits):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat` - 新功能
- `fix` - Bug修复
- `docs` - 文档更新
- `style` - 代码格式化 (不影响功能)
- `refactor` - 重构 (不添加功能，不修复bug)
- `test` - 测试相关
- `chore` - 构建/工具配置

**Example**:
```bash
git commit -m "$(cat <<'EOF'
feat(phase-2.5): Implement TPST data collection framework (Cycle 1+2)

## Phase 2.5: TPST数据收集框架
实施Story 2.5.1的前2个Cycle，建立TPST(Tokens Per Solved Task)数据收集基础设施。

### Cycle 1: TPSTRecord数据模型 ✅
- Add TPSTRecord Pydantic model (15 statements, 100% coverage)
- Implement timestamp, tool tracking, token metrics
- Pass all 4 tests first try (KISS principle applied)

### Cycle 2: TPSTTracker.record()方法 ✅
- Add record() method with append-mode JSONL
- Implement automatic directory creation
- Pass all 3 tests first try (100% coverage)

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

### Merging Feature to Develop

```bash
# 1. 确保feature分支最新且测试通过
git checkout feature/epic1-story2-new-feature
uv run poe format
uv run poe type-check
uv run poe test

# 2. 更新develop到最新
git checkout develop
git pull origin develop

# 3. 合并feature分支
git merge feature/epic1-story2-new-feature

# 或使用--no-ff保留分支历史
git merge --no-ff feature/epic1-story2-new-feature

# 4. Push到origin
git push origin develop

# 5. 删除本地feature分支
git branch -d feature/epic1-story2-new-feature

# 6. 如果push过remote feature分支，也删除
git push origin --delete feature/epic1-story2-new-feature
```

---

## Release Workflow - 发布流程

### Preparing Release

```bash
# 1. 确保develop稳定且测试通过
git checkout develop
uv run poe test
uv run poe type-check

# 2. 更新版本号和CHANGELOG
# Edit pyproject.toml, CHANGELOG.md

# 3. 提交版本更新
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 1.1.0"
git push origin develop
```

### Creating Release

```bash
# 1. 切换到main分支
git checkout main
git pull origin main

# 2. 合并develop到main
git merge develop

# 3. 创建tag
git tag -a v1.1.0 -m "Release v1.1.0: TPST Framework"

# 4. Push到origin
git push origin main
git push origin v1.1.0

# 5. 在GitHub上创建Release
# 使用tag v1.1.0，附加CHANGELOG内容
```

---

## Upstream Sync - 上游同步

### EvolvAI vs Serena Relationship

**技术关系**:
- EvolvAI fork自Serena，共享LSP基础设施
- Serena: LSP工具平台
- EvolvAI: AI行为优化平台 (在LSP基础上添加GoT、Behavior Constraints等)

**同步策略**:
- ✅ **选择性同步**: Cherry-pick有价值的改进
- ✅ **关注领域**: LSP bug修复、新语言支持、性能优化
- ❌ **忽略领域**: Serena特有功能、与EvolvAI架构冲突的改动

### Checking Upstream Updates

```bash
# 1. Fetch upstream更新
git fetch upstream

# 2. 查看upstream/main的新commits
git log develop..upstream/main --oneline

# 3. 查看具体commit内容
git show <commit-hash>

# 4. 查看文件变更统计
git diff develop..upstream/main --stat
```

### Cherry-picking from Upstream

```bash
# 1. 创建临时分支进行测试
git checkout develop
git checkout -b sync/upstream-lsp-fixes

# 2. Cherry-pick有价值的commits
git cherry-pick <commit-hash>

# 3. 解决冲突 (如果有)
# ... resolve conflicts ...
git add .
git cherry-pick --continue

# 4. 测试
uv run poe test
uv run poe type-check

# 5. 如果测试通过，合并到develop
git checkout develop
git merge sync/upstream-lsp-fixes

# 6. Push到origin
git push origin develop

# 7. 删除临时分支
git branch -d sync/upstream-lsp-fixes
```

### Syncing Multiple Commits

```bash
# 如果需要同步多个连续commits
git cherry-pick <start-commit>..<end-commit>

# 或使用rebase (更适合连续的相关commits)
git rebase --onto develop <last-synced-commit> upstream/main
```

---

## Branch Management - 分支管理

### Listing Branches

```bash
# 列出所有本地分支
git branch

# 列出所有remote分支
git branch -r

# 列出所有分支 (本地+remote)
git branch -a

# 查看分支tracking状态
git branch -vv
```

### Cleaning Up Branches

```bash
# 删除已合并的本地分支
git branch -d feature/old-feature

# 强制删除未合并的分支 (慎用)
git branch -D feature/abandoned-feature

# 删除remote分支
git push origin --delete feature/old-feature

# 清理已删除的remote tracking分支
git fetch origin --prune
git fetch upstream --prune
```

### Updating Branch Tracking

```bash
# 设置当前分支tracking
git branch -u origin/develop

# 创建分支时设置tracking
git checkout -b feature/new --track origin/develop

# 查看tracking状态
git branch -vv
```

---

## Common Operations - 常见操作

### Stashing Changes

```bash
# 保存当前更改
git stash push -m "WIP: feature implementation"

# 查看stash列表
git stash list

# 恢复stash
git stash pop

# 应用stash但不删除
git stash apply stash@{0}

# 删除stash
git stash drop stash@{0}
```

### Undoing Changes

```bash
# 丢弃工作区修改 (未staged)
git restore <file>
git restore .  # 所有文件

# 取消staging (已add但未commit)
git restore --staged <file>

# 撤销最后一次commit (保留更改)
git reset --soft HEAD~1

# 撤销最后一次commit (丢弃更改) - 慎用
git reset --hard HEAD~1

# 修改最后一次commit message
git commit --amend

# 修改最后一次commit内容
git add <forgotten-file>
git commit --amend --no-edit
```

### Resolving Conflicts

```bash
# 1. 尝试合并/rebase时出现冲突
git merge feature/branch
# CONFLICT (content): Merge conflict in file.py

# 2. 查看冲突文件
git status

# 3. 编辑冲突文件，解决冲突标记
# <<<<<<< HEAD
# your changes
# =======
# their changes
# >>>>>>> feature/branch

# 4. 标记为已解决
git add file.py

# 5. 完成合并
git merge --continue
# 或 git rebase --continue

# 6. 如果想放弃合并
git merge --abort
# 或 git rebase --abort
```

---

## Git Best Practices - 最佳实践

### Commit Guidelines

**✅ Do This**:
- 频繁提交小改动 (每个逻辑单元一个commit)
- 使用清晰的commit message (遵循Conventional Commits)
- 提交前运行测试和格式化
- 保持commit历史清晰可读

**❌ Avoid This**:
- 巨大的commit (数百行变更)
- 模糊的commit message ("fix", "update", "changes")
- 提交未测试的代码
- 混合多个不相关的改动在一个commit

### Branch Naming

**✅ Good Examples**:
- `feature/phase-2.5-tpst-framework`
- `feature/epic1-story2-safe-edit`
- `hotfix/memory-leak-in-lsp`
- `archive/serena-memory-redesign`

**❌ Bad Examples**:
- `my-feature` (太模糊)
- `fix` (太简单)
- `开发新功能` (不要用中文)
- `dev-branch-2024` (无意义命名)

### Push Strategy

**开发过程**:
```bash
# Feature分支可以随时push到origin (备份)
git push origin feature/my-feature

# Develop分支只在feature合并后push
git checkout develop
git merge feature/my-feature
git push origin develop
```

**Main分支保护**:
```bash
# Main分支只在正式发布时更新
git checkout main
git merge develop
git tag v1.0.0
git push origin main --tags
```

---

## Troubleshooting - 问题排查

### Remote配置错误

**问题**: Origin指向错误的仓库

```bash
# 查看当前配置
git remote -v

# 修改remote URL
git remote set-url origin https://github.com/dreamlx/evolvai.git
git remote set-url upstream https://github.com/oraios/serena.git

# 验证
git remote -v
```

### Branch tracking错误

**问题**: 分支track错误的remote

```bash
# 查看当前tracking
git branch -vv

# 更新tracking
git branch -u origin/develop

# 或创建新分支时设置正确的tracking
git checkout -b new-branch origin/develop
```

### 误操作恢复

**问题**: 误删除分支或commit

```bash
# 查看reflog (Git的操作历史)
git reflog

# 恢复到某个历史状态
git reset --hard HEAD@{5}

# 恢复已删除的分支
git checkout -b recovered-branch <commit-hash>
```

---

## Integration with Project Workflow - 与项目工作流集成

### GitFlow + Project Management

**结合BACKLOG.md**:
```bash
# 1. BACKLOG.md中识别高优先级想法
# 2. 创建Git Issue
# 3. 创建feature分支开发
git checkout -b feature/epic1-story3-idea-from-backlog

# 4. 完成后合并到develop
# 5. 归档BACKLOG.md项到docs/planning/backlog-archive/
```

### GitFlow + TDD

**TDD Cycle中的Git操作**:
```bash
# Red Phase: 创建测试
git add test/test_new_feature.py
git commit -m "test: add tests for new feature (Red Phase)"

# Green Phase: 实现功能
git add src/new_feature.py
git commit -m "feat: implement new feature (Green Phase)"

# Refactor Phase: 优化代码 (如果需要)
git add src/new_feature.py
git commit -m "refactor: optimize new feature implementation"

# 整个Story完成后合并到develop
```

### GitFlow + Documentation

**文档更新流程**:
```bash
# 1. 与代码改动一起提交
git add src/feature.py docs/knowledge/feature-guide.md
git commit -m "feat: add feature with documentation"

# 2. 或单独更新文档
git checkout -b docs/update-architecture
git add docs/knowledge/architecture-overview.md
git commit -m "docs: update architecture overview"
git checkout develop
git merge docs/update-architecture
```

---

## Quick Reference - 快速参考

### Daily Commands

```bash
# 开始新功能
git checkout develop && git pull origin develop
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "feat: ..."
git push origin feature/new-feature

# 合并到develop
git checkout develop
git merge feature/new-feature
git push origin develop

# 清理
git branch -d feature/new-feature
```

### Sync Commands

```bash
# 检查upstream
git fetch upstream
git log develop..upstream/main --oneline

# Cherry-pick有价值的commit
git cherry-pick <commit-hash>
git push origin develop
```

### Emergency Commands

```bash
# 撤销最后一次commit
git reset --soft HEAD~1

# 丢弃所有本地更改
git reset --hard origin/develop

# 恢复误删除的分支
git reflog
git checkout -b recovered <commit-hash>
```

---

## Related Documentation - 相关文档

**项目工作流**:
- `docs/development/workflows/project-management-workflow.md` - 项目管理三层架构
- `BACKLOG.md` - 想法池
- `.claude/AI_RULES.md` - AI开发规则 (Rule 5: GitFlow Workflow)

**开发规范**:
- `docs/development/tdd-methodology.md` - TDD最佳实践
- `CLAUDE.md` - 项目概览和开发命令
- `docs/.structure.md` - 文档组织规范

---

## Version History - 版本历史

**v1.0 (2025-11-02)**:
- Initial Git workflow documentation
- Remote configuration (origin/upstream)
- Branch strategy (main/develop/feature)
- Daily workflow and release process
- Upstream sync strategy
- Common operations and troubleshooting
- Integration with project management and TDD
