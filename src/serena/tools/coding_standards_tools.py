"""
Coding Standards Tools - AI Code Generation Optimization

These tools use Serena's coding standards memory to generate code that matches
user's established naming conventions and style preferences.
"""

import json
from pathlib import Path
from typing import Any, Optional

from serena.memory.coding_standards import CodingStandardsMemory
from serena.tools import Tool


class AnalyzeCodingStandardsTool(Tool):
    """
    Analyze existing codebase to learn coding standards and conventions.

    This tool examines the project's code to identify naming patterns,
    style preferences, and conventions for future AI code generation.
    """

    def apply(self, file_patterns: Optional[str] = None) -> str:
        """
        Analyze project coding standards from existing code.

        Args:
            file_patterns: Optional file patterns to focus analysis on

        """
        standards_memory = CodingStandardsMemory(self.project.project_root)
        analysis_results = {}

        # Analyze Python files
        python_analysis = self._analyze_python_standards(standards_memory)
        if python_analysis:
            analysis_results["python"] = python_analysis

        # Analyze JavaScript/TypeScript files
        js_analysis = self._analyze_javascript_standards(standards_memory)
        if js_analysis:
            analysis_results["javascript"] = js_analysis
            analysis_results["typescript"] = js_analysis

        # Detect project type patterns
        project_patterns = self._detect_project_patterns()
        if project_patterns:
            standards_memory.record_project_pattern("detected", project_patterns)
            analysis_results["project_patterns"] = project_patterns

        return json.dumps(
            {
                "status": "Coding standards analysis completed",
                "learned_patterns": analysis_results,
                "message": "Serena will use these patterns for optimized code generation",
            },
            indent=2,
        )

    def _analyze_python_standards(self, standards_memory: CodingStandardsMemory) -> Optional[dict]:
        """Analyze Python coding standards."""
        project_root = Path(self.project.project_root)
        python_files = list(project_root.rglob("*.py"))

        if not python_files:
            return None

        naming_analysis: dict[str, Any] = {"backend_snake_case": 0, "other_patterns": 0, "examples": {}}

        for py_file in python_files[:10]:  # Limit to first 10 files for efficiency
            try:
                with open(py_file, encoding="utf-8") as f:
                    content = f.read()
                    self._analyze_python_naming(content, naming_analysis, py_file.name)
            except (OSError, UnicodeDecodeError):
                continue

        # Record findings
        if naming_analysis["backend_snake_case"] > naming_analysis["other_patterns"]:
            standards_memory.record_naming_convention("python", "backend", "snake_case", naming_analysis["examples"])
        else:
            standards_memory.record_naming_convention("python", "general", "snake_case", naming_analysis["examples"])

        return naming_analysis

    def _analyze_python_naming(self, content: str, analysis: dict, filename: str) -> None:
        """Analyze naming patterns in Python code."""
        import re

        # Find function definitions
        func_matches = re.findall(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)", content)
        for func_name in func_matches[:5]:  # Limit examples
            if "_" in func_name:
                analysis["backend_snake_case"] += 1
            else:
                analysis["other_patterns"] += 1
            analysis["examples"][f"function_{func_name}"] = func_name

        # Find class definitions
        class_matches = re.findall(r"class\s+([A-Z][a-zA-Z0-9_]*)", content)
        for class_name in class_matches[:3]:
            analysis["examples"][f"class_{class_name}"] = class_name

    def _analyze_javascript_standards(self, standards_memory: CodingStandardsMemory) -> Optional[dict]:
        """Analyze JavaScript/TypeScript coding standards."""
        project_root = Path(self.project.project_root)
        js_files = list(project_root.rglob("*.js")) + list(project_root.rglob("*.jsx"))
        ts_files = list(project_root.rglob("*.ts")) + list(project_root.rglob("*.tsx"))

        all_files = js_files + ts_files
        if not all_files:
            return None

        naming_analysis: dict[str, Any] = {"frontend_camelCase": 0, "other_patterns": 0, "examples": {}}

        for js_file in all_files[:10]:  # Limit to first 10 files
            try:
                with open(js_file, encoding="utf-8") as f:
                    content = f.read()
                    self._analyze_js_naming(content, naming_analysis, js_file.name)
            except (OSError, UnicodeDecodeError):
                continue

        # Record findings
        if naming_analysis["frontend_camelCase"] > naming_analysis["other_patterns"]:
            standards_memory.record_naming_convention("javascript", "frontend", "camelCase", naming_analysis["examples"])
            standards_memory.record_naming_convention("typescript", "frontend", "camelCase", naming_analysis["examples"])

        return naming_analysis

    def _analyze_js_naming(self, content: str, analysis: dict, filename: str) -> None:
        """Analyze naming patterns in JavaScript/TypeScript code."""
        import re

        # Find function definitions
        func_matches = re.findall(r"(?:function\s+|const\s+|let\s+)([a-zA-Z_][a-zA-Z0-9_]*)\s*=", content)
        for func_name in func_matches[:5]:
            if func_name[0].isupper() or "_" in func_name:
                analysis["other_patterns"] += 1
            else:
                analysis["frontend_camelCase"] += 1
            analysis["examples"][f"function_{func_name}"] = func_name

        # Find variable names
        var_matches = re.findall(r"(?:const|let|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)", content)
        for var_name in var_matches[:5]:
            if "_" in var_name and not var_name.isupper():
                analysis["other_patterns"] += 1
            else:
                analysis["frontend_camelCase"] += 1
            analysis["examples"][f"variable_{var_name}"] = var_name

    def _detect_project_patterns(self) -> dict:
        """Detect project-specific patterns."""
        project_root = Path(self.project.project_root)
        patterns: dict[str, Any] = {}

        # Detect project structure
        if (project_root / "frontend").exists():
            patterns["has_frontend_folder"] = True
        if (project_root / "backend").exists():
            patterns["has_backend_folder"] = True
        if (project_root / "src").exists():
            patterns["has_src_folder"] = True

        # Detect framework usage
        package_json = project_root / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    content = f.read()
                    if "react" in content:
                        patterns["framework"] = "react"
                    elif "vue" in content:
                        patterns["framework"] = "vue"
                    elif "angular" in content:
                        patterns["framework"] = "angular"
            except OSError:
                pass

        return patterns


