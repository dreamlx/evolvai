# MCP Interface Extensions - 函数调用形态优化设计

**Purpose**: 高质量、LLM友好的MCP接口设计，支持智能参数优化和可观测反馈

## 🎯 设计原则

1. **函数调用形态优先**: 暴露清晰的JSON Schema函数接口
2. **高质量Examples**: 提供丰富的正例和负例
3. **字段间依赖**: 明确参数间的逻辑关系
4. **可观测反馈**: 区分错误类型并提供修复建议
5. **调用预算管理**: 编排层约束和降级策略

## 🏗️ 通用接口模式

### Enhanced Tool Schema Template

```json
{
  "name": "safe_<tool_name>",
  "description": "<LLM-friendly description with clear value proposition>",
  "parameters": {
    "type": "object",
    "properties": {
      "<primary_param>": {
        "type": "<type>",
        "description": "<Clear description with context>",
        "examples": [<positive examples>],
        "negative_examples": [<anti-patterns>],
        "validation_hints": [<common pitfalls to avoid>]
      },
      "optimization_hints": {
        "type": "object",
        "description": "LLM optimization guidance parameters",
        "properties": {
          "complexity_estimate": {
            "type": "string",
            "enum": ["simple", "medium", "complex"],
            "description": "LLM's assessment of operation complexity"
          },
          "scope_preference": {
            "type": "string",
            "enum": ["conservative", "balanced", "aggressive"],
            "description": "Risk tolerance for the operation"
          }
        }
      },
      "execution_constraints": {
        "type": "object",
        "description": "Runtime constraints (LLM will optimize based on context)",
        "properties": {
          "<constraint_name>": {
            "type": "<type>",
            "description": "<Constraint description>",
            "field_dependencies": {
              "<dependency_field>": {
                "<dependency_value>": {"default": <optimized_default>}
              }
            }
          }
        }
      }
    },
    "required": ["<essential_params>"]
  },
  "examples": [
    {
      "name": "<Descriptive scenario name>",
      "parameters": {...},
      "expected_outcome": "<What LLM should expect>",
      "optimization_notes": "<Why these parameters work well>"
    }
  ],
  "negative_examples": [
    {
      "name": "<Anti-pattern name>",
      "parameters": {...},
      "error_reason": "<Why this fails>",
      "fix_suggestion": "<How to correct>"
    }
  ],
  "error_handling": {
    "error_types": {
      "invalid_parameters": {
        "description": "Parameter validation failed",
        "common_causes": ["Missing required fields", "Invalid value types"],
        "fix_patterns": ["Use valid examples as template", "Check field dependencies"]
      },
      "permission_denied": {
        "description": "Access or execution not permitted",
        "common_causes": ["File system permissions", "Security constraints"],
        "fix_patterns": ["Check file permissions", "Use alternative approach"]
      },
      "business_conflict": {
        "description": "Operation violates business rules",
        "common_causes": ["Scope too broad", "Impact too large"],
        "fix_patterns": ["Reduce scope", "Break into smaller operations"]
      },
      "temporary_error": {
        "description": "Transient system issues",
        "common_causes": ["Resource temporarily unavailable", "Network issues"],
        "fix_patterns": ["Retry after delay", "Use alternative method"]
      }
    }
  }
}
```

## 📊 错误分类和反馈系统

### Error Type Hierarchy

```python
class ExecutionErrorType(Enum):
    """执行错误类型分类"""

    INVALID_PARAMETERS = "invalid_parameters"
    """参数无效 - Schema验证失败、类型错误、缺失必需字段"""

    PERMISSION_DENIED = "permission_denied"
    """权限不足 - 文件系统权限、安全策略、访问控制"""

    BUSINESS_CONFLICT = "business_conflict"
    """业务冲突 - 范围过大、影响过广、违反约束"""

    TEMPORARY_ERROR = "temporary_error"
    """暂时性错误 - 资源暂时不可用、网络问题、系统过载"""

@dataclass
class FixSuggestion:
    """修复建议"""
    summary: str  # 精简总结
    code_example: Optional[str]  # 可复制的代码示例
    alternative_approach: Optional[str]  # 替代方案
    confidence: float  # 修复成功率 0-1

@dataclass
class ExecutionFeedback:
    """执行反馈"""
    success: bool
    error_type: Optional[ExecutionErrorType] = None
    error_message: Optional[str] = None
    fix_suggestion: Optional[FixSuggestion] = None
    optimization_applied: Optional[dict] = None
    performance_metrics: Optional[dict] = None
    retry_recommendation: Optional[bool] = None
```

### Feedback Examples

