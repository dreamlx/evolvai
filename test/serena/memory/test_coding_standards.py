"""
Tests for CodingStandardsMemory component.

Tests coding standards learning, naming convention detection, and code transformation.
"""

import tempfile
from pathlib import Path

import pytest

from serena.memory.coding_standards import CodingStandardsMemory


@pytest.fixture
def temp_project_root():
    """Create a temporary project root for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def standards_memory(temp_project_root):
    """Create a CodingStandardsMemory instance for testing."""
    return CodingStandardsMemory(temp_project_root)


class TestCodingStandardsMemory:
    """Test cases for CodingStandardsMemory."""

    def test_init_creates_memory_directory(self, standards_memory, temp_project_root):
        """Test that initialization creates the memory directory."""
        memory_dir = temp_project_root / ".serena" / "memory" / "coding_standards"
        assert memory_dir.exists()
        assert memory_dir.is_dir()

    def test_record_naming_convention(self, standards_memory):
        """Test recording naming conventions."""
        conventions = {
            "function_example": "snake_case_function",
            "variable_test": "snake_case_variable",
            "class_example": "PascalCaseClass",
        }
        standards_memory.record_naming_convention("python", "backend", "snake_case", conventions)

        # Test retrieval
        convention = standards_memory.get_naming_convention("python", "backend")
        assert convention == "snake_case"

        # Test examples retrieval
        examples = standards_memory.get_naming_examples("python", "backend")
        assert examples == conventions

    def test_record_style_preferences(self, standards_memory):
        """Test recording style preferences."""
        style_prefs = {"max_line_length": 88, "use_black": True, "quote_style": "double"}
        standards_memory.record_style_preference("python", style_prefs)

        retrieved_prefs = standards_memory.get_style_preferences("python")
        assert retrieved_prefs == style_prefs

    def test_record_project_pattern(self, standards_memory):
        """Test recording project patterns."""
        patterns = {"has_frontend_folder": True, "has_backend_folder": True, "framework": "react"}
        standards_memory.record_project_pattern("detected", patterns)

        stored_patterns = standards_memory.get_project_patterns("detected")
        assert stored_patterns == patterns

    def test_detect_domain_from_file(self, standards_memory):
        """Test domain detection from file paths."""
        # Test frontend paths
        assert standards_memory.detect_domain_from_file("src/App.jsx") == "frontend"
        assert standards_memory.detect_domain_from_file("components/Button.tsx") == "frontend"
        assert standards_memory.detect_domain_from_file("styles/main.css") == "frontend"

        # Test backend paths
        assert standards_memory.detect_domain_from_file("services/user.py") == "backend"
        assert standards_memory.detect_domain_from_file("controllers/auth.js") == "backend"
        assert standards_memory.detect_domain_from_file("models/database.rs") == "backend"

        # Test default domain
        assert standards_memory.detect_domain_from_file("utils/helpers.go") == "general"

    def test_apply_naming_convention(self, standards_memory):
        """Test applying naming conventions."""
        # Set up naming convention
        standards_memory.record_naming_convention("python", "backend", "snake_case", {"function_example": "snake_case_function"})

        # Test snake_case conversion
        result = standards_memory.apply_naming_convention("MyFunctionName", "python", "backend")
        assert result == "my_function_name"

        # Test with no convention set
        result = standards_memory.apply_naming_convention("MyFunctionName", "javascript", "frontend")
        assert result == "MyFunctionName"  # Should return unchanged

    def test_convert_naming_convention(self, standards_memory):
        """Test naming convention conversions."""
        # Test to snake_case
        snake = standards_memory._to_snake_case("camelCaseFunction")
        assert snake == "camel_case_function"

        snake = standards_memory._to_snake_case("PascalCaseClass")
        assert snake == "pascal_case_class"

        # Test to camelCase
        camel = standards_memory._to_camel_case("snake_case_variable")
        assert camel == "snakeCaseVariable"

        # Test to PascalCase
        pascal = standards_memory._to_pascal_case("snake_case_function")
        assert pascal == "SnakeCaseFunction"

        # Test to kebab-case
        kebab = standards_memory._to_kebab_case("camelCaseString")
        assert kebab == "camel-case-string"

    def test_get_coding_standards_summary(self, standards_memory):
        """Test getting comprehensive coding standards summary."""
        # Set up coding standards
        standards_memory.record_naming_convention("python", "backend", "snake_case", {"function_example": "snake_case_function"})
        standards_memory.record_naming_convention("javascript", "frontend", "camelCase", {"function_example": "camelCaseFunction"})
        standards_memory.record_style_preference("python", {"max_line_length": 88, "use_black": True})
        standards_memory.record_project_pattern("detected", {"has_frontend_folder": True, "framework": "react"})

        summary = standards_memory.get_coding_standards_summary()

        assert summary["naming_conventions"]["python_backend"]["convention"] == "snake_case"
        assert summary["naming_conventions"]["javascript_frontend"]["convention"] == "camelCase"
        assert summary["style_preferences"]["python"]["rules"]["max_line_length"] == 88
        assert summary["project_patterns"]["detected"]["patterns"]["framework"] == "react"

    def test_clear_coding_standards_memory(self, standards_memory):
        """Test clearing coding standards memory."""
        # Set up some standards
        standards_memory.record_naming_convention("python", "backend", "snake_case", {})
        standards_memory.record_style_preference("python", {"max_line_length": 88})

        # Verify standards exist
        assert standards_memory.get_naming_convention("python", "backend") == "snake_case"
        assert standards_memory.get_style_preferences("python") is not None

        # Clear memory
        standards_memory.clear_coding_standards()

        # Verify standards are cleared
        assert standards_memory.get_naming_convention("python", "backend") is None
        assert standards_memory.get_style_preferences("python") == {}

    def test_persistence_across_instances(self, temp_project_root):
        """Test that coding standards persist across memory instances."""
        # Create first instance and record standards
        standards_memory1 = CodingStandardsMemory(temp_project_root)
        standards_memory1.record_naming_convention("python", "backend", "snake_case", {"function_example": "example_function"})
        standards_memory1.record_style_preference("python", {"max_line_length": 88})

        # Create second instance and verify standards persisted
        standards_memory2 = CodingStandardsMemory(temp_project_root)
        convention = standards_memory2.get_naming_convention("python", "backend")
        style_prefs = standards_memory2.get_style_preferences("python")

        assert convention == "snake_case"
        assert style_prefs["max_line_length"] == 88

    def test_handle_corrupted_standards_file(self, standards_memory):
        """Test handling of corrupted standards file."""
        # Get path to naming conventions file
        standards_file = standards_memory._get_config_path("naming_conventions")

        # Write invalid JSON to standards file
        with open(standards_file, "w") as f:
            f.write("invalid json content")

        # Should handle gracefully and return None for missing standards
        assert standards_memory.get_naming_convention("python", "backend") is None
        assert standards_memory.get_style_preferences("python") == {}

    def test_get_naming_examples_with_no_convention(self, standards_memory):
        """Test getting naming examples when no convention is set."""
        examples = standards_memory.get_naming_examples("python", "backend")
        assert examples == {}

    def test_get_project_patterns_with_no_patterns(self, standards_memory):
        """Test getting project patterns when no patterns are recorded."""
        patterns = standards_memory.get_project_patterns("detected")
        assert patterns == {}

    def test_naming_conversion_edge_cases(self, standards_memory):
        """Test naming convention conversion edge cases."""
        # Test with all caps
        assert standards_memory._to_snake_case("URLParser") == "url_parser"
        assert standards_memory._to_camel_case("API_URL") == "apiUrl"
        assert standards_memory._to_pascal_case("API_URL") == "ApiUrl"

        # Test with single letters
        assert standards_memory._to_snake_case("A") == "a"
        assert standards_memory._to_camel_case("a") == "a"
        assert standards_memory._to_pascal_case("a") == "A"

        # Test with consecutive separators
        assert standards_memory._to_snake_case("testXMLParser") == "test_xml_parser"
        assert standards_memory._to_kebab_case("testXMLParser") == "test-xml-parser"

    def test_apply_naming_convention_with_unsupported_convention(self, standards_memory):
        """Test applying unsupported naming convention."""
        # Set up unsupported convention
        standards_memory.conventions["python"]["backend"] = "unsupported_convention"

        # Should return unchanged input
        result = standards_memory.apply_naming_convention("MyFunction", "python", "backend")
        assert result == "MyFunction"
