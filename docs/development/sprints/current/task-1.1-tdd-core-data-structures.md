# Task 1.1 TDD Document - Core Data Structures Definition

**Task ID**: TASK-2.1.1.1
**Feature**: FEATURE-004 (safe_search wrapper)
**Cycle**: Cycle 1 (AreaDetector + 哨兵文件检测)
**Date**: 2025-10-30
**Status**: Ready for TDD Implementation
**Estimate**: 0.2 person-day (1.6 hours)

---

## 📋 Task Overview

### Objective
Define the core data structures for AreaDetector component, providing the foundation for intelligent project area detection with sentinel file matching.

### Strategic Context
This task establishes the data models needed for:
- **Project Area Representation**: Standardized area description
- **Sentinel File Configuration**: Language-specific file patterns
- **Detection Results**: Structured output for query routing
- **Type Safety**: Full mypy compliance

---

## 🎯 Acceptance Criteria (Specific & Measurable)

### 1. ProjectArea Data Class
**✅ Requirement**: Complete dataclass with 7 required fields
```python
@dataclass
class ProjectArea:
    name: str              # Area identifier (e.g., "backend-go")
    language: str          # Language name (e.g., "go", "typescript")
    root_path: str         # Absolute path to area root
    confidence: str        # "High", "Medium", or "Low"
    evidence: list[str]     # Supporting evidence list
    file_patterns: list[str] # Include glob patterns
    exclude_patterns: list[str] # Exclude glob patterns
```

**Verification Tests**:
```python
def test_project_area_completeness():
    """Test ProjectArea has all required fields"""
    area = ProjectArea(
        name="backend-go",
        language="go",
        root_path="/tmp/backend",
        confidence="High",
        evidence=["go.mod", "cmd/"],
        file_patterns=["backend/**/*.go"],
        exclude_patterns=["backend/vendor/**"]
    )
    assert area.name == "backend-go"
    assert area.language == "go"
    # ... verify all 7 fields accessible

def test_project_area_type_safety():
    """Test ProjectArea field types"""
    # Test type annotations exist for all fields
    # Test mypy passes without errors
```

### 2. AreaDetector Class Framework
**✅ Requirement**: Complete class with detect_areas method signature
```python
class AreaDetector:
    """Zero-cost mixed project area detection."""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.cache: dict[str, list[ProjectArea]] = {}

    def detect_areas(self, sample_limit: int = 200) -> list[ProjectArea]:
        """Detect project areas using multi-layer pipeline."""
        raise NotImplementedError
```

**Verification Tests**:
```python
def test_area_detector_interface():
    """Test AreaDetector has required methods"""
    detector = AreaDetector("/tmp/test")

    # Test method exists with correct signature
    assert hasattr(detector, "detect_areas")
    assert callable(getattr(detector, "detect_areas"))

    # Test attributes exist
    assert hasattr(detector, "project_root")
    assert hasattr(detector, "cache")
    assert detector.project_root == "/tmp/test"
    assert isinstance(detector.cache, dict)

def test_detect_areas_signature():
    """Test detect_areas method signature"""
    detector = AreaDetector("/tmp")

    # Should accept no arguments (using default sample_limit)
    # Should accept optional sample_limit argument
    # Should return list[ProjectArea] type annotation
```

### 3. Sentinel File Configuration
**✅ Requirement**: Complete configuration for 4 languages with specific patterns
```python
SENTINEL_PATTERNS: dict[str, list[str]] = {
    "go": [
        "go.mod",        # Go modules (highest priority)
        "Makefile",      # Build systems
        "CMakeLists.txt" # CMake for Go
    ],
    "ruby": [
        "Gemfile",         # Ruby dependencies
        "*.gemspec",       # Gem specifications
        "Rakefile",        # Build tasks
        ".ruby-version"    # Ruby version
    ],
    "typescript": [
        "package.json",    # Node.js dependencies
        "tsconfig.json"    # TypeScript configuration
    ],
    "python": [
        "pyproject.toml",  # Modern Python projects
        "requirements.txt", # Pip requirements
        "setup.py"         # Legacy setup
    ]
}
```

**Verification Tests**:
```python
def test_sentinel_patterns_completeness():
    """Test sentinel patterns cover 4 languages"""
    from evolvai.detector.area_detector import SENTINEL_PATTERNS

    required_languages = {"go", "ruby", "typescript", "python"}
    assert set(SENTINEL_PATTERNS.keys()) == required_languages

    # Each language has at least 2 patterns
    for language, patterns in SENTINEL_PATTERNS.items():
        assert len(patterns) >= 2
        assert all(isinstance(p, str) for p in patterns)

def test_go_pattern_specificity():
    """Test Go patterns include critical files"""
    assert "go.mod" in SENTINEL_PATTERNS["go"]
    assert "Makefile" in SENTINEL_PATTERNS["go"]

def test_ruby_pattern_specificity():
    """Test Ruby patterns include critical files"""
    assert "Gemfile" in SENTINEL_PATTERNS["ruby"]
    assert "*.gemspec" in SENTINEL_PATTERNS["ruby"]

def test_typescript_pattern_specificity():
    """Test TypeScript patterns include critical files"""
    assert "package.json" in SENTINEL_PATTERNS["typescript"]
    assert "tsconfig.json" in SENTINEL_PATTERNS["typescript"]

def test_python_pattern_specificity():
    """Test Python patterns include critical files"""
    assert "pyproject.toml" in SENTINEL_PATTERNS["python"]
    assert "requirements.txt" in SENTINEL_PATTERNS["python"]
```

