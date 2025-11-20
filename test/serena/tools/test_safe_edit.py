"""
Story 2.2: safe_edit TDD Tests
TDD Cycle 1: propose_edit 核心功能
TDD Cycle 2: apply_edit 核心功能

架构决策: ADR-006 - 基于工作目录操作，不使用Git worktree
"""

import inspect
import subprocess

import pytest

from evolvai.tools.safe_edit import (
    PatchAlreadyAppliedError,
    PatchNotFoundError,
    PatchOutdatedError,
    SafeEditTool,
)


class TestProposalCore:
    """Cycle 1: propose_edit 核心功能测试"""
    
    def test_propose_edit_basic_flow(self, tmp_path):
        """
        Test 1.1: 基础 propose 流程
        Given: 工作目录有1个文件
        When: propose_edit 替换文本
        Then: 返回 patch_id 和 unified diff，文件未修改
        """
        # Setup
        file = tmp_path / "main.py"
        file.write_text("def old_func():\n    pass\n")
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Execute
        result = tool.propose_edit(
            pattern="old_func",
            replacement="new_func",
            scope="**/*.py"
        )
        
        # Verify
        assert result["patch_id"] is not None
        assert "old_func" in result["unified_diff"]
        assert "new_func" in result["unified_diff"]
        
        # 关键: 文件未修改
        assert file.read_text() == "def old_func():\n    pass\n"
    
    def test_propose_based_on_working_directory(self, tmp_path):
        """
        Test 1.2: 基于工作目录（包含 unstaged 修改）
        Given: Git 仓库，文件有 unstaged 修改
        When: propose_edit
        Then: diff 基于工作目录内容（不是 HEAD）
        """
        # Setup: 创建 Git 仓库
        subprocess.run(["git", "init"], check=False, cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], check=False, cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], check=False, cwd=tmp_path, capture_output=True)
        
        file = tmp_path / "main.py"
        
        # 1. 提交初始版本
        file.write_text("version = '1.0'\n")
        subprocess.run(["git", "add", "main.py"], check=False, cwd=tmp_path, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial"], check=False, cwd=tmp_path, capture_output=True)
        
        # 2. 修改文件（unstaged）
        file.write_text("version = '2.0'\n")  # ← unstaged 修改
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Execute
        result = tool.propose_edit(
            pattern="version = '2.0'",
            replacement="version = '3.0'",
            scope="**/*.py"
        )
        
        # Verify: diff 基于工作目录（2.0 → 3.0），不是 HEAD（1.0）
        assert "version = '2.0'" in result["unified_diff"]  # from
        assert "version = '3.0'" in result["unified_diff"]  # to
        assert "version = '1.0'" not in result["unified_diff"]  # 不包含 HEAD
    
    def test_propose_multiple_files(self, tmp_path):
        """
        Test 1.3: 多文件批量预览
        Given: 多个文件需要修改
        When: propose_edit
        Then: 返回所有文件的 unified diff
        """
        # Setup
        (tmp_path / "a.py").write_text("name = 'old'\n")
        (tmp_path / "b.py").write_text("name = 'old'\n")
        (tmp_path / "c.txt").write_text("name = 'old'\n")  # 不匹配 scope
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Execute
        result = tool.propose_edit(
            pattern="old",
            replacement="new",
            scope="**/*.py"
        )
        
        # Verify
        assert set(result["affected_files"]) == {"a.py", "b.py"}  # 不包含 c.txt
        assert result["statistics"]["files_modified"] == 2
        assert "a.py" in result["unified_diff"]
        assert "b.py" in result["unified_diff"]
    
    def test_propose_no_matches(self, tmp_path):
        """
        Test 1.4: 无匹配时返回空
        Given: 文件不匹配 pattern
        When: propose_edit
        Then: 返回空 patch
        """
        # Setup
        file = tmp_path / "main.py"
        file.write_text("def func():\n    pass\n")
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Execute
        result = tool.propose_edit(
            pattern="nonexistent",
            replacement="new",
            scope="**/*.py"
        )
        
        # Verify
        assert result["affected_files"] == []
        assert result["statistics"]["files_modified"] == 0
        assert result["unified_diff"] == ""
    
    def test_propose_with_regex_pattern(self, tmp_path):
        """
        Test 1.5: 复杂正则 pattern
        Given: 使用复杂正则 pattern
        When: propose_edit
        Then: 正则匹配和捕获组工作正常
        """
        # Setup
        file = tmp_path / "main.py"
        file.write_text('log.info("message")\nlog.debug("data")\n')
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Execute: 替换所有 log.X → logger.X
        result = tool.propose_edit(
            pattern=r'log\.(\w+)\("(.*)"\)',
            replacement=r'logger.\1("\2", extra={"timestamp": True})',
            scope="**/*.py"
        )
        
        # Verify
        assert 'logger.info("message"' in result["unified_diff"]
        assert 'logger.debug("data"' in result["unified_diff"]
        assert 'extra={"timestamp": True}' in result["unified_diff"]
    
    def test_patch_storage_and_retrieval(self, tmp_path):
        """
        Test 1.6: Patch 存储和检索
        Given: propose_edit 返回 patch_id
        When: 使用 patch_id 检索
        Then: 可以获取完整 patch 信息
        """
        # Setup
        file = tmp_path / "main.py"
        file.write_text("old\n")
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Execute
        result1 = tool.propose_edit("old", "new", "**/*.py")
        patch_id = result1["patch_id"]
        
        # Verify: 可以检索 patch
        patch = tool._get_patch(patch_id)
        assert patch is not None
        assert patch["unified_diff"] == result1["unified_diff"]
        assert len(patch["changes"]) == 1
        assert patch["changes"][0]["file"] == "main.py"
        assert patch["changes"][0]["original"] == "old\n"
        assert patch["changes"][0]["new"] == "new\n"


class TestApplyCore:
    """Cycle 2: apply_edit 核心功能测试"""
    
    def test_apply_edit_basic_flow(self, tmp_path):
        """
        Test 2.1: 基础 apply 流程
        Given: propose_edit 返回的 patch_id
        When: apply_edit
        Then: 文件被修改，返回 rollback_id
        """
        # Setup
        file = tmp_path / "main.py"
        file.write_text("old\n")
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Propose
        propose_result = tool.propose_edit("old", "new", "**/*.py")
        patch_id = propose_result["patch_id"]
        
        # Execute
        apply_result = tool.apply_edit(patch_id=patch_id)
        
        # Verify
        assert apply_result["success"] is True
        assert apply_result["rollback_id"] is not None
        assert file.read_text() == "new\n"  # 文件已修改
    
    def test_apply_invalid_patch_id(self, tmp_path):
        """
        Test 2.2: 无效 patch_id 拒绝
        Given: 无效的 patch_id
        When: apply_edit
        Then: 抛出 PatchNotFoundError
        """
        tool = SafeEditTool(project_root=tmp_path)
        
        with pytest.raises(PatchNotFoundError):
            tool.apply_edit(patch_id="invalid-uuid")
    
    def test_apply_does_not_accept_pattern_replacement(self, tmp_path):
        """
        Test 2.3: 不接受 pattern/replacement
        Given: apply_edit 只接受 patch_id
        When: 检查方法签名
        Then: 不包含 pattern/replacement 参数
        """
        tool = SafeEditTool(project_root=tmp_path)
        
        # Verify: apply_edit 签名只接受 patch_id 和 execution_plan
        sig = inspect.signature(tool.apply_edit)
        assert "patch_id" in sig.parameters
        assert "pattern" not in sig.parameters
        assert "replacement" not in sig.parameters
    
    def test_patch_can_only_apply_once(self, tmp_path):
        """
        Test 2.4: Patch 只能 apply 一次
        Given: patch_id 已经 applied
        When: 再次 apply 同一个 patch_id
        Then: 抛出 PatchAlreadyAppliedError
        """
        # Setup
        file = tmp_path / "main.py"
        file.write_text("old\n")
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Propose
        result = tool.propose_edit("old", "new", "**/*.py")
        patch_id = result["patch_id"]
        
        # First apply - OK
        tool.apply_edit(patch_id)
        
        # Second apply - Error
        with pytest.raises(PatchAlreadyAppliedError):
            tool.apply_edit(patch_id)
    
    def test_apply_multiple_files_atomic(self, tmp_path):
        """
        Test 2.5: 多文件原子性应用
        Given: patch 影响多个文件
        When: apply_edit
        Then: 所有文件同时修改（原子性）
        """
        # Setup
        file_a = tmp_path / "a.py"
        file_b = tmp_path / "b.py"
        file_a.write_text("old\n")
        file_b.write_text("old\n")
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Propose
        result = tool.propose_edit("old", "new", "**/*.py")
        
        # Apply
        tool.apply_edit(result["patch_id"])
        
        # Verify: 两个文件都被修改
        assert file_a.read_text() == "new\n"
        assert file_b.read_text() == "new\n"
    
    def test_apply_detects_file_changes(self, tmp_path):
        """
        Test 2.6: Patch 过期检测（文件变更冲突）
        Given: propose_edit 生成 patch
        When: 文件在 propose 后被修改
        Then: apply_edit 检测冲突，拒绝应用
        """
        # Setup
        file = tmp_path / "main.py"
        file.write_text("version = '1.0'\n")
        
        tool = SafeEditTool(project_root=tmp_path)
        
        # Step 1: Propose
        result = tool.propose_edit("1.0", "2.0", "**/*.py")
        patch_id = result["patch_id"]
        
        # Step 2: 文件被修改（模拟用户或其他进程修改）
        file.write_text("version = '1.5'\n")  # 内容已变化
        
        # Step 3: Apply - 应该检测到冲突
        with pytest.raises(PatchOutdatedError) as exc:
            tool.apply_edit(patch_id)
        
        assert "has changed since propose_edit" in str(exc.value)
        
        # Verify: 文件未被修改（保持用户的 1.5）
        assert file.read_text() == "version = '1.5'\n"


# DoD 1 验收标准：
# ✅ 基于工作目录（包含 unstaged/staged/untracked）
# ✅ 生成 unified diff 格式
# ✅ 支持多文件批量预览
# ✅ 支持复杂正则 pattern
# ✅ patch_id 可检索
# ✅ 不修改任何文件

# DoD 2 验收标准:
# ✅ 验证 patch_id 有效性
# ✅ 应用 patch 到工作目录
# ✅ 不接受 pattern/replacement（物理删除错误路径）
# ✅ Patch 只能 apply 一次
# ✅ 多文件原子性应用
# ✅ 检测文件变更冲突（Patch 过期）

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
