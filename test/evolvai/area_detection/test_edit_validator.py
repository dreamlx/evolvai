"""
测试EditValidator的编辑验证功能
"""

import pytest
from unittest.mock import Mock, patch
from evolvai.area_detection.data_models import ProjectArea
from evolvai.area_detection.edit_validator import EditValidator, EditValidationResult, EditValidationError


class TestEditValidator:
    """测试EditValidator的核心功能"""

    def test_edit_syntax_validation_success(self):
        """测试编辑语法验证成功"""

        validator = EditValidator()

        # 模拟有效的Python代码编辑
        original_code = "def hello():\n    print('hello')"
        edited_code = "def hello():\n    print('hello world')"

        result = validator.validate_edit_syntax(
            original_code=original_code,
            edited_code=edited_code,
            file_path="test.py",
            language="python"
        )

        assert result.is_valid
        assert result.error_message is None
        assert result.syntax_errors == []

    def test_edit_syntax_validation_failure(self):
        """测试编辑语法验证失败"""

        validator = EditValidator()

        # 模拟语法错误的编辑
        original_code = "def hello():\n    print('hello')"
        edited_code = "def hello():\n    print('hello world'\n    # Missing closing parenthesis"

        result = validator.validate_edit_syntax(
            original_code=original_code,
            edited_code=edited_code,
            file_path="test.py",
            language="python"
        )

        assert not result.is_valid
        assert result.error_message is not None
        assert "syntax" in result.error_message.lower()
        assert len(result.syntax_errors) > 0

    def test_edit_area_validation_success(self):
        """测试编辑区域验证成功"""

        validator = EditValidator()

        # 模拟backend区域的编辑
        areas = [
            ProjectArea(
                name="backend-go",
                language="go",
                confidence="High",
                evidence=["go.mod"],
                file_patterns=["*.go"],
                root_path="/project"
            )
        ]

        result = validator.validate_edit_area(
            file_path="backend/auth.go",
            areas=areas
        )

        assert result.is_valid
        assert result.affected_areas == ["backend-go"]

    def test_edit_area_validation_cross_area_edit(self):
        """测试跨区域编辑验证"""

        validator = EditValidator()

        # 模拟试图编辑不属于任何区域的文件
        areas = [
            ProjectArea(
                name="backend-go",
                language="go",
                confidence="High",
                evidence=["go.mod"],
                file_patterns=["*.go"],
                root_path="/project"
            )
        ]

        result = validator.validate_edit_area(
            file_path="frontend/component.tsx",
            areas=areas
        )

        # 跨区域编辑应该被标记但可能允许
        assert result.is_valid  # 默认允许跨区域，但会记录警告
        assert len(result.warnings) > 0
        assert "cross-area" in result.warnings[0].lower()

    def test_edit_size_validation_within_limits(self):
        """测试编辑大小验证在限制内"""

        validator = EditValidator()

        # 模拟小规模编辑
        original_code = "function test() { return 1; }"
        edited_code = "function test() { return 2; }"

        result = validator.validate_edit_size(
            original_code=original_code,
            edited_code=edited_code,
            max_changes=10,
            max_lines_added=20
        )

        assert result.is_valid
        assert result.changes_count == 1
        assert result.lines_added == 0
        assert result.lines_removed == 0

    def test_edit_size_validation_exceeds_limits(self):
        """测试编辑大小验证超出限制"""

        validator = EditValidator()

        # 模拟大规模编辑
        original_code = "function test() { return 1; }"
        edited_code = "function test() { \n" + "    // " + "large change\n" * 50 + "\n    return 2; \n}"

        result = validator.validate_edit_size(
            original_code=original_code,
            edited_code=edited_code,
            max_changes=5,
            max_lines_added=10
        )

        assert not result.is_valid
        assert result.error_message is not None
        assert "exceeds" in result.error_message.lower() or "limit" in result.error_message.lower()

    def test_edit_import_validation_no_new_imports(self):
        """测试编辑导入验证 - 无新导入"""

        validator = EditValidator()

        original_code = "import os\nimport sys\ndef test(): pass"
        edited_code = "import os\nimport sys\ndef test(): return 1"

        result = validator.validate_imports(
            original_code=original_code,
            edited_code=edited_code,
            language="python"
        )

        assert result.is_valid
        assert result.new_imports == []
        assert result.removed_imports == []

    def test_edit_import_validation_with_new_imports(self):
        """测试编辑导入验证 - 有新导入"""

        validator = EditValidator()

        original_code = "import os\ndef test(): pass"
        edited_code = "import os\nimport sys\ndef test(): return 1"

        result = validator.validate_imports(
            original_code=original_code,
            edited_code=edited_code,
            language="python"
        )

        assert result.is_valid  # 新导入通常允许，但需要记录
        assert "sys" in result.new_imports
        assert len(result.new_imports) == 1

    def test_edit_import_validation_removal_detection(self):
        """测试编辑导入验证 - 检测导入移除"""

        validator = EditValidator()

        original_code = "import os\nimport sys\ndef test(): pass"
        edited_code = "import os\ndef test(): return 1"

        result = validator.validate_imports(
            original_code=original_code,
            edited_code=edited_code,
            language="python"
        )

        assert result.is_valid
        assert "sys" in result.removed_imports
        assert len(result.removed_imports) == 1

    def test_comprehensive_edit_validation_all_pass(self):
        """测试综合编辑验证 - 全部通过"""

        validator = EditValidator()

        areas = [
            ProjectArea(
                name="backend-go",
                language="go",
                confidence="High",
                evidence=["go.mod"],
                file_patterns=["*.go"],
                root_path="/project"
            )
        ]

        original_code = "package main\n\nfunc getUserData() string {\n    return \"user\"\n}"
        edited_code = "package main\n\nfunc getUserData() string {\n    return \"updated user\"\n}"

        result = validator.validate_comprehensive(
            original_code=original_code,
            edited_code=edited_code,
            file_path="backend/user.go",
            language="go",
            areas=areas,
            max_changes=5,
            max_lines_added=10
        )

        assert result.is_valid
        assert result.syntax_errors == []
        assert result.warnings == []
        assert result.affected_areas == ["backend-go"]

    def test_comprehensive_edit_validation_with_warnings(self):
        """测试综合编辑验证 - 有警告但通过"""

        validator = EditValidator()

        # 空区域列表，会产生跨区域编辑警告
        areas = []

        original_code = "function test() { return 1; }"
        edited_code = "function test() { return 2; }"

        result = validator.validate_comprehensive(
            original_code=original_code,
            edited_code=edited_code,
            file_path="test.js",
            language="javascript",
            areas=areas,
            max_changes=5,
            max_lines_added=10
        )

        assert result.is_valid  # 有警告但仍然有效
        assert len(result.warnings) > 0
        assert "cross-area" in result.warnings[0].lower()

    def test_comprehensive_edit_validation_failure(self):
        """测试综合编辑验证 - 验证失败"""

        validator = EditValidator()

        areas = []

        # 模拟语法错误的编辑
        original_code = "function test() { return 1; }"
        edited_code = "function test() { return 2;\n    // syntax error"

        result = validator.validate_comprehensive(
            original_code=original_code,
            edited_code=edited_code,
            file_path="test.js",
            language="javascript",
            areas=areas,
            max_changes=5,
            max_lines_added=10
        )

        assert not result.is_valid
        assert result.error_message is not None
        assert len(result.syntax_errors) > 0


class TestEditValidationError:
    """测试EditValidationError异常"""

    def test_edit_validation_error_creation(self):
        """测试EditValidationError创建"""

        error = EditValidationError(
            error_type="syntax_error",
            message="Invalid syntax detected",
            file_path="test.py",
            line_number=10,
            details={"error_char": 25}
        )

        assert error.error_type == "syntax_error"
        assert error.message == "Invalid syntax detected"
        assert error.file_path == "test.py"
        assert error.line_number == 10
        assert error.details["error_char"] == 25

    def test_edit_validation_error_str_representation(self):
        """测试EditValidationError字符串表示"""

        error = EditValidationError(
            error_type="size_limit",
            message="Edit exceeds size limits",
            file_path="large_file.py"
        )

        error_str = str(error)
        assert "size_limit" in error_str
        assert "large_file.py" in error_str
        assert "Edit exceeds size limits" in error_str