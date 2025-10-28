"""
Tests for Coding Standards Tools.

Tests code analysis, standards application, and pattern learning.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from serena.agent import SerenaAgent
from serena.config.serena_config import ProjectConfig
from serena.project import Project
from serena.tools.coding_standards_tools import AnalyzeCodingStandardsTool, ApplyCodingStandardsTool, ShowCodingStandardsTool


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_project(temp_project_root):
    """Create a mock project for testing tools."""
    project_config = ProjectConfig(
        project_name="test_project",
        language="python",
        ignored_paths=[],
        excluded_tools=set(),
        read_only=False,
        ignore_all_files_in_gitignore=True,
        initial_prompt="",
        encoding="utf-8",
    )
    return Project(project_root=str(temp_project_root), project_config=project_config)


@pytest.fixture
def mock_agent(mock_project):
    """Create a mock Serena agent."""
    agent = Mock(spec=SerenaAgent)
    agent.project = mock_project
    agent.serena_config = Mock()
    agent.serena_config.default_max_tool_answer_chars = 10000
    return agent


@pytest.fixture
def python_code_files(temp_project_root):
    """Create sample Python code files for testing."""
    # Create Python files with snake_case patterns
    python_code = '''
def get_user_data():
    """Get user information from database."""
    user_id = 123
    return {"id": user_id, "name": "test_user"}

class UserService:
    """Service class for user management."""

    def __init__(self):
        self.database_connection = None

    def create_user(self, user_data):
        """Create a new user."""
        return True
'''

    # Create JavaScript files with camelCase patterns
    js_code = """
function getUserData() {
    const userId = 123;
    return { id: userId, name: "test_user" };
}

class UserService {
    constructor() {
        this.databaseConnection = null;
    }