```python
# 参数无效示例
ExecutionFeedback(
    success=False,
    error_type=ExecutionErrorType.INVALID_PARAMETERS,
    error_message="Query pattern '.*' is too broad for safe_search",
    fix_suggestion=FixSuggestion(
        summary="Use more specific search pattern",
        code_example='safe_search(query="find getUserData function", scope_hint="src/")',
        alternative_approach="Search specific file types or directories",
        confidence=0.9
    )
)

# 业务冲突示例
ExecutionFeedback(
    success=False,
    error_type=ExecutionErrorType.BUSINESS_CONFLICT,
    error_message="Edit operation would affect 150 files, exceeds safe limit of 20",
    fix_suggestion=FixSuggestion(
        summary="Reduce edit scope or increase limits explicitly",
        code_example='safe_edit(pattern="TODO", max_files=50, max_changes=100)',
        alternative_approach="Break into multiple smaller edit operations",
        confidence=0.8
    )
)
```

## 🎛️ 编排层调用预算管理

### Budget Manager Design

```python
@dataclass
class ExecutionBudget:
    """执行预算配置"""
    max_steps: int = 50  # 最大执行步数
    max_concurrent: int = 5  # 最大并发数
    max_cost_tokens: int = 100000  # 最大token消耗
    timeout_seconds: int = 300  # 总执行超时

class BudgetManager:
    """调用预算管理器"""

    def check_budget(self, operation: dict) -> BudgetCheckResult:
        """检查操作是否符合预算约束"""

    def suggest_optimization(self, operation: dict, budget_state: BudgetState) -> OptimizationSuggestion:
        """建议优化策略以符合预算"""

    def apply_degradation_strategy(self, operation: dict) -> DegradedOperation:
        """应用降级策略（只读或摘要模式）"""

class DegradationStrategy(Enum):
    """降级策略"""
    READ_ONLY = "read_only"  # 切换到只读操作
    SUMMARY_MODE = "summary_mode"  # 摘要模式
    REDUCED_SCOPE = "reduced_scope"  # 减少范围
    INCREASED_TIMEOUT = "increased_timeout"  # 增加超时时间
```

### Integration with Safe Tools

```python
class SafeToolWithBudget:
    """集成预算管理的安全工具"""

    def __init__(self, tool: Tool, budget_manager: BudgetManager):
        self.tool = tool
        self.budget_manager = budget_manager

    def execute_with_budget(self, **kwargs) -> ExecutionResult:
        """带预算约束的执行"""

        # 1. 预算检查
        budget_check = self.budget_manager.check_budget(kwargs)
        if not budget_check.within_budget:
            # 2. 应用优化建议
            optimization = self.budget_manager.suggest_optimization(kwargs, budget_check.state)
            if optimization.auto_applicable:
                kwargs.update(optimization.parameters)
            else:
                # 3. 应用降级策略
                degraded = self.budget_manager.apply_degradation_strategy(kwargs)
                return self.execute_degraded(degraded)

        # 4. 正常执行
        return self.execute_normal(**kwargs)
```

## 🔗 LLM可学习性设计

### Parameter Dependency Learning

```json
{
  "field_dependencies": {
    "query": {
      "simple_pattern": {
        "max_files": {"default": 25, "max": 50},
        "timeout_seconds": {"default": 10}
      },
      "complex_regex": {
        "max_files": {"default": 100, "max": 500},
        "timeout_seconds": {"default": 30}
      },
      "file_type_specific": {
        "max_files": {"default": 50, "max": 200},
        "file_types": {"suggested": ["*.py", "*.js", "*.ts"]}
      }
    },
    "scope_hint": {
      "current_directory": {
        "max_files": {"default": 20}
      },
      "entire_project": {
        "max_files": {"default": 200},
        "timeout_seconds": {"default": 60}
      }
    }
  },
  "learning_patterns": {
    "successful_calls": [
      {
        "pattern": "find specific function",
        "parameters": {"max_files": 30, "timeout_seconds": 15},
        "success_rate": 0.95
      }
    ],
    "failed_calls": [
      {
        "pattern": "broad regex search",
        "parameters": {"max_files": 1000},
        "failure_reason": "timeout_exceeded",
        "fix_applied": {"max_files": 100, "timeout_seconds": 30}
      }
    ]
  }
}
```

## 🎯 实施优先级

### Phase 2.1: safe_search (当前任务)
- ✅ 基础LLM参数优化
- ✅ 智能scope分析
- ✅ 高质量MCP Schema
- ✅ 错误分类反馈

### Phase 2.2: safe_edit (后续)
- 🔄 Impact评估算法
- 🔄 编辑复杂度分析
- 🔄 回滚策略集成

### Phase 2.3: safe_exec (最后)
- ⏳ 危险命令检测
- ⏳ 权限验证集成
- ⏳ 执行环境隔离

---

**Next Step**: 基于这个设计开始 Feature 2.1 的 TDD 实现