# 🎯 通用基准测试框架设计

**创建日期**: 2025-11-07
**关键洞察**: 用户发现ToolExecutionEngine是统一执行入口，可以为所有Safe Tools提供通用基准测试能力

---

## 💡 核心发现

### 用户洞察

> "safe_search需要拆分多个阶段：核心功能+使用日志+基准测试
>
> 类似情况其他工具应该也需要，但是我记得应该有一个统一工具执行入口的？"

### 关键事实

✅ **Phase 0已完成统一执行基础设施！**

```python
# src/evolvai/core/execution.py

class ToolExecutionEngine:
    """Unified tool execution engine (Phase 0完成)"""

    def __init__(self):
        self._audit_log: list[dict] = []  # 所有工具执行的审计日志

    def execute(self, tool: Tool, **kwargs) -> str:
        """所有工具调用都通过这里"""
        ctx = ExecutionContext(
            tool_name=tool.get_name(),
            start_time=time.time(),
            execution_plan=kwargs.get("execution_plan")
        )

        # 4-phase execution
        result = self._execute_tool(tool, ctx)

        # 自动记录到审计日志
        ctx.end_time = time.time()
        self._audit_log.append(ctx.to_audit_record())

        return result

    # TPST分析接口（已有！）
    def analyze_tpst(self) -> dict:
        """分析tokens/成功率/执行时间"""
        return {...}

    def get_slow_tools(self, threshold=1.0) -> list:
        """检测慢工具"""
        return [...]

    def get_audit_log(self, tool_name=None) -> list:
        """获取审计日志（可按工具过滤）"""
        return [...]
```

**关键能力**：
- ✅ **所有工具执行**都通过ToolExecutionEngine
- ✅ **自动记录审计日志**（duration, tokens, success/failure）
- ✅ **统一TPST分析接口**（analyze_tpst, get_slow_tools）
- ✅ **ExecutionContext**包含所有执行细节

---

## 🏗️ 通用基准测试架构

### 三层通用架构（适用所有Safe Tools）

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: 单元基准测试（工具特定）                     │
│ - test/evolvai/benchmarks/test_safe_search_bench.py │
│ - test/evolvai/benchmarks/test_safe_edit_bench.py   │
│ - test/evolvai/benchmarks/test_safe_exec_bench.py   │
│ - 每个工具有固定测试集                               │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: 通用使用日志系统（复用！）                   │
│ - src/evolvai/benchmarks/usage_logger.py            │
│ - src/evolvai/benchmarks/usage_replayer.py          │
│ - 所有工具共享日志格式和回放逻辑                      │
└─────────────────┬───────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: ToolExecutionEngine审计（已有！）            │
│ - execution_engine.get_audit_log("safe_search")     │
│ - execution_engine.analyze_tpst()                   │
│ - execution_engine.get_slow_tools()                 │
│ - 通用TPST分析，无需额外代码                         │
└─────────────────────────────────────────────────────┘
```

---

## 📦 Story拆分策略（Phase 2统一模式）

### 原Epic README计划（需要调整）

```
Phase 2: Safe Operations Wrapper System

Story 2.1: safe_search wrapper (4人天)
Story 2.2: safe_edit wrapper (7人天)
Story 2.3: safe_exec wrapper (3人天)
```

### 修正后的Story拆分（统一模式）

```
Story 2.1: safe_search核心功能 (4人天)
  ├─ Story 2.1.1: 单元基准测试套件 (1人天)
  └─ Story 2.1.2: MCP集成和端到端测试 (0.5人天)

Story 2.2: safe_edit核心功能 (6人天) ← 从7天减少
  ├─ Story 2.2.1: 单元基准测试套件 (1人天)
  └─ Story 2.2.2: MCP集成和端到端测试 (0.5人天)

Story 2.3: safe_exec核心功能 (3人天)
  ├─ Story 2.3.1: 单元基准测试套件 (1人天)
  └─ Story 2.3.2: MCP集成和端到端测试 (0.5人天)

