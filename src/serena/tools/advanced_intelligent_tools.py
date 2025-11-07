"""
Advanced Intelligent Tools - Complete AI Tool Optimization System

These tools provide the complete integration of Serena's intelligent memory system
for optimal AI tool usage, command generation, and code creation.
"""

import json
from typing import Any, Optional

from serena.memory.intelligent_memory import SerenaIntelligentMemory
from serena.tools import Tool


class OptimizeAIToolsTool(Tool):
    """
    Comprehensive AI tool optimization using Serena's intelligent memory.

    This tool coordinates environment preferences, coding standards, and learned patterns
    to provide optimal AI tool recommendations and configurations.
    """

    def get_name(self) -> str:
        """Override default conversion to fix AI naming issue."""
        return "optimize_ai_tools"

    def apply(self, operation: str, context: Optional[dict[str, Any]] = None) -> str:
        """
        Get optimal AI tool configuration for the operation.

        Args:
            operation: Description of the desired operation or task
            context: Optional additional context (file_path, language, etc.)

        Returns:
            Optimized configuration for AI tools

        """
        if context is None:
            context = {}

        intelligent_memory = SerenaIntelligentMemory(self.project.project_root)

        # Get optimal configuration
        config = intelligent_memory.get_optimal_configuration(operation, context)

        # Generate recommendations
        recommendations = self._generate_recommendations(operation, config, intelligent_memory)

        return json.dumps(
            {
                "operation": operation,
                "optimal_configuration": config,
                "recommendations": recommendations,
                "message": "Optimized configuration generated using Serena's intelligent memory",
            },
            indent=2,
        )

    def _generate_recommendations(
        self, operation: str, config: dict[str, Any], intelligent_memory: SerenaIntelligentMemory
    ) -> dict[str, Any]:
        """Generate specific recommendations based on operation and configuration."""
        recommendations: dict[str, Any] = {"environment_optimizations": [], "coding_standards": [], "tool_suggestions": []}

        # Environment optimizations
        env_config = config["environment"]
        if env_config["python_manager"] == "uv":
            recommendations["environment_optimizations"].append(
                {
                    "type": "command_generation",
                    "suggestion": "Use 'uv run poe test' instead of 'pytest' for better compatibility",
                    "reason": "Detected uv environment manager",
                }
            )

        if env_config["shell"] == "zsh":
            recommendations["environment_optimizations"].append(
                {
                    "type": "shell_compatibility",
                    "suggestion": "Ensure commands are zsh-compatible",
                    "reason": "Detected zsh shell environment",
                }
            )

        # Coding standards
        standards_config = config["coding_standards"]
        if standards_config["naming_convention"]:
            recommendations["coding_standards"].append(
                {
                    "type": "naming_convention",
                    "convention": standards_config["naming_convention"],
                    "domain": standards_config["domain"],
                    "suggestion": f"Apply {standards_config['naming_convention']} naming for {standards_config['domain']} code",
                }
            )

        # Tool suggestions based on operation
        operation_lower = operation.lower()
        if "test" in operation_lower:
            recommendations["tool_suggestions"].append(
                {
                    "type": "test_framework",
                    "suggestion": "Use pytest with appropriate test discovery patterns",
                    "optimization": "Configure test runner based on project structure",
                }
            )

        if "format" in operation_lower:
            recommendations["tool_suggestions"].append(
                {
                    "type": "code_formatting",
                    "suggestion": "Use ruff + black for consistent formatting",
                    "optimization": "Format before commits for clean history",
                }
            )

        return recommendations


