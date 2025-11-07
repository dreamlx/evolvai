"""
Feature 2.2: safe_edit Patch-First Architecture - Tests
基于BDD场景的TDD测试套件
"""


import pytest

from evolvai.tools.patch_editor import (
    ApplyResult,
    PatchEditor,
    PatchNotFoundError,
    ProposalResult,
)


class TestProposeEdit:
    """propose_edit功能测试 - Scenario 1-2"""

    def test_propose_single_file_edit_success(self, tmp_path):
        """
        Scenario 1: 成功生成单文件diff

        Story: story-2.2-bdd-scenarios.md Scenario 1
        DoD: F1 - propose_edit生成unified diff

        Given 项目目录包含文件 "src/user.go"
        When 调用 propose_edit(pattern="getUserData", replacement="fetchUserData")
        Then 返回成功的ProposalResult
          And patch_id格式为 "patch_<timestamp>_<hash>"
          And unified_diff包含正确的差异
          And 原文件未被修改
          And patch保存到内存
        """
        # Arrange - 准备测试文件
        test_file = tmp_path / "src" / "user.go"
        test_file.parent.mkdir(parents=True)
        original_content = 'package main\nfunc getUserData() string { return "user" }'
        test_file.write_text(original_content)

        editor = PatchEditor(project_root=tmp_path)

        # Act - 执行propose_edit
        result = editor.propose_edit(
            pattern="getUserData",
            replacement="fetchUserData"
        )

        # Assert - 验证结果
        # DoD F1.1: 返回ProposalResult
        assert isinstance(result, ProposalResult)
        
        # DoD F1.2: patch_id格式正确
        assert result.patch_id.startswith("patch_")
        parts = result.patch_id.split("_")
        assert len(parts) == 3  # patch_timestamp_hash
        assert parts[1].isdigit()  # timestamp
        assert len(parts[2]) == 8  # hash
        
        # DoD F1.3: unified_diff包含正确的差异
        assert "src/user.go" in result.unified_diff
        assert "-func getUserData()" in result.unified_diff
        assert "+func fetchUserData()" in result.unified_diff
        
        # DoD F1.4: affected_files正确
        assert len(result.affected_files) == 1
        assert "src/user.go" in result.affected_files[0]
        
        # DoD F1.5: statistics有意义
        assert "files_modified" in result.statistics
        assert result.statistics["files_modified"] == 1
        assert "lines_changed" in result.statistics
        
        # DoD F1.6: 原文件未被修改
        assert test_file.read_text() == original_content
        
        # DoD F1.7: patch保存到内存
        assert result.patch_id in editor.patch_store
        stored_patch = editor.patch_store[result.patch_id]
        assert stored_patch.unified_diff == result.unified_diff

    def test_propose_multi_file_edit_with_scope(self, tmp_path):
        """
        Scenario 2: 扫描多文件生成完整patch

        Story: story-2.2-bdd-scenarios.md Scenario 2
        DoD: F1 - propose_edit生成unified diff

        Given 项目有backend/和frontend/文件
        When 调用 propose_edit(..., scope="backend/**")
        Then 只扫描backend目录
          And unified_diff包含所有匹配文件
          And frontend文件未被扫描
        """
        # Arrange - 准备多个测试文件
        backend_dir = tmp_path / "backend"
        frontend_dir = tmp_path / "frontend"
        backend_dir.mkdir()
        frontend_dir.mkdir()

        (backend_dir / "user.go").write_text("func getUserData() { ... }")
        (backend_dir / "auth.go").write_text("user := getUserData()")
        (frontend_dir / "api.ts").write_text("const data = getUserData()")

        editor = PatchEditor(project_root=tmp_path)

        # Act - 只在backend目录中进行编辑
        result = editor.propose_edit(
            pattern="getUserData",
            replacement="fetchUserData",
            scope="backend/**/*"
        )

        # Assert
        # DoD F1.1: 返回ProposalResult
        assert isinstance(result, ProposalResult)
        
        # DoD F1.2: 只包含backend文件
        assert len(result.affected_files) == 2
        assert all("backend" in f for f in result.affected_files)
        assert not any("frontend" in f for f in result.affected_files)
        
        # DoD F1.3: unified_diff包含所有backend文件变更
        assert "backend/user.go" in result.unified_diff
        assert "backend/auth.go" in result.unified_diff
        assert "frontend/api.ts" not in result.unified_diff
        
        # DoD F1.4: statistics正确
        assert result.statistics["files_modified"] == 2
        
        # DoD F1.5: 原文件未被修改
        assert "getUserData" in (backend_dir / "user.go").read_text()
        assert "getUserData" in (frontend_dir / "api.ts").read_text()