class ApplyCodingStandardsTool(Tool):
    """
    Apply learned coding standards to generated code.

    This tool transforms code to match the user's established naming
    conventions and style preferences.
    """

    def apply(self, code: str, language: str, file_context: Optional[str] = None) -> str:
        """
        Apply coding standards to code.

        Args:
            code: The code to transform
            language: Programming language (python, javascript, typescript, etc.)
            file_context: Optional file path for domain detection

        """
        standards_memory = CodingStandardsMemory(self.project.project_root)

        # Detect domain from file context
        domain = "general"
        if file_context:
            domain = standards_memory.detect_domain_from_file(file_context)

        # Apply naming conventions
        transformed_code = self._apply_naming_conventions(code, language, domain, standards_memory)

        # Apply style preferences if available
        style_preferences = standards_memory.get_style_preferences(language)
        if style_preferences:
            transformed_code = self._apply_style_preferences(transformed_code, style_preferences)

        return json.dumps(
            {
                "original_language": language,
                "detected_domain": domain,
                "transformed_code": transformed_code,
                "applied_conventions": self._get_applied_conventions(language, domain, standards_memory),
                "message": "Code transformed to match project's coding standards",
            },
            indent=2,
        )

    def _apply_naming_conventions(self, code: str, language: str, domain: str, standards_memory: CodingStandardsMemory) -> str:
        """Apply naming conventions to code."""
        convention = standards_memory.get_naming_convention(language, domain)
        if not convention:
            return code

        # This is a simplified implementation - in practice, you'd want
        # more sophisticated AST-based transformation
        lines = code.split("\n")
        transformed_lines = []

        for line in lines:
            transformed_line = self._transform_line_naming(line, convention, standards_memory)
            transformed_lines.append(transformed_line)

        return "\n".join(transformed_lines)

    def _transform_line_naming(self, line: str, convention: str, standards_memory: CodingStandardsMemory) -> str:
        """Transform naming in a single line."""
        import re

        # Simple pattern matching for function definitions
        if "def " in line:
            func_match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)", line)
            if func_match:
                func_name = func_match.group(1)
                new_name = standards_memory.apply_naming_convention(func_name, "python", "general")
                line = line.replace(f"def {func_name}", f"def {new_name}")

        # Simple pattern matching for variable assignments
        if "=" in line and not line.strip().startswith("#"):
            var_match = re.search(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=", line)
            if var_match and len(var_match.group(1)) > 2:  # Avoid single-letter vars
                var_name = var_match.group(1)
                if var_name not in ["True", "False", "None"]:  # Skip Python keywords
                    new_name = standards_memory.apply_naming_convention(var_name, "python", "general")
                    line = line.replace(f"{var_name} =", f"{new_name} =")

        return line

    def _apply_style_preferences(self, code: str, style_rules: dict) -> str:
        """Apply style preferences to code."""
        # This is a placeholder for style application
        # In practice, you'd use a formatter like black, prettier, etc.
        return code

    def _get_applied_conventions(self, language: str, domain: str, standards_memory: CodingStandardsMemory) -> dict:
        """Get information about applied conventions."""
        convention = standards_memory.get_naming_convention(language, domain)
        style_prefs = standards_memory.get_style_preferences(language)

        return {"naming_convention": convention, "style_rules_applied": bool(style_prefs)}


class ShowCodingStandardsTool(Tool):
    """
    Show current coding standards and conventions learned by Serena.

    This tool displays the coding standards that Serena has learned
    for optimizing AI code generation.
    """

    def apply(self) -> str:
        """
        Show current coding standards and conventions.
        """
        standards_memory = CodingStandardsMemory(self.project.project_root)
        summary = standards_memory.get_coding_standards_summary()

        return json.dumps(
            {
                "coding_standards": summary,
                "message": "These standards are used to optimize AI-generated code to match your project's conventions",
            },
            indent=2,
        )
