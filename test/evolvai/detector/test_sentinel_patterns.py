"""Test cases for SENTINEL_PATTERNS configuration."""

from evolvai.detector.area_detector import SENTINEL_PATTERNS


def test_sentinel_patterns_completeness():
    """Test sentinel patterns cover 4 languages."""
    required_languages = {"go", "ruby", "typescript", "python"}
    assert set(SENTINEL_PATTERNS.keys()) == required_languages

    # Each language has at least 2 patterns
    for language, patterns in SENTINEL_PATTERNS.items():
        assert len(patterns) >= 2
        assert all(isinstance(p, str) for p in patterns)


def test_go_pattern_specificity():
    """Test Go patterns include critical files."""
    assert "go.mod" in SENTINEL_PATTERNS["go"]
    assert "Makefile" in SENTINEL_PATTERNS["go"]
    assert "CMakeLists.txt" in SENTINEL_PATTERNS["go"]


def test_ruby_pattern_specificity():
    """Test Ruby patterns include critical files."""
    assert "Gemfile" in SENTINEL_PATTERNS["ruby"]
    assert "*.gemspec" in SENTINEL_PATTERNS["ruby"]
    assert "Rakefile" in SENTINEL_PATTERNS["ruby"]
    assert ".ruby-version" in SENTINEL_PATTERNS["ruby"]


def test_typescript_pattern_specificity():
    """Test TypeScript patterns include critical files."""
    assert "package.json" in SENTINEL_PATTERNS["typescript"]
    assert "tsconfig.json" in SENTINEL_PATTERNS["typescript"]


def test_python_pattern_specificity():
    """Test Python patterns include critical files."""
    assert "pyproject.toml" in SENTINEL_PATTERNS["python"]
    assert "requirements.txt" in SENTINEL_PATTERNS["python"]
    assert "setup.py" in SENTINEL_PATTERNS["python"]


def test_sentinel_patterns_type():
    """Test SENTINEL_PATTERNS has correct type structure."""
    assert isinstance(SENTINEL_PATTERNS, dict)
    assert all(isinstance(k, str) for k in SENTINEL_PATTERNS.keys())
    assert all(isinstance(v, list) for v in SENTINEL_PATTERNS.values())
    assert all(isinstance(p, str) for patterns in SENTINEL_PATTERNS.values() for p in patterns)


def test_sentinel_patterns_no_duplicates():
    """Test no duplicate patterns within each language."""
    for language, patterns in SENTINEL_PATTERNS.items():
        assert len(patterns) == len(set(patterns)), f"Duplicate patterns found in {language}"


def test_go_pattern_order():
    """Test Go patterns have go.mod first (highest priority)."""
    go_patterns = SENTINEL_PATTERNS["go"]
    assert go_patterns[0] == "go.mod", "go.mod should be first (highest priority)"


def test_python_modern_first():
    """Test Python patterns prioritize pyproject.toml."""
    python_patterns = SENTINEL_PATTERNS["python"]
    assert python_patterns[0] == "pyproject.toml", "pyproject.toml should be first (modern Python)"