Story 2.4: 通用基准测试框架 (2人天) ← 新增
  ├─ 通用使用日志系统 (UsageLogger/Replayer)
  ├─ 基准测试报告生成器
  └─ CI/CD集成和自动化回归检测
```

**总工作量**:
- 原计划: 14人天
- 修正后: 13 + 2 + 1.5 + 1.5 = **18人天**（增加了完整基准测试能力）

---

## 🔧 通用组件设计

### 1. UsageLogger（通用，所有工具共享）

```python
# src/evolvai/benchmarks/usage_logger.py

from pathlib import Path
import json
from datetime import datetime

class UsageLogger:
    """通用使用日志记录器（所有Safe Tools共享）"""

    def __init__(self, log_dir: Path = Path(".evolvai/usage_logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True

    def log_tool_execution(
        self,
        tool_name: str,
        operation: str,
        execution_time: float,
        success: bool,
        metadata: dict = None
    ):
        """记录任意工具的执行

        Args:
            tool_name: "safe_search" | "safe_edit" | "safe_exec"
            operation: 操作描述（search的query, edit的pattern等）
            execution_time: 执行时间（秒）
            success: 是否成功
            metadata: 工具特定的额外数据
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "operation": operation,
            "execution_time": execution_time,
            "success": success,
            "project_path": os.getcwd(),
            "metadata": metadata or {}
        }

        # 按日期分片（所有工具混合在一起）
        log_file = self.log_dir / f"usage_{datetime.now().date()}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
```

**关键设计**：
- ✅ 工具无关的通用接口
- ✅ 统一日志格式（所有工具混合）
- ✅ 灵活的metadata字段存储工具特定数据

### 2. UsageReplayer（通用，所有工具共享）

```python
# src/evolvai/benchmarks/usage_replayer.py

class UsageReplayer:
    """通用使用日志回放器"""

    def replay_logs(
        self,
        log_file: Path,
        tool_filter: str | None = None
    ) -> BenchmarkReport:
        """回放使用日志，评估性能变化

        Args:
            log_file: 日志文件路径
            tool_filter: 可选的工具名过滤（"safe_search" | "safe_edit" | "safe_exec"）

        Returns:
            BenchmarkReport: 包含所有工具或指定工具的性能报告
        """
        results = []

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)

                # 过滤工具（如果指定）
                if tool_filter and entry["tool"] != tool_filter:
                    continue

                # 根据工具类型分派回放
                if entry["tool"] == "safe_search":
                    new_result = self._replay_search(entry)
                elif entry["tool"] == "safe_edit":
                    new_result = self._replay_edit(entry)
                elif entry["tool"] == "safe_exec":
                    new_result = self._replay_exec(entry)
                else:
                    continue

                # 对比性能变化
                results.append({
                    "tool": entry["tool"],
                    "operation": entry["operation"],
                    "old_time": entry["execution_time"],
                    "new_time": new_result["execution_time"],
                    "change_pct": (
                        (new_result["execution_time"] - entry["execution_time"])
                        / entry["execution_time"] * 100
                    )
                })

        return BenchmarkReport(results)

    def _replay_search(self, entry: dict) -> dict:
        """重新执行search（在相同项目路径）"""
        with chdir(entry["project_path"]):
            return safe_search(
                query=entry["metadata"]["query"],
                scope=entry["metadata"]["scope"]
            )

    def _replay_edit(self, entry: dict) -> dict:
        """重新执行edit"""
        # 类似逻辑
        pass

    def _replay_exec(self, entry: dict) -> dict:
        """重新执行exec"""
        # 类似逻辑
        pass
```

**关键设计**：
- ✅ 单一回放器处理所有工具
- ✅ 可按工具类型过滤
- ✅ 统一的性能对比逻辑

### 3. BenchmarkReporter（通用报告生成）

```python
# src/evolvai/benchmarks/reporter.py

class BenchmarkReporter:
    """通用基准测试报告生成器"""

    def __init__(self, execution_engine: ToolExecutionEngine):
        self.engine = execution_engine

    def generate_weekly_report(self) -> str:
        """生成每周性能报告（所有工具）

        Returns:
            Markdown格式的报告
        """
        # 从ToolExecutionEngine获取审计日志
        audit_log = self.engine.get_audit_log()

        # 按工具分组统计
        by_tool = {}
        for record in audit_log:
            tool = record["tool"]
            if tool not in by_tool:
                by_tool[tool] = []
            by_tool[tool].append(record)

        # 生成报告
        report = ["# EvolvAI Performance Report - Week 45\n"]
        report.append(f"**Total Executions**: {len(audit_log)}\n")

        for tool_name, records in by_tool.items():
            report.append(f"\n## {tool_name}\n")
            report.append(f"- Calls: {len(records)}\n")

            durations = [r["duration"] for r in records]
            report.append(f"- P50: {self._percentile(durations, 50):.2f}s\n")
            report.append(f"- P95: {self._percentile(durations, 95):.2f}s\n")
            report.append(f"- P99: {self._percentile(durations, 99):.2f}s\n")

            success_rate = sum(r["success"] for r in records) / len(records)
            report.append(f"- Success Rate: {success_rate:.1%}\n")

        # TPST分析
        tpst = self.engine.analyze_tpst()
        report.append("\n## TPST Metrics\n")
        report.append(f"- Total Tokens: {tpst['total_tokens']}\n")
        report.append(f"- Avg Tokens: {tpst['average_tokens']:.1f}\n")
        report.append(f"- Success Rate: {tpst['success_rate']:.1%}\n")

        # 慢工具检测
        slow_tools = self.engine.get_slow_tools(threshold_seconds=1.0)
        if slow_tools:
            report.append("\n## Slow Operations (>1s)\n")
            for record in slow_tools[:10]:  # Top 10
                report.append(
                    f"- {record['tool']}: {record['duration']:.2f}s\n"
                )

        return "".join(report)
```

**关键设计**：
- ✅ 直接使用ToolExecutionEngine的审计日志
- ✅ 按工具分组统计
- ✅ 统一的性能指标（P50/P95/P99）
- ✅ TPST分析集成

---

## 📊 集成到Safe Tools的模式

### 模式1: safe_search集成（示例）

```python
# src/evolvai/tools/safe_search_wrapper.py

from evolvai.benchmarks.usage_logger import UsageLogger

class SafeSearchWrapper:
    """safe_search实现"""

    def __init__(self, agent, project):
        self.agent = agent
        self.project = project

        # 初始化使用日志记录器
        if os.getenv("EVOLVAI_LOG_USAGE") == "true":
            self.usage_logger = UsageLogger()
        else:
            self.usage_logger = None

    def safe_search(
        self,
        query: str,
        scope: str = "**/*",
        execution_plan: Optional[ExecutionPlan] = None
    ) -> SearchResult:
        """核心搜索功能"""

        start_time = time.time()

        try:
            # 1. 检测工具
            tool = self._detect_tool()

            # 2. 执行搜索
            result = self._run_search(tool, query, scope)

            execution_time = time.time() - start_time

            # 3. 记录使用日志（通用系统）
            if self.usage_logger:
                self.usage_logger.log_tool_execution(
                    tool_name="safe_search",
                    operation=query,
                    execution_time=execution_time,
                    success=True,
                    metadata={
                        "tool_used": tool,
                        "scope": scope,
                        "hits_count": result["stats"]["hits_count"]
                    }
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            # 记录失败
            if self.usage_logger:
                self.usage_logger.log_tool_execution(
                    tool_name="safe_search",
                    operation=query,
                    execution_time=execution_time,
                    success=False,
                    metadata={"error": str(e)}
                )

            raise
```

**集成要点**：
1. ✅ 初始化时创建UsageLogger实例
2. ✅ 执行时记录成功/失败
3. ✅ metadata存储工具特定数据
4. ✅ 环境变量控制开关

### 模式2: safe_edit集成（类似）

```python
# src/evolvai/tools/safe_edit_wrapper.py

class SafeEditWrapper:
    """safe_edit实现"""

    def __init__(self, agent, project):
        self.usage_logger = UsageLogger() if os.getenv("EVOLVAI_LOG_USAGE") else None

    def propose_edit(self, pattern: str, replacement: str, scope: str) -> ProposalResult:
        """生成patch"""

        start_time = time.time()

        try:
            result = self._generate_patch(pattern, replacement, scope)

            # 记录使用日志
            if self.usage_logger:
                self.usage_logger.log_tool_execution(
                    tool_name="safe_edit",
                    operation=f"propose: {pattern} → {replacement}",
                    execution_time=time.time() - start_time,
                    success=True,
                    metadata={
                        "files_matched": result["files_matched"],
                        "patch_id": result["patch_id"]
                    }
                )

            return result

        except Exception as e:
            if self.usage_logger:
                self.usage_logger.log_tool_execution(
                    tool_name="safe_edit",
                    operation=f"propose: {pattern} → {replacement}",
                    execution_time=time.time() - start_time,
                    success=False,
                    metadata={"error": str(e)}
                )
            raise
```

---

## 🎯 实施计划更新

### Phase 2新Story结构

```
┌─────────────────────────────────────────────────────┐
│ Story 2.1: safe_search核心功能 (4人天)              │
│ - 工具检测和选择（rg/ugrep/grep）                    │
│ - JSON输出结构                                      │
│ - ExecutionPlan集成                                 │
│ - BDD场景驱动TDD                                    │
│ - UsageLogger集成（复用通用系统）                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.1.1: safe_search单元基准测试 (1人天)        │
│ - 准备3个benchmark repos（small/medium/large）      │
│ - 编写10-15个基准测试用例                           │
│ - CI/CD集成和回归检测                               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.1.2: safe_search MCP集成 (0.5人天)          │
│ - SafeSearchTool（Tool基类）                        │
│ - MCP服务器注册                                     │
│ - 端到端测试                                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.2: safe_edit核心功能 (6人天)                │
│ - Patch-First架构（propose/apply）                  │
│ - Git worktree隔离                                  │
│ - ExecutionPlan集成                                 │
│ - BDD场景驱动TDD                                    │
│ - UsageLogger集成（复用通用系统）                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.2.1: safe_edit单元基准测试 (1人天)          │
│ - 基准测试用例（编辑速度、patch生成等）              │
│ - CI/CD集成                                         │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.2.2: safe_edit MCP集成 (0.5人天)            │
│ - SafeEditTool（Tool基类）                          │
│ - MCP服务器注册                                     │
│ - 端到端测试                                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.3: safe_exec核心功能 (3人天)                │
│ - 进程组管理（killpg）                              │
│ - 输出截断                                          │
│ - ExecutionPlan集成                                 │
│ - UsageLogger集成（复用通用系统）                    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.3.1: safe_exec单元基准测试 (1人天)          │
│ - 基准测试用例（命令执行速度、超时等）               │
│ - CI/CD集成                                         │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.3.2: safe_exec MCP集成 (0.5人天)            │
│ - SafeExecTool（Tool基类）                          │
│ - MCP服务器注册                                     │
│ - 端到端测试                                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ Story 2.4: 通用基准测试框架 (2人天) ⭐ 新增          │
│ Day 1:                                              │
│ - UsageLogger通用实现                               │
│ - UsageReplayer通用实现                             │
│ - BenchmarkReporter实现                             │
│ Day 2:                                              │
│ - CLI工具（evolvai-replay, evolvai-report）         │
│ - CI/CD集成（每周自动回放）                         │
│ - 文档和使用指南                                    │
└─────────────────────────────────────────────────────┘
```

**总工作量**:
- 核心功能: 4 + 6 + 3 = 13人天
- 单元基准测试: 1 + 1 + 1 = 3人天
- MCP集成: 0.5 + 0.5 + 0.5 = 1.5人天
- 通用框架: 2人天
- **总计: 19.5人天（约4周）**

---

## 🔄 数据流图（完整）

```
┌────────────────────────────────────────────────────┐
│ 用户调用safe_search/edit/exec                      │
└────────────────┬───────────────────────────────────┘
                 ↓
┌────────────────────────────────────────────────────┐
│ ToolExecutionEngine.execute()                      │
│ - 自动记录审计日志（duration, tokens, success）     │
│ - ExecutionContext包含完整执行细节                  │
└────────────────┬───────────────────────────────────┘
                 ↓
         ┌───────┴────────┐
         ↓                ↓
┌─────────────────┐  ┌──────────────────────┐
│ Safe Tool执行    │  │ UsageLogger记录      │
│ - 工具逻辑       │  │ - 操作描述           │
│ - 返回结果       │  │ - 性能数据           │
└─────────────────┘  │ - metadata           │
                     └──────────┬───────────┘
                                ↓
                    .evolvai/usage_logs/usage_2025-11-07.jsonl
                                ↓
┌────────────────────────────────────────────────────┐
│ 每周回放和分析                                      │
│ 1. UsageReplayer回放真实调用                        │
│ 2. 对比性能变化（old vs new）                       │
│ 3. BenchmarkReporter生成报告                        │
│ 4. ToolExecutionEngine提供TPST分析                 │
└────────────────────────────────────────────────────┘
```

---

## ✅ 关键优势

### 1. 统一性

✅ **所有工具使用相同的基准测试基础设施**
- UsageLogger: 通用日志记录
- UsageReplayer: 通用回放逻辑
- BenchmarkReporter: 统一报告格式
- ToolExecutionEngine: 内置TPST分析

### 2. 零额外开销

✅ **ToolExecutionEngine已有审计日志**
- 无需为每个工具单独实现TPST跟踪
- get_audit_log()可按工具过滤
- analyze_tpst()自动分析

### 3. 可扩展性

✅ **未来新增Safe Tools自动获得基准测试能力**
- 只需集成UsageLogger（3行代码）
- 自动记录到ToolExecutionEngine审计日志
- 自动包含在每周报告中

### 4. 一致性

✅ **所有工具的性能数据在同一个仪表板**
- 横向对比（safe_search vs safe_edit vs safe_exec）
- 纵向对比（本周 vs 上周）
- TPST统一分析

---

## 📋 修正后的Epic README更新

### Phase 2: Safe Operations Wrapper System（修正）

**总工作量**: 19.5人天（约4周）- 从14人天增加，但获得完整基准测试能力

#### Story 2.1: safe_search wrapper
- **Story ID**: STORY-2.1
- **描述**: 实现safe_search，增加scope限制和自动工具选择
- **优先级**: [P0]
- **估算**: **4人天**
- **状态**: [Backlog]
- **交付物**:
  - safe_search工具实现
  - scope限制验证
  - ripgrep/ugrep/grep自动选择逻辑
  - JSON格式输出
  - UsageLogger集成

#### Story 2.1.1: safe_search单元基准测试
- **Story ID**: STORY-2.1.1
- **描述**: 建立safe_search的单元基准测试套件
- **优先级**: [P0]
- **估算**: **1人天**
- **状态**: [Backlog]
- **交付物**:
  - 3个benchmark repos（small/medium/large）
  - 10-15个基准测试用例
  - CI/CD集成和回归检测

#### Story 2.1.2: safe_search MCP集成
- **Story ID**: STORY-2.1.2
- **描述**: 将safe_search暴露为MCP工具
- **优先级**: [P0]
- **估算**: **0.5人天**
- **状态**: [Backlog]
- **交付物**:
  - SafeSearchTool（Tool基类）
  - MCP服务器注册
  - 端到端测试

#### Story 2.2: safe_edit wrapper
- **Story ID**: STORY-2.2
- **描述**: 实现safe_edit，Patch-First架构
- **优先级**: [P0]
- **估算**: **6人天**（从7人天减少）
- **状态**: [Backlog]
- **交付物**:
  - Patch-First架构（propose/apply）
  - Git worktree隔离
  - ExecutionPlan集成
  - UsageLogger集成

#### Story 2.2.1: safe_edit单元基准测试
- **Story ID**: STORY-2.2.1
- **描述**: 建立safe_edit的单元基准测试套件
- **优先级**: [P0]
- **估算**: **1人天**
- **状态**: [Backlog]

#### Story 2.2.2: safe_edit MCP集成
- **Story ID**: STORY-2.2.2
- **描述**: 将safe_edit暴露为MCP工具
- **优先级**: [P0]
- **估算**: **0.5人天**
- **状态**: [Backlog]

#### Story 2.3: safe_exec wrapper
- **Story ID**: STORY-2.3
- **描述**: 实现safe_exec，进程组管理
- **优先级**: [P1]
- **估算**: **3人天**
- **状态**: [Backlog]
- **交付物**:
  - 进程组管理（killpg）
  - 输出截断
  - ExecutionPlan集成
  - UsageLogger集成

#### Story 2.3.1: safe_exec单元基准测试
- **Story ID**: STORY-2.3.1
- **描述**: 建立safe_exec的单元基准测试套件
- **优先级**: [P1]
- **估算**: **1人天**
- **状态**: [Backlog]

#### Story 2.3.2: safe_exec MCP集成
- **Story ID**: STORY-2.3.2
- **描述**: 将safe_exec暴露为MCP工具
- **优先级**: [P1]
- **估算**: **0.5人天**
- **状态**: [Backlog]

#### Story 2.4: 通用基准测试框架 ⭐ 新增
- **Story ID**: STORY-2.4
- **描述**: 实现通用基准测试基础设施（所有Safe Tools共享）
- **优先级**: [P0]
- **估算**: **2人天**
- **状态**: [Backlog]
- **交付物**:
  - UsageLogger通用实现
  - UsageReplayer通用实现
  - BenchmarkReporter实现
  - CLI工具（evolvai-replay, evolvai-report）
  - CI/CD集成（每周自动回放）
  - 文档和使用指南

**Phase 2总工作量**: 19.5人天（约4周）

---

## 🎯 关键决策

### 决策1: 通用vs专用基准测试框架

**选择**: ✅ 通用框架（Story 2.4）

**理由**:
1. ToolExecutionEngine已提供统一审计日志
2. 三个Safe Tools共享相同的性能监控需求
3. 代码复用减少维护成本
4. 未来新增工具自动获得基准测试能力

### 决策2: 基准测试是否必需

**选择**: ✅ 必需，纳入MVP范围

**理由**:
1. Dogfooding需要长期数据收集
2. 参数优化依赖真实使用数据
3. TPST目标验证需要基准对比
4. 2人天投入换取持续改进能力

### 决策3: Story拆分粒度

**选择**: ✅ 每个工具拆分3个Story（核心 + 基准测试 + MCP集成）

**理由**:
1. 核心功能和基准测试关注点不同
2. MCP集成是轻量级独立任务
3. 允许并行开发（不同开发者负责不同Story）
4. 更清晰的交付物和验收标准

---

## 📚 参考文档

### 已完成基础设施
- [Phase 0 Completion Report](../../sprints/current/phase-0-completion-report.md) ⭐ ToolExecutionEngine实现
- [ADR-003: 工具链路简化](../adrs/003-tool-execution-engine-simplification.md) ⭐ 统一执行架构决策

### 基准测试策略
- [Baseline Testing Strategy](../../knowledge/research/baseline-testing-strategy.md) ⭐ 完整基准测试方案
- [Preventive Analysis: safe_search](../../knowledge/preventive-analysis-safe-search.md) ⭐ safe_search预防性分析

---

**最后更新**: 2025-11-07
**关键贡献**: 用户洞察 - 发现ToolExecutionEngine统一执行能力
**下一步**: 更新Epic README，开始Story 2.1实施

---

## 💡 最终总结

### 核心价值

> **ToolExecutionEngine (Phase 0) 为所有Safe Tools提供了统一的基准测试基础设施。**
>
> **只需2人天构建通用框架（Story 2.4），三个Safe Tools自动获得完整的性能监控和优化能力。**

### 投资回报

**投入**: 2人天（Story 2.4）
**收益**:
- ✅ 所有Safe Tools的使用日志系统
- ✅ 真实使用场景的性能回放
- ✅ 统一的TPST分析和报告
- ✅ 持续监控和参数优化能力
- ✅ 未来新增工具零成本获得基准测试

**ROI**: 极高（一次投入，长期受益）