class GenerateOptimizedCodeTool(Tool):
    """
    Generate code optimized for the project's standards and environment.

    This tool uses all learned preferences to generate code that matches
    the project's established conventions and works with the user's environment.
    """

    def apply(self, request: str, language: str, file_context: Optional[str] = None) -> str:
        """
        Generate optimized code based on request and learned preferences.

        Args:
            request: Description of the code to generate
            language: Programming language
            file_context: Optional file path for domain detection

        Returns:
            Generated code with applied optimizations

        """
        intelligent_memory = SerenaIntelligentMemory(self.project.project_root)

        # Build context for code generation
        context = {
            "language": language,
            "file_path": file_context or "",
            "request": request,
        }

        # Get optimal configuration
        config = intelligent_memory.get_optimal_configuration(request, context)

        # Generate placeholder code (in practice, this would use AI models)
        generated_code = self._generate_placeholder_code(request, language, config)

        # Apply coding standards
        optimized_code = intelligent_memory.apply_coding_standards(generated_code, context)

        # Learn from this interaction
        intelligent_memory.learn_from_interaction(
            request, context, {"success": True, "configuration": config, "code_generated": optimized_code}
        )

        return json.dumps(
            {
                "request": request,
                "language": language,
                "generated_code": optimized_code,
                "applied_optimizations": {
                    "environment": config["environment"],
                    "coding_standards": config["coding_standards"],
                    "learned_preferences": config["learned_preferences"],
                },
                "message": "Code generated with Serena's intelligent optimizations",
            },
            indent=2,
        )

    def _generate_placeholder_code(self, request: str, language: str, config: dict[str, Any]) -> str:
        """Generate placeholder code based on request and configuration."""
        # This is a simplified placeholder - in practice, you'd integrate with AI models
        request_lower = request.lower()

        if language == "python":
            if "function" in request_lower:
                # Apply naming convention
                func_name = "example_function"
                naming_convention = config["coding_standards"].get("naming_convention")
                if naming_convention == "snake_case":
                    func_name = "example_function"
                elif naming_convention == "camelCase":
                    func_name = "exampleFunction"

                return f"""def {func_name}():
    \"\"\"
    Generated function based on: {request}
    Optimized for project coding standards.
    \"\"\"
    # TODO: Implement function logic
    pass"""

            elif "class" in request_lower:
                class_name = "ExampleClass"
                naming_convention = config["coding_standards"].get("naming_convention")
                if naming_convention == "snake_case":
                    class_name = "ExampleClass"  # Classes are PascalCase even with snake_case
                elif naming_convention == "camelCase":
                    class_name = "ExampleClass"

                return f"""class {class_name}:
    \"\"\"
    Generated class based on: {request}
    Optimized for project coding standards.
    \"\"\"
    def __init__(self):
        # TODO: Initialize attributes
        pass"""

        elif language == "javascript":
            if "function" in request_lower:
                func_name = "exampleFunction"
                naming_convention = config["coding_standards"].get("naming_convention")
                if naming_convention == "camelCase":
                    func_name = "exampleFunction"
                elif naming_convention == "snake_case":
                    func_name = "example_function"

                return f"""function {func_name}() {{
    /**
     * Generated function based on: {request}
     * Optimized for project coding standards.
     */
    // TODO: Implement function logic
}}"""

        return f"""// Generated code for: {request}
// Language: {language}
// Optimized with Serena intelligent memory
// TODO: Implement actual code generation logic"""


class ShowIntelligentMemoryStatusTool(Tool):
    """
    Show comprehensive status of Serena's intelligent memory system.

    This tool displays all learned preferences, configurations, and optimization
    capabilities that Serena has developed for the project.
    """

    def apply(self) -> str:
        """
        Show comprehensive intelligent memory status.
        """
        intelligent_memory = SerenaIntelligentMemory(self.project.project_root)
        summary = intelligent_memory.get_memory_summary()

        return json.dumps(
            {
                "intelligent_memory_status": summary,
                "capabilities": {
                    "environment_optimization": "Shell, Python, Node.js preferences learned",
                    "coding_standards": "Naming conventions and style preferences applied",
                    "adaptive_learning": "Continuous improvement from user interactions",
                    "project_context": "Domain-aware code generation and tool selection",
                },
                "optimization_examples": {
                    "command_generation": "'run tests' → 'uv run poe test' (if uv detected)",
                    "code_generation": "Python functions → snake_case naming (if backend detected)",
                    "tool_selection": "Symbol tools preferred for large codebases",
                    "style_application": "Project-specific formatting rules applied",
                },
                "message": "Serena's intelligent memory is actively optimizing AI tool usage",
            },
            indent=2,
        )


class ResetIntelligentMemoryTool(Tool):
    """
    Reset Serena's intelligent memory system.

    This tool allows clearing all learned preferences for testing
    or starting fresh with new project patterns.
    """

    def apply(self, confirm: str = "false") -> str:
        """
        Reset intelligent memory system.

        Args:
            confirm: Must be "true" to confirm the reset operation

        """
        if confirm.lower() != "true":
            return json.dumps(
                {
                    "status": "reset_cancelled",
                    "message": "Reset cancelled. Set confirm='true' to proceed with reset.",
                    "warning": "This will clear all learned environment preferences, coding standards, and learning cache.",
                },
                indent=2,
            )

        intelligent_memory = SerenaIntelligentMemory(self.project.project_root)
        intelligent_memory.clear_all_memory()

        return json.dumps(
            {
                "status": "reset_completed",
                "message": "All intelligent memory has been cleared.",
                "next_steps": "Serena will start learning new patterns from your next interactions.",
            },
            indent=2,
        )
