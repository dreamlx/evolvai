"""Test cases for AreaDetector class."""

import inspect
from typing import get_type_hints

import pytest

from evolvai.detector.area_detector import AreaDetector


def test_area_detector_interface():
    """Test AreaDetector has required methods and attributes."""
    detector = AreaDetector("/tmp/test")

    # Test class docstring
    assert detector.__class__.__doc__ is not None
    assert "zero-cost" in detector.__class__.__doc__.lower()

    # Test method exists with correct signature
    assert hasattr(detector, "detect_areas")
    assert callable(getattr(detector, "detect_areas"))

    # Test attributes exist
    assert hasattr(detector, "project_root")
    assert hasattr(detector, "cache")
    assert detector.project_root == "/tmp/test"
    assert isinstance(detector.cache, dict)


def test_area_detector_initialization():
    """Test AreaDetector initialization with different project roots."""
    # Test with absolute path
    detector1 = AreaDetector("/absolute/path")
    assert detector1.project_root == "/absolute/path"
    assert detector1.cache == {}

    # Test with relative path
    detector2 = AreaDetector("relative/path")
    assert detector2.project_root == "relative/path"
    assert detector2.cache == {}

    # Test with root path
    detector3 = AreaDetector("/")
    assert detector3.project_root == "/"
    assert detector3.cache == {}


def test_detect_areas_signature():
    """Test detect_areas method signature."""
    detector = AreaDetector("/tmp")

    # Get method signature
    method = getattr(detector, "detect_areas")
    signature = inspect.signature(method)

    # Test parameter exists with default value
    assert "sample_limit" in signature.parameters
    sample_limit_param = signature.parameters["sample_limit"]
    assert sample_limit_param.default == 200
    assert sample_limit_param.annotation is int

    # Test return type annotation
    return_annotation = signature.return_annotation
    # Should be list[ProjectArea] but we can't import ProjectArea yet
    # so we check for basic list type
    assert hasattr(return_annotation, "__origin__")
    assert return_annotation.__origin__ is list


def test_detect_areas_not_implemented():
    """Test detect_areas raises NotImplementedError."""
    detector = AreaDetector("/tmp")

    with pytest.raises(NotImplementedError):
        detector.detect_areas()


def test_detect_areas_with_custom_limit():
    """Test detect_areas accepts custom sample_limit."""
    detector = AreaDetector("/tmp")

    with pytest.raises(NotImplementedError):
        detector.detect_areas(sample_limit=100)


def test_area_detector_type_annotations():
    """Test AreaDetector has proper type annotations."""
    # Get type hints for the class
    type_hints = get_type_hints(AreaDetector.__init__)

    # Test project_root parameter type
    assert "project_root" in type_hints
    assert type_hints["project_root"] is str

    # Test cache attribute type (should be inferred from __init__)
    detector = AreaDetector("/test")
    assert isinstance(detector.cache, dict)


def test_area_detector_cache_isolation():
    """Test each AreaDetector instance has isolated cache."""
    detector1 = AreaDetector("/test1")
    detector2 = AreaDetector("/test2")

    # Caches should be separate
    assert detector1.cache is not detector2.cache
    assert detector1.cache == {}
    assert detector2.cache == {}

    # Modifying one shouldn't affect the other
    detector1.cache["test"] = "value"
    assert detector1.cache == {"test": "value"}
    assert detector2.cache == {}
