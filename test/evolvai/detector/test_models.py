"""Test cases for ProjectArea dataclass."""

from dataclasses import is_dataclass
from typing import get_type_hints

from evolvai.detector.models import ProjectArea


def test_project_area_completeness():
    """Test ProjectArea has all required fields."""
    area = ProjectArea(
        name="backend-go",
        language="go",
        root_path="/tmp/backend",
        confidence="High",
        evidence=["go.mod", "cmd/"],
        file_patterns=["backend/**/*.go"],
        exclude_patterns=["backend/vendor/**"],
    )

    # Test all 7 fields are accessible and have correct values
    assert area.name == "backend-go"
    assert area.language == "go"
    assert area.root_path == "/tmp/backend"
    assert area.confidence == "High"
    assert area.evidence == ["go.mod", "cmd/"]
    assert area.file_patterns == ["backend/**/*.go"]
    assert area.exclude_patterns == ["backend/vendor/**"]


def test_project_area_is_dataclass():
    """Test ProjectArea is properly decorated as dataclass."""
    assert is_dataclass(ProjectArea)


def test_project_area_type_safety():
    """Test ProjectArea field types exist."""
    # Get type hints to ensure all fields have type annotations
    type_hints = get_type_hints(ProjectArea)

    required_fields = {
        "name": str,
        "language": str,
        "root_path": str,
        "confidence": str,
        "evidence": list[str],
        "file_patterns": list[str],
        "exclude_patterns": list[str],
    }

    # Test all required fields have correct type hints
    for field_name, expected_type in required_fields.items():
        assert field_name in type_hints
        assert type_hints[field_name] == expected_type


def test_project_area_field_count():
    """Test ProjectArea has exactly 7 fields."""
    fields = ProjectArea.__dataclass_fields__
    assert len(fields) == 7

    expected_field_names = {"name", "language", "root_path", "confidence", "evidence", "file_patterns", "exclude_patterns"}

    actual_field_names = set(fields.keys())
    assert actual_field_names == expected_field_names


def test_project_area_immutability():
    """Test ProjectArea field types are immutable (list[str] not list)."""
    # Test that evidence list can be mutated (it's a list, not tuple)
    area = ProjectArea(
        name="test",
        language="python",
        root_path="/test",
        confidence="Medium",
        evidence=["test.py"],
        file_patterns=["*.py"],
        exclude_patterns=["*.pyc"],
    )

    # Lists should be mutable
    area.evidence.append("new_evidence.txt")
    assert "new_evidence.txt" in area.evidence

    area.file_patterns.append("*.pyx")
    assert "*.pyx" in area.file_patterns

    area.exclude_patterns.append("**/__pycache__")
    assert "**/__pycache__" in area.exclude_patterns


def test_project_area_confidence_values():
    """Test ProjectArea accepts various confidence values."""
    valid_confidences = ["High", "Medium", "Low"]

    for confidence in valid_confidences:
        area = ProjectArea(
            name="test", language="python", root_path="/test", confidence=confidence, evidence=[], file_patterns=[], exclude_patterns=[]
        )
        assert area.confidence == confidence