class TestApplyEdit:
    """apply_edit功能测试 - Scenario 3-6"""

    def test_apply_single_file_patch_success(self, tmp_path):
        """
        Scenario 3: 成功应用单文件patch

        Story: story-2.2-bdd-scenarios.md Scenario 3
        DoD: F2, F3 - apply_edit接受patch_id + Git worktree隔离

        Given 已有有效的patch_id
        When 调用 apply_edit(patch_id)
        Then 创建临时Git worktree
          And 在worktree中执行git apply
          And 成功后合并到主目录
          And 清理临时worktree
          And 返回成功的ApplyResult
        """
        # Arrange - 准备Git仓库和文件
        import subprocess
        
        # 初始化Git仓库
        subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True, capture_output=True)
        
        # 创建并提交原始文件
        test_file = tmp_path / "user.go"
        original_content = 'package main\nfunc getUserData() string { return "user" }'
        test_file.write_text(original_content)
        subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=tmp_path, check=True, capture_output=True)
        
        # 生成patch
        editor = PatchEditor(project_root=tmp_path)
        proposal = editor.propose_edit(
            pattern="getUserData",
            replacement="fetchUserData"
        )
        
        # Act - 应用patch
        result = editor.apply_edit(patch_id=proposal.patch_id)
        
        # Assert - 验证结果
        # DoD F2.1: 返回ApplyResult
        assert isinstance(result, ApplyResult)
        
        # DoD F2.2: 操作成功
        assert result.success is True
        assert result.error_message is None
        
        # DoD F2.3: modified_files正确
        assert len(result.modified_files) == 1
        assert "user.go" in result.modified_files[0]
        
        # DoD F3.1: 文件内容已更新
        assert "fetchUserData" in test_file.read_text()
        assert "getUserData" not in test_file.read_text()
        
        # DoD F3.2: worktree已清理 (不存在临时目录)
        if result.worktree_path:
            from pathlib import Path
            assert not Path(result.worktree_path).exists()

    def test_apply_invalid_patch_id(self, tmp_path):
        """
        Scenario 4: patch_id不存在

        Story: story-2.2-bdd-scenarios.md Scenario 4
        DoD: F2 - apply_edit验证patch存在

        Given 不存在的patch_id
        When 调用 apply_edit(patch_id="invalid_patch")
        Then 抛出PatchNotFoundError
          And 错误消息清晰
          And 未创建worktree
          And 未修改任何文件
        """
        editor = PatchEditor(project_root=tmp_path)
        
        # DoD F2.1: 抛出PatchNotFoundError
        with pytest.raises(PatchNotFoundError, match="Patch 'invalid_patch' not found"):
            editor.apply_edit(patch_id="invalid_patch")

    def test_apply_patch_conflict_rollback(self, tmp_path):
        """
        Scenario 5: patch与当前代码冲突

        Story: story-2.2-bdd-scenarios.md Scenario 5
        DoD: F3, F4 - Git worktree隔离 + 原子性回滚

        Given patch基于旧版本文件
          And 主目录文件已被修改（冲突）
        When 调用 apply_edit(patch_id)
        Then git apply失败
          And 自动清理worktree
          And 抛出PatchConflictError
          And 主目录未被修改
        """
        pytest.skip("Day 3: Conflict handling implementation")

    def test_apply_with_isolated_validation(self, tmp_path):
        """
        Scenario 6: 在worktree中验证后才合并

        Story: story-2.2-bdd-scenarios.md Scenario 6
        DoD: F3 - Git worktree隔离验证

        Given 配置了post_apply_validation
        When 调用 apply_edit(patch_id)
        Then 在worktree中apply patch
          And 运行验证脚本
          And 验证通过后才合并
          And 清理worktree
        """
        pytest.skip("Day 3: Isolated validation implementation")