### 4. Type Safety Compliance
**✅ Requirement**: 100% mypy compliance with strict mode
- All public methods have type annotations
- All dataclasses use proper type hints
- No `Any` types in public interfaces
- mypy `--strict` mode passes without errors

**Verification Tests**:
```bash
# Type checking commands that must pass
mypy src/evolvai/detector/area_detector.py --strict
mypy src/evolvai/detector/models.py --strict
```

```python
def test_type_annotations_complete():
    """Test all public interfaces have type annotations"""
    import inspect
    from evolvai.detector.area_detector import AreaDetector
    from evolvai.detector.models import ProjectArea

    # Check AreaDetector methods
    for name, method in inspect.getmembers(AreaDetector, predicate=inspect.ismethod):
        if not name.startswith('_'):
            signature = inspect.signature(method)
            # Should have type annotations for return and parameters
            assert signature.return_annotation != inspect.Signature.empty

    # Check ProjectArea fields
    fields = ProjectArea.__dataclass_fields__
    for field_name, field_info in fields.items():
        # All fields should have type annotations
        assert field_info.type != type

def test_no_any_types():
    """Test no Any types in public interfaces"""
    import ast
    from evolvai.detector.area_detector import AreaDetector
    from evolvai.detector.models import ProjectArea

    # Parse source code to check for Any types
    area_detector_source = inspect.getsource(AreaDetector.__class__)
    project_area_source = inspect.getsource(ProjectArea)

    for source in [area_detector_source, project_area_source]:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "Any":
                # Allow Any in docstrings but not in type annotations
                # This is simplified; should check context in real implementation
                continue
```

---

## 🔄 TDD Implementation Plan

### 🔴 Phase 1: Red (Write Tests First)
**Duration**: 0.8 hours

**Test File Structure**:
```
test/evolvai/detector/
├── __init__.py
├── test_project_area.py     # ProjectArea dataclass tests
├── test_area_detector.py    # AreaDetector class tests
└── test_sentinel_patterns.py # Configuration tests
```

**Test Implementation Order**:
1. Create test file structure
2. Implement ProjectArea completeness tests
3. Implement AreaDetector interface tests
4. Implement sentinel pattern specification tests
5. Implement type safety tests

**Expected Failure**: All tests should fail initially (Red phase)

### 🟢 Phase 2: Green (Minimal Implementation)
**Duration**: 0.5 hours

**Implementation Order**:
1. Create `src/evolvai/detector/models.py` with ProjectArea dataclass
2. Create `src/evolvai/detector/area_detector.py` with AreaDetector class framework
3. Create SENTINEL_PATTERNS configuration
4. Add type annotations to all public interfaces
5. Ensure basic mypy compliance

**Success Criteria**: All tests pass, no functionality beyond test requirements

### 🟡 Phase 3: Refactor (Code Quality)
**Duration**: 0.3 hours

**Refactoring Checklist**:
- ✅ Code formatting with `uv run poe format`
- ✅ Type checking with `uv run poe type-check`
- ✅ Add comprehensive docstrings
- ✅ Remove any code not required by tests
- ✅ Final test suite run: `pytest test/evolvai/detector/ -v`
- ✅ Coverage check: `pytest --cov=src/evolvai/detector/`

---

## 📁 File Structure

### New Files Required
```
src/evolvai/detector/
├── __init__.py
├── models.py           # ProjectArea dataclass
└── area_detector.py    # AreaDetector class

test/evolvai/detector/
├── __init__.py
├── test_models.py           # ProjectArea tests
├── test_area_detector.py    # AreaDetector tests
└── test_sentinel_patterns.py # Configuration tests
```

### Import Dependencies
```python
# External dependencies
from dataclasses import dataclass
from typing import Dict, List

# Internal dependencies
# None for this task (pure data structures)
```

---

## 🎯 Quality Gates

### Pre-Commit Checklist
1. ✅ All tests pass: `pytest test/evolvai/detector/`
2. ✅ Type checking passes: `uv run poe type-check`
3. ✅ Code formatted: `uv run poe format`
4. ✅ Coverage ≥95%: `pytest --cov=src/evolvai/detector/`
5. ✅ No linting errors: `uv run poe lint`

### Success Metrics
- ✅ 4 test files created with 15+ test cases
- ✅ 100% test pass rate
- ✅ 0 mypy errors in strict mode
- ✅ 95%+ code coverage
- ✅ Implementation time ≤1.6 hours

---

## 🚀 Next Steps

After Task 1.1 completion:
1. 🔄 **Task 1.2**: Sentinel File Detection Implementation
2. 🔄 **Task 1.3**: Lightweight Sampling Implementation
3. 🔄 **Task 1.4**: Caching and Integration

---

**Document Status**: [READY] - Approved for TDD implementation
**Implementation Start**: After user confirmation
**Last Updated**: 2025-10-30
**Next Review**: Post Task 1.1 completion