    createUser(userData) {
        return true;
    }
}
"""

    # Write Python files
    (temp_project_root / "services").mkdir()
    (temp_project_root / "services" / "user.py").write_text(python_code)
    (temp_project_root / "models" / "user.py").write_text(python_code)

    # Write JavaScript files
    (temp_project_root / "frontend").mkdir()
    (temp_project_root / "frontend" / "user.js").write_text(js_code)
    (temp_project_root / "frontend" / "User.jsx").write_text(js_code)

    # Create package.json for React detection
    package_json = {"name": "test-project", "version": "1.0.0", "dependencies": {"react": "^18.0.0"}}
    (temp_project_root / "package.json").write_text(json.dumps(package_json))


class TestAnalyzeCodingStandardsTool:
    """Test cases for AnalyzeCodingStandardsTool."""

    @pytest.fixture
    def analyze_tool(self, mock_agent):
        """Create AnalyzeCodingStandardsTool instance."""
        return AnalyzeCodingStandardsTool(mock_agent)

    def test_analyze_python_standards(self, analyze_tool, mock_agent, temp_project_root, python_code_files):
        """Test analyzing Python coding standards."""
        result = analyze_tool.apply()
        result_data = json.loads(result)

        assert result_data["status"] == "Coding standards analysis completed"
        assert "learned_patterns" in result_data
        assert "python" in result_data["learned_patterns"]

        python_analysis = result_data["learned_patterns"]["python"]
        assert "backend_snake_case" in python_analysis
        assert "examples" in python_analysis

    def test_analyze_javascript_standards(self, analyze_tool, mock_agent, temp_project_root, python_code_files):
        """Test analyzing JavaScript/TypeScript coding standards."""
        result = analyze_tool.apply()
        result_data = json.loads(result)

        assert "javascript" in result_data["learned_patterns"]
        assert "typescript" in result_data["learned_patterns"]

        js_analysis = result_data["learned_patterns"]["javascript"]
        assert "frontend_camelCase" in js_analysis
        assert "examples" in js_analysis

    def test_detect_project_patterns(self, analyze_tool, mock_agent, temp_project_root, python_code_files):
        """Test detecting project patterns."""
        result = analyze_tool.apply()
        result_data = json.loads(result)

        assert "project_patterns" in result_data["learned_patterns"]
        patterns = result_data["learned_patterns"]["project_patterns"]

        assert patterns["has_frontend_folder"] is True
        assert patterns["framework"] == "react"

    def test_analyze_with_no_code_files(self, analyze_tool, mock_agent, temp_project_root):
        """Test analysis when no code files exist."""
        result = analyze_tool.apply()
        result_data = json.loads(result)

        assert result_data["status"] == "Coding standards analysis completed"
        assert result_data["learned_patterns"] == {}

    def test_analyze_with_file_patterns(self, analyze_tool, mock_agent, temp_project_root, python_code_files):
        """Test analysis with specific file patterns."""
        result = analyze_tool.apply("*.py")
        result_data = json.loads(result)

        # Should only analyze Python files
        assert "python" in result_data["learned_patterns"]
        # JavaScript/TypeScript should not be analyzed
        assert "javascript" not in result_data["learned_patterns"]


class TestApplyCodingStandardsTool:
    """Test cases for ApplyCodingStandardsTool."""

    @pytest.fixture
    def apply_tool(self, mock_agent):
        """Create ApplyCodingStandardsTool instance."""
        return ApplyCodingStandardsTool(mock_agent)

    def test_apply_snake_case_convention(self, apply_tool, mock_agent, temp_project_root):
        """Test applying snake_case naming convention."""
        # Pre-set coding standards
        from serena.memory.coding_standards import CodingStandardsMemory

        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("python", "backend", "snake_case", {})

        original_code = "def myTestFunction():\n    localVar = 123\n    return localVar"
        result = apply_tool.apply(original_code, "python", "services/user.py")
        result_data = json.loads(result)

        assert result_data["original_language"] == "python"
        assert result_data["detected_domain"] == "backend"
        assert "transformed_code" in result_data
        assert "applied_conventions" in result_data

    def test_apply_camel_case_convention(self, apply_tool, mock_agent, temp_project_root):
        """Test applying camelCase naming convention."""
        # Pre-set coding standards
        from serena.memory.coding_standards import CodingStandardsMemory

        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("javascript", "frontend", "camelCase", {})

        original_code = "function my_test_function() {\n    let local_var = 123;\n    return local_var;\n}"
        result = apply_tool.apply(original_code, "javascript", "frontend/user.js")
        result_data = json.loads(result)

        assert result_data["original_language"] == "javascript"
        assert result_data["detected_domain"] == "frontend"
        assert "transformed_code" in result_data

    def test_apply_with_no_standards(self, apply_tool, mock_agent, temp_project_root):
        """Test applying standards when none are set."""
        original_code = "def testFunction(): pass"
        result = apply_tool.apply(original_code, "python", "test.py")
        result_data = json.loads(result)

        # Should return unchanged code
        assert result_data["transformed_code"] == original_code
        assert result_data["applied_conventions"]["naming_convention"] is None

    def test_domain_detection_from_file_context(self, apply_tool, mock_agent, temp_project_root):
        """Test domain detection from file context."""
        # Test frontend domain
        result = apply_tool.apply("function test() {}", "javascript", "src/components/Button.jsx")
        result_data = json.loads(result)
        assert result_data["detected_domain"] == "frontend"

        # Test backend domain
        result = apply_tool.apply("def test(): pass", "python", "services/user.py")
        result_data = json.loads(result)
        assert result_data["detected_domain"] == "backend"

        # Test general domain
        result = apply_tool.apply("def test(): pass", "python", "utils/helpers.py")
        result_data = json.loads(result)
        assert result_data["detected_domain"] == "general"

    def test_apply_style_preferences(self, apply_tool, mock_agent, temp_project_root):
        """Test applying style preferences."""
        # Pre-set style preferences
        from serena.memory.coding_standards import CodingStandardsMemory

        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_style_preferences("python", {"max_line_length": 88, "quote_style": "double"})

        original_code = "def test():\n    return 'single quotes'"
        result = apply_tool.apply(original_code, "python", "test.py")
        result_data = json.loads(result)

        assert result_data["applied_conventions"]["style_rules_applied"] is True

    def test_get_applied_conventions(self, apply_tool, mock_agent, temp_project_root):
        """Test getting applied conventions information."""
        # Pre-set coding standards
        from serena.memory.coding_standards import CodingStandardsMemory

        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("python", "backend", "snake_case", {})

        result = apply_tool.apply("def testFunction(): pass", "python", "test.py")
        result_data = json.loads(result)

        conventions = result_data["applied_conventions"]
        assert conventions["naming_convention"] == "snake_case"


class TestShowCodingStandardsTool:
    """Test cases for ShowCodingStandardsTool."""

    @pytest.fixture
    def show_tool(self, mock_agent):
        """Create ShowCodingStandardsTool instance."""
        return ShowCodingStandardsTool(mock_agent)

    def test_show_empty_standards(self, show_tool, mock_agent, temp_project_root):
        """Test showing standards when none are set."""
        result = show_tool.apply()
        result_data = json.loads(result)

        assert "coding_standards" in result_data
        assert result_data["coding_standards"]["naming_conventions"] == {}
        assert result_data["coding_standards"]["style_preferences"] == {}
        assert result_data["coding_standards"]["project_patterns"] == {}

    def test_show_saved_standards(self, show_tool, mock_agent, temp_project_root):
        """Test showing saved coding standards."""
        # Pre-set coding standards
        from serena.memory.coding_standards import CodingStandardsMemory

        standards_memory = CodingStandardsMemory(temp_project_root)
        standards_memory.record_naming_convention("python", "backend", "snake_case", {"function_example": "test_function"})
        standards_memory.record_style_preferences("python", {"max_line_length": 88, "use_black": True})
        standards_memory.record_project_pattern("detected", {"has_frontend_folder": True, "framework": "react"})

        result = show_tool.apply()
        result_data = json.loads(result)

        standards = result_data["coding_standards"]
        assert standards["naming_conventions"]["python"]["backend"] == "snake_case"
        assert standards["style_preferences"]["python"]["max_line_length"] == 88
        assert standards["project_patterns"]["framework"] == "react"

    def test_message_in_result(self, show_tool, mock_agent, temp_project_root):
        """Test that result contains explanatory message."""
        result = show_tool.apply()
        result_data = json.loads(result)

        assert "message" in result_data
        assert "optimize AI-generated code" in result_data["message"]