class TestExecutionPlanIntegration:
    """ExecutionPlan集成测试 - Scenario 7"""

    def test_apply_with_max_changes_violation(self, tmp_path):
        """
        Scenario 7a: patch修改超过max_changes限制

        Story: story-2.2-bdd-scenarios.md Scenario 7
        DoD: F2 - ExecutionPlan集成

        Given ExecutionPlan定义max_changes=3
        When patch修改产生4行变化
        Then 抛出ConstraintViolationError
          And 未执行任何修改
        """
        from evolvai.core.execution_plan import (
            ExecutionLimits,
            ExecutionPlan,
            RollbackStrategy,
            RollbackStrategyType,
        )
        from evolvai.tools import ConstraintViolationError

        # Arrange - 准备测试文件
        test_file = tmp_path / "user.go"
        original_content = '''package main

func getUserData() string {
    return "user"
}

func getUser() {
    data := getUserData()
    return data
}'''
        test_file.write_text(original_content)

        editor = PatchEditor(project_root=tmp_path)

        # 生成一个会产生很多变化的patch(>5行)
        proposal = editor.propose_edit(
            pattern="getUserData",
            replacement="fetchUserData"
        )

        # Act & Assert - 应用时违反max_changes约束
        # Note: This patch will produce 4 changes (2 deletions + 2 additions)
        execution_plan = ExecutionPlan(
            dry_run=False,
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.GIT_REVERT,
                commands=[]
            ),
            limits=ExecutionLimits(
                max_files=10,
                max_changes=3,  # 限制为3, 实际变更为4
                timeout_seconds=30
            )
        )

        with pytest.raises(ConstraintViolationError) as exc_info:
            editor.apply_edit(patch_id=proposal.patch_id, execution_plan=execution_plan)

        # 验证异常详情
        assert exc_info.value.constraint_type == "max_changes"
        assert exc_info.value.limit == 3
        assert exc_info.value.actual == 4  # 实际变更数

        # 验证文件未被修改
        assert test_file.read_text() == original_content

    def test_apply_with_max_files_violation(self, tmp_path):
        """
        Scenario 7b: patch影响文件数超过max_files限制

        Story: story-2.2-bdd-scenarios.md Scenario 7
        DoD: F2 - ExecutionPlan集成

        Given ExecutionPlan定义max_files=1
        When patch影响2个文件
        Then 抛出ConstraintViolationError
          And 未执行任何修改
        """
        from evolvai.core.execution_plan import (
            ExecutionLimits,
            ExecutionPlan,
            RollbackStrategy,
            RollbackStrategyType,
        )
        from evolvai.tools import ConstraintViolationError

        # Arrange - 准备多个测试文件
        file1 = tmp_path / "user.go"
        file2 = tmp_path / "auth.go"
        file1.write_text('func getUserData() { return "user" }')
        file2.write_text('user := getUserData()')

        editor = PatchEditor(project_root=tmp_path)

        # 生成影响2个文件的patch
        proposal = editor.propose_edit(
            pattern="getUserData",
            replacement="fetchUserData"
        )

        # Act & Assert - 应用时违反max_files约束
        execution_plan = ExecutionPlan(
            dry_run=False,
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.GIT_REVERT,
                commands=[]
            ),
            limits=ExecutionLimits(
                max_files=1,  # 只允许1个文件
                max_changes=50,
                timeout_seconds=30
            )
        )

        with pytest.raises(ConstraintViolationError) as exc_info:
            editor.apply_edit(patch_id=proposal.patch_id, execution_plan=execution_plan)

        # 验证异常详情
        assert exc_info.value.constraint_type == "max_files"
        assert exc_info.value.limit == 1
        assert exc_info.value.actual == 2

    def test_apply_with_execution_plan_success(self, tmp_path):
        """
        Scenario 7c: ExecutionPlan约束满足，正常执行

        Story: story-2.2-bdd-scenarios.md Scenario 7
        DoD: F2 - ExecutionPlan集成

        Given ExecutionPlan定义合理的限制
        When patch在限制范围内
        Then 成功应用patch
          And 返回成功的ApplyResult
        """
        from evolvai.core.execution_plan import (
            ExecutionLimits,
            ExecutionPlan,
            RollbackStrategy,
            RollbackStrategyType,
        )

        # Arrange
        test_file = tmp_path / "user.go"
        original_content = 'func getUserData() { return "user" }'
        test_file.write_text(original_content)

        editor = PatchEditor(project_root=tmp_path)
        proposal = editor.propose_edit(
            pattern="getUserData",
            replacement="fetchUserData"
        )

        # Act - 使用合理的ExecutionPlan
        execution_plan = ExecutionPlan(
            dry_run=False,
            rollback=RollbackStrategy(
                strategy=RollbackStrategyType.GIT_REVERT,
                commands=[]
            ),
            limits=ExecutionLimits(
                max_files=10,
                max_changes=50,
                timeout_seconds=30
            )
        )

        result = editor.apply_edit(patch_id=proposal.patch_id, execution_plan=execution_plan)

        # Assert
        assert result.success is True
        assert len(result.modified_files) == 1
        assert "fetchUserData" in test_file.read_text()


