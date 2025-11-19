#!/usr/bin/env python3
"""Pre-commit hook: Check MCP tool docstring length.

Rule: Tool class docstrings must be ≤ 10 lines.
Reason: Transmitted on every MCP connection (~1 token/word).

Usage:
    python scripts/check-tool-docstrings.py [files...]
"""

import ast
import sys
from pathlib import Path

MAX_DOCSTRING_LINES = 10
TOOL_DIRS = ["src/evolvai/tools/", "src/serena/tools/"]


def count_docstring_lines(docstring: str) -> int:
    """Count non-empty lines in docstring."""
    if not docstring:
        return 0
    lines = [line.strip() for line in docstring.split("\n") if line.strip()]
    return len(lines)


def check_file(file_path: Path) -> list[str]:
    """Check if file contains Tool classes with long docstrings.

    Returns:
        List of error messages (empty if no violations)

    """
    errors = []

    try:
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=str(file_path))
    except SyntaxError:
        # Skip files with syntax errors (will be caught by other tools)
        return []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        # Check if class inherits from Tool
        is_tool = any(
            (isinstance(base, ast.Name) and base.id == "Tool")
            or (isinstance(base, ast.Attribute) and base.attr == "Tool")
            for base in node.bases
        )

        if not is_tool:
            continue

        # Check docstring length
        docstring = ast.get_docstring(node)
        if docstring:
            line_count = count_docstring_lines(docstring)
            if line_count > MAX_DOCSTRING_LINES:
                errors.append(
                    f"❌ {file_path}:{node.lineno} - "
                    f"Tool class '{node.name}' docstring too long "
                    f"({line_count} lines > {MAX_DOCSTRING_LINES} lines)\n"
                    f"   💡 See CONTRIBUTING.md 'MCP Tool Guidelines' or "
                    f"src/evolvai/tools/TOOL_TEMPLATE.py"
                )

    return errors


def main(files: list[str] | None = None) -> int:
    """Check all Tool files for docstring violations.

    Args:
        files: Optional list of specific files to check.
               If None, checks all files in TOOL_DIRS.

    Returns:
        Exit code (0 = success, 1 = violations found)

    """
    if files:
        # Check specific files (from git pre-commit)
        paths = [Path(f) for f in files if f.endswith(".py")]
    else:
        # Check all Tool files
        paths = []
        for tool_dir in TOOL_DIRS:
            tool_path = Path(tool_dir)
            if tool_path.exists():
                paths.extend(tool_path.rglob("*.py"))

    all_errors = []
    for file_path in paths:
        # Skip template file
        if file_path.name == "TOOL_TEMPLATE.py":
            continue

        errors = check_file(file_path)
        all_errors.extend(errors)

    if all_errors:
        print("\n" + "=" * 70)
        print("MCP Tool Docstring Length Violations")
        print("=" * 70 + "\n")
        for error in all_errors:
            print(error)
        print("\n" + "=" * 70)
        print("📚 Documentation:")
        print("   - Rule: Class docstring ≤ 10 lines")
        print("   - Guide: docs/guides/tool-usage.md")
        print("   - Template: src/evolvai/tools/TOOL_TEMPLATE.py")
        print("   - Why: Transmitted on every MCP connection (token waste)")
        print("=" * 70 + "\n")
        return 1

    if paths:
        print(f"✅ All {len(paths)} Tool files have compliant docstrings")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] if len(sys.argv) > 1 else None))