class TestMCPIntegration:
    """MCP接口集成测试 - Scenario 8"""

    def test_mcp_propose_edit_tool_registered(self):
        """
        Scenario 8a: propose_edit工具已注册到MCP系统

        Story: story-2.2-bdd-scenarios.md Scenario 8
        DoD: F5 - MCP工具暴露

        Given EvolvAI MCP服务器启动
        When 检查已注册的工具列表
        Then propose_edit工具存在于工具注册表中
          And 工具元数据包含正确的文档说明
        """
        from serena.tools import ToolRegistry

        registry = ToolRegistry()

        # DoD F5.1: propose_edit工具已注册
        assert "propose_edit" in registry.get_tool_names()

        # DoD F5.2: 工具类可以被获取
        propose_tool_class = registry.get_tool_class_by_name("propose_edit")
        assert propose_tool_class is not None

        # DoD F5.3: 工具有正确的文档字符串
        tool_description = propose_tool_class.get_tool_description()
        assert "Patch-First" in tool_description or "unified diff" in tool_description

        # DoD F5.4: apply方法有正确的文档字符串
        apply_docstring = propose_tool_class.get_apply_docstring_from_cls()
        assert "pattern" in apply_docstring.lower()
        assert "replacement" in apply_docstring.lower()
        assert "scope" in apply_docstring.lower()

    def test_mcp_apply_edit_tool_registered(self):
        """
        Scenario 8b: apply_edit工具已注册到MCP系统

        Story: story-2.2-bdd-scenarios.md Scenario 8
        DoD: F5 - MCP工具暴露

        Given EvolvAI MCP服务器启动
        When 检查已注册的工具列表
        Then apply_edit工具存在于工具注册表中
          And 工具元数据包含正确的文档说明
          And 工具标记为可编辑工具
        """
        from serena.tools import ToolRegistry

        registry = ToolRegistry()

        # DoD F5.1: apply_edit工具已注册
        assert "apply_edit" in registry.get_tool_names()

        # DoD F5.2: 工具类可以被获取
        apply_tool_class = registry.get_tool_class_by_name("apply_edit")
        assert apply_tool_class is not None

        # DoD F5.3: 工具标记为可编辑
        assert apply_tool_class.can_edit() is True

        # DoD F5.4: 工具有正确的文档字符串
        tool_description = apply_tool_class.get_tool_description()
        assert "ExecutionPlan" in tool_description or "constraints" in tool_description

        # DoD F5.5: apply方法文档包含必需参数说明
        apply_docstring = apply_tool_class.get_apply_docstring_from_cls()
        assert "patch_id" in apply_docstring.lower()
        assert "max_files" in apply_docstring.lower()
        assert "max_changes" in apply_docstring.lower()
        assert "timeout" in apply_docstring.lower()


@pytest.fixture
def sample_patch_content():
    """示例patch内容"""
    return """--- a/src/user.go
+++ b/src/user.go
@@ -1,1 +1,1 @@
-func getUserData() string { return "user" }
+func fetchUserData() string { return "user" }
"""
