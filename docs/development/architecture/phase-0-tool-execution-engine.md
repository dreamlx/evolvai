# Phase 0: 工具调用链路简化 - 详细设计

**版本**: v1.0
**日期**: 2025-10-27
**状态**: [APPROVED]
**优先级**: [P0] - 最高优先级

---

## 📋 概述

### 目标

将 SerenaAgent 的工具调用链路从 **7 层简化到 4 层**，为 Epic-001（行为约束系统）和 TPST 优化奠定基础。

### 核心价值

1. **清晰的审计路径**：完整的 ExecutionContext 记录每个执行环节
2. **统一的执行入口**：所有工具调用经过统一的 ToolExecutionEngine
3. **易于扩展**：Epic-001 的约束系统可以直接注入到执行引擎
4. **性能监控**：自动识别慢工具和 token 浪费

### 设计原则

- **KISS (Keep It Simple, Stupid)**: 简单通用优于复杂精确
- **Single Entry Point**: 统一执行入口，易于审计和优化
- **Feature Flag**: 渐进式启用，保持向后兼容
- **Full Audit Trail**: 完整的执行上下文，支持 TPST 分析

---

## 🏗️ 架构设计

### 简化前 vs 简化后

```
┌─────────────────────────────────────────────────────────────────────┐
│ 简化前（7 层）                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ AI Client → FastMCP → MCP Tool wrapper → Tool.apply_ex()           │
│ → SerenaAgent.execute_task() → ThreadPoolExecutor → Tool.apply()   │
│                                                                     │
│ 问题：                                                              │
│ - 链路过长，难以追踪                                                │
│ - 职责分散，难以审计                                                │
│ - 扩展困难，需要多处注入                                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ 简化后（4 层）                                                      │
├─────────────────────────────────────────────────────────────────────┤
│ AI Client → FastMCP → ToolExecutionEngine → Tool.apply()           │
│                                                                     │
│ 优势：                                                              │
│ - 链路清晰，易于追踪                                                │
│ - 职责集中，易于审计                                                │
│ - 单一入口，易于扩展                                                │
└─────────────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. ExecutionContext（执行上下文）

```python
@dataclass
class ExecutionContext:
    """
    执行上下文 - 完整的审计信息

    这是 TPST 分析的核心数据结构。
    """
    # 工具信息
    tool_name: str
    kwargs: dict[str, Any]
    execution_plan: Any | None = None

    # 时间追踪
    start_time: float = 0.0
    end_time: float = 0.0
    phase: ExecutionPhase = ExecutionPhase.PRE_VALIDATION

    # 约束检查结果（Epic-001）
    constraint_violations: list[str] | None = None
    should_batch: bool = False

    # 执行结果
    result: str | None = None
    error: Exception | None = None

    # Token 追踪（TPST 核心指标）
    estimated_tokens: int = 0
    actual_tokens: int = 0

    @property
    def duration(self) -> float:
        """执行时长（秒）"""
        return self.end_time - self.start_time

    @property
    def success(self) -> bool:
        """是否成功执行"""
        return self.error is None

    @property
    def token_estimation_accuracy(self) -> float:
        """Token 估算准确度（0-1）"""
        if self.estimated_tokens == 0:
            return 0.0
        return min(self.estimated_tokens, self.actual_tokens) / max(self.estimated_tokens, self.actual_tokens)

    def to_audit_record(self) -> dict:
        """转换为审计记录（用于 TPST 分析）"""
        return {
            'tool': self.tool_name,
            'phase': self.phase.value,
            'duration': self.duration,
            'tokens': self.actual_tokens,
            'success': self.success,
            'constraints': self.constraint_violations,
            'batched': self.should_batch,
            'estimation_accuracy': self.token_estimation_accuracy
        }
```

#### 2. ExecutionPhase（执行阶段）

```python
class ExecutionPhase(Enum):
    """执行阶段枚举"""
    PRE_VALIDATION = "pre_validation"     # 前置验证（工具激活、项目、LSP）
    PRE_EXECUTION = "pre_execution"       # 执行前处理（Epic-001 约束检查）
    EXECUTION = "execution"               # 实际执行（Tool.apply()）
    POST_EXECUTION = "post_execution"     # 执行后处理（日志、监控）
    ERROR_HANDLING = "error_handling"     # 错误处理
```

#### 3. ToolExecutionEngine（统一执行引擎）

```python
class ToolExecutionEngine:
    """
    统一工具执行引擎

    职责：
    1. 统一执行流程（4 阶段）
    2. 集成约束检查（Epic-001）
    3. 审计追踪（完整 ExecutionContext）
    4. 线程池管理（异步执行）
    5. 性能监控（慢工具、token 浪费）
    """

    def __init__(self, agent: 'SerenaAgent'):
        self.agent = agent

        # 线程池（从 SerenaAgent 移到这里）
        self._executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="ToolExecution"
        )

        # 约束引擎（Epic-001，feature flag 控制）
        self._constraints_enabled = False
        self._constraint_engine: ConstraintEngine | None = None

        # 审计追踪
        self._audit_log: list[dict] = []

        # 性能监控
        self._slow_tool_threshold = 5.0  # 5 秒
        self._token_waste_threshold = 1.2  # 实际 tokens > 估算 * 1.2

    def enable_constraints(self, constraint_engine: 'ConstraintEngine') -> None:
        """启用约束系统（feature flag）"""
        self._constraints_enabled = True
        self._constraint_engine = constraint_engine
        log.info("Constraint system enabled")

    def execute(self, tool: Tool, **kwargs) -> str:
        """
        统一执行入口（同步接口）

        这是唯一的工具执行入口，所有工具调用都经过这里。

        参数：
            tool: 要执行的工具实例
            **kwargs: 工具参数（包含 execution_plan）

        返回：
            执行结果（字符串）

        异常：
            ToolNotActiveError: 工具未激活
            ProjectRequiredError: 需要激活项目
            InvalidExecutionPlanError: ExecutionPlan 无效
            ConstraintViolationError: 违反约束
            TimeoutError: 执行超时
        """
        # 创建执行上下文
        ctx = ExecutionContext(
            tool_name=tool.get_name(),
            kwargs=kwargs.copy(),  # 复制一份，避免修改原参数
            execution_plan=kwargs.pop('execution_plan', None),
            start_time=time.time()
        )

        try:
            # Phase 1: Pre-validation
            ctx.phase = ExecutionPhase.PRE_VALIDATION
            self._pre_validation(tool, ctx)

            # Phase 2: Pre-execution (Epic-001 约束)
            if self._constraints_enabled:
                ctx.phase = ExecutionPhase.PRE_EXECUTION
                self._pre_execution_with_constraints(tool, ctx)

            # Phase 3: Execution
            ctx.phase = ExecutionPhase.EXECUTION
            ctx.result = self._execute_tool(tool, ctx)

            # Phase 4: Post-execution
            ctx.phase = ExecutionPhase.POST_EXECUTION
            self._post_execution(tool, ctx)

            return ctx.result

        except BatchExecutionCompleted:
            # 批处理已经在 pre-execution 阶段完成
            ctx.phase = ExecutionPhase.POST_EXECUTION
            self._post_execution(tool, ctx)
            return ctx.result

        except Exception as e:
            ctx.error = e
            ctx.phase = ExecutionPhase.ERROR_HANDLING
            return self._handle_error(tool, ctx)

        finally:
            ctx.end_time = time.time()
            self._audit_log.append(ctx.to_audit_record())

    def _pre_validation(self, tool: Tool, ctx: ExecutionContext) -> None:
        """
        阶段 1：前置验证

        检查：
        1. 工具是否激活
        2. 是否需要激活项目
        3. Language Server 是否运行
        """
        # 1. 检查工具是否激活
        if not tool.is_active():
            raise ToolNotActiveError(
                f"Tool '{tool.get_name()}' is not active. "
                f"Active tools: {self.agent.get_active_tool_names()}"
            )

        # 2. 检查项目（如果需要）
        if not isinstance(tool, ToolMarkerDoesNotRequireActiveProject):
            if self.agent._active_project is None:
                raise ProjectRequiredError(
                    "No active project. Ask the user to provide the project path or "
                    f"select a project from: {self.agent.serena_config.project_names}"
                )

        # 3. 检查 Language Server（如果需要）
        if self.agent.is_using_language_server():
            if not self.agent.is_language_server_running():
                log.info("Language server not running, starting...")
                self.agent.reset_language_server()

    def _pre_execution_with_constraints(self, tool: Tool, ctx: ExecutionContext) -> None:
        """
        阶段 2：执行前处理（Epic-001 约束检查）

        Feature flag 控制，默认禁用。

        检查：
        1. ExecutionPlan 验证
        2. Constitutional Constraints
        3. Batching 机会
        """
        assert self._constraint_engine is not None

        # 1. ExecutionPlan 验证
        if not self._constraint_engine.validate_plan(ctx.execution_plan):
            raise InvalidExecutionPlanError(
                f"Invalid or missing execution plan for {ctx.tool_name}"
            )

        # 2. Constitutional 约束检查
        violations = self._constraint_engine.check_constraints(tool, ctx.kwargs)
        if violations:
            ctx.constraint_violations = violations
            raise ConstraintViolationError(
                f"Constraint violations for {ctx.tool_name}: {violations}"
            )

        # 3. Batching 机会检测
        ctx.should_batch = self._constraint_engine.should_batch(tool, ctx.kwargs)
        if ctx.should_batch:
            log.info(f"Batching opportunity detected for {ctx.tool_name}")
            ctx.result = self._constraint_engine.execute_batched(tool, ctx.kwargs)
            # 提前返回，跳过正常执行
            raise BatchExecutionCompleted()

    def _execute_tool(self, tool: Tool, ctx: ExecutionContext) -> str:
        """
        阶段 3：实际执行工具

        流程：
        1. Token 估算（执行前）
        2. 提交到线程池执行
        3. 等待结果（带超时）
        4. Token 统计（执行后）
        """
        # 1. Token 估算（执行前）
        ctx.estimated_tokens = self._estimate_tokens(tool, ctx.kwargs)

        # 2. 提交到线程池执行
        future = self._executor.submit(tool.apply, **ctx.kwargs)

        # 3. 等待结果（带超时）
        timeout = self.agent.serena_config.tool_timeout
        try:
            result = future.result(timeout=timeout)
        except TimeoutError:
            log.error(f"Tool {ctx.tool_name} timed out after {timeout}s")
            raise

        # 4. Token 统计（执行后）
        ctx.actual_tokens = self._count_tokens(result)

        return result

    def _post_execution(self, tool: Tool, ctx: ExecutionContext) -> None:
        """
        阶段 4：执行后处理

        处理：
        1. 日志记录
        2. 统计上报
        3. 性能监控
        """
        # 1. 记录日志
        log.info(
            f"{ctx.tool_name}: "
            f"duration={ctx.duration:.2f}s, "
            f"tokens={ctx.actual_tokens}, "
            f"success={ctx.success}"
        )

        # 2. 记录统计（如果启用）
        if self.agent._tool_usage_stats:
            self.agent._tool_usage_stats.record(
                tool_name=ctx.tool_name,
                input_kwargs=ctx.kwargs,
                result=ctx.result,
                tokens=ctx.actual_tokens
            )

        # 3. 性能监控
        self._monitor_performance(ctx)

    def _monitor_performance(self, ctx: ExecutionContext) -> None:
        """性能监控（识别慢工具和 token 浪费）"""
        # 识别慢工具
        if ctx.duration > self._slow_tool_threshold:
            log.warning(
                f"⚠️ Slow tool detected: {ctx.tool_name} took {ctx.duration:.2f}s "
                f"(threshold: {self._slow_tool_threshold}s)"
            )

        # 识别 token 浪费
        if ctx.estimated_tokens > 0:
            if ctx.actual_tokens > ctx.estimated_tokens * self._token_waste_threshold:
                log.warning(
                    f"⚠️ Token waste detected: {ctx.tool_name} used {ctx.actual_tokens} tokens "
                    f"(estimated: {ctx.estimated_tokens}, accuracy: {ctx.token_estimation_accuracy:.1%})"
                )

    def _handle_error(self, tool: Tool, ctx: ExecutionContext) -> str:
        """统一错误处理"""
        error_msg = f"Error executing {ctx.tool_name}: {ctx.error}"
        log.error(error_msg, exc_info=ctx.error)
        return error_msg

    def _estimate_tokens(self, tool: Tool, kwargs: dict) -> int:
        """Token 估算（执行前）"""
        # TODO: 实现更精确的 token 估算
        # 简单实现：基于参数字符串长度估算
        params_str = str(kwargs)
        return len(params_str) // 4  # 粗略估算：4 个字符 ≈ 1 token

    def _count_tokens(self, result: str) -> int:
        """Token 统计（执行后）"""
        # TODO: 使用 agent 的 token count estimator
        return len(result) // 4  # 粗略估算：4 个字符 ≈ 1 token

    # === 审计和分析接口 ===

    def get_audit_log(self) -> list[dict]:
        """获取审计日志（用于 TPST 分析）"""
        return self._audit_log

    def clear_audit_log(self) -> None:
        """清空审计日志"""
        self._audit_log.clear()

    def analyze_tpst(self) -> dict:
        """
        分析 TPST（Tokens Per Solved Task）

        这是项目核心指标！

        返回：
            {
                'total_tokens': int,           # 总 token 消耗
                'successful_tasks': int,       # 成功任务数
                'failed_tasks': int,           # 失败任务数
                'tpst': float,                 # TPST 指标
                'constraint_violations': int,  # 约束违反次数
                'batched_operations': int,     # 批处理操作次数
                'avg_duration': float,         # 平均执行时长
                'slow_tools': list[str],       # 慢工具列表
                'token_waste': list[dict]      # Token 浪费详情
            }
        """
        if not self._audit_log:
            return {
                'total_tokens': 0,
                'successful_tasks': 0,
                'failed_tasks': 0,
                'tpst': 0.0,
                'constraint_violations': 0,
                'batched_operations': 0,
                'avg_duration': 0.0,
                'slow_tools': [],
                'token_waste': []
            }

        total_tokens = sum(r['tokens'] for r in self._audit_log)
        successful_tasks = sum(1 for r in self._audit_log if r['success'])
        failed_tasks = len(self._audit_log) - successful_tasks

        # 识别慢工具
        slow_tools = [
            r['tool'] for r in self._audit_log
            if r['duration'] > self._slow_tool_threshold
        ]

        # 识别 token 浪费
        token_waste = [
            {
                'tool': r['tool'],
                'tokens': r['tokens'],
                'accuracy': r['estimation_accuracy']
            }
            for r in self._audit_log
            if r['estimation_accuracy'] < 0.8  # 准确度 < 80%
        ]

        return {
            'total_tokens': total_tokens,
            'successful_tasks': successful_tasks,
            'failed_tasks': failed_tasks,
            'tpst': total_tokens / successful_tasks if successful_tasks > 0 else 0,
            'constraint_violations': sum(1 for r in self._audit_log if r['constraints']),
            'batched_operations': sum(1 for r in self._audit_log if r['batched']),
            'avg_duration': sum(r['duration'] for r in self._audit_log) / len(self._audit_log),
            'slow_tools': list(set(slow_tools)),
            'token_waste': token_waste
        }
```

---

## 🔄 集成方案

### Step 1: SerenaAgent 集成

```python
# src/serena/agent.py

class SerenaAgent:
    def __init__(
        self,
        project: str | None = None,
        project_activation_callback: Callable[[], None] | None = None,
        serena_config: SerenaConfig | None = None,
        context: SerenaAgentContext | None = None,
        modes: list[SerenaAgentMode] | None = None,
        memory_log_handler: MemoryLogHandler | None = None,
    ):
        # ... 现有初始化代码 ...

        # 【新增】：创建统一执行引擎
        from evolvai.core.execution_engine import ToolExecutionEngine
        self._execution_engine = ToolExecutionEngine(self)

        # 【可选】：启用约束系统（feature flag）
        if self.serena_config.enable_constraints:
            from evolvai.constraints import ConstraintEngine
            constraint_engine = ConstraintEngine(self)
            self._execution_engine.enable_constraints(constraint_engine)
            log.info("Constraint system enabled via feature flag")
```

### Step 2: Tool 基类简化

```python
# src/serena/tools/tools_base.py

class Tool(Component):
    def apply_ex(self, log_call: bool = True, catch_exceptions: bool = True, **kwargs) -> str:
        """
        【简化版】apply_ex - 只保留向后兼容的接口

        实际执行委托给 ToolExecutionEngine。

        参数：
            log_call: 已废弃（向后兼容保留）
            catch_exceptions: 已废弃（向后兼容保留）
            **kwargs: 工具参数

        返回：
            执行结果
        """
        # 直接委托给执行引擎
        return self.agent._execution_engine.execute(self, **kwargs)

    # apply() 方法不变，子类继续实现业务逻辑
    def apply(self, **kwargs) -> str:
        """
        实际的工具业务逻辑（子类必须实现）

        这个方法由 ToolExecutionEngine 调用。
        """
        raise NotImplementedError("Subclasses must implement apply()")
```

### Step 3: 配置扩展

```python
# src/serena/config/serena_config.py

@dataclass
class SerenaConfig:
    # ... 现有配置 ...

    # 【新增】：执行引擎配置
    enable_constraints: bool = False  # Feature flag: 启用约束系统
    slow_tool_threshold: float = 5.0  # 慢工具阈值（秒）
    token_waste_threshold: float = 1.2  # Token 浪费阈值（实际 / 估算）
```

---

## 📊 实施计划

### Story 0.1: 实现 ToolExecutionEngine（5 天）

**目标**：创建核心执行引擎和数据结构

**任务**：
1. 创建 `ExecutionPhase` 枚举
2. 创建 `ExecutionContext` 数据类
3. 创建 `ToolExecutionEngine` 类
4. 实现 4 阶段执行流程
5. 实现审计日志接口
6. 实现 TPST 分析接口

**测试覆盖**：
- `test_execution_context_creation()`
- `test_execution_context_to_audit_record()`
- `test_execution_engine_pre_validation()`
- `test_execution_engine_execution_flow()`
- `test_execution_engine_error_handling()`
- `test_execution_engine_audit_log()`
- `test_execution_engine_tpst_analysis()`

**验收标准**：
- [ ] 所有单元测试通过
- [ ] 代码覆盖率 ≥ 90%
- [ ] 类型检查通过（mypy）
- [ ] 代码格式化通过（ruff + black）

### Story 0.2: 集成到 SerenaAgent（3 天）

**目标**：将执行引擎集成到 SerenaAgent

**任务**：
1. 修改 `SerenaAgent.__init__()` 创建执行引擎
2. 修改 `Tool.apply_ex()` 委托给执行引擎
3. 移除 `SerenaAgent.execute_task()`（保留注释）
4. 添加配置项（feature flag）
5. 更新 MCP 适配器（保持不变，因为接口未变）

**测试覆盖**：
- `test_agent_creates_execution_engine()`
- `test_tool_apply_ex_delegates_to_engine()`
- `test_feature_flag_controls_constraints()`
- `test_backward_compatibility()`

**验收标准**：
- [ ] 所有现有测试通过（回归测试）
- [ ] 新增测试通过
- [ ] 工具调用行为不变
- [ ] MCP 协议兼容

### Story 0.3: 回归测试和性能验证（2 天）

**目标**：验证简化后的链路正确性和性能

**任务**：
1. 运行所有现有单元测试
2. 运行所有集成测试
3. 验证审计日志正确性
4. 性能基准测试（与简化前对比）
5. 文档更新

**测试场景**：
- 所有工具的基本调用
- 异常情况处理
- 超时处理
- Language Server 启动
- 项目激活

**验收标准**：
- [ ] 所有测试通过（无回归）
- [ ] 审计日志完整准确
- [ ] 性能无明显下降（< 5%）
- [ ] 文档更新完成

---

## 🎯 成功指标

### 技术指标

```yaml
代码质量:
  测试覆盖率: ≥ 90%
  类型检查: 100% 通过
  代码复杂度: McCabe < 10

性能指标:
  执行耗时: < 105% 简化前（允许 5% 增加）
  内存占用: < 110% 简化前
  线程数: 不变（仍然是 1 个工作线程）

审计能力:
  审计日志完整性: 100%（所有工具调用都有记录）
  Token 追踪准确性: ≥ 80%（estimation_accuracy）
  TPST 可计算: ✅（提供完整接口）
```

### 业务指标

```yaml
开发效率:
  Epic-001 开发时间: 减少 30%（统一入口，无需多处注入）
  调试时间: 减少 50%（清晰的执行路径）

可维护性:
  代码理解时间: 减少 40%（4 层 vs 7 层）
  Bug 定位时间: 减少 50%（统一审计日志）
```

---

## 🛡️ 风险管理

### 高风险项

1. **回归风险**：修改核心调用链路可能破坏现有功能
   - **缓解**：充分的回归测试 + 渐进式发布

2. **性能风险**：新的执行引擎可能带来性能开销
   - **缓解**：性能基准测试 + 优化瓶颈

3. **Feature flag 风险**：约束系统启用可能有 bug
   - **缓解**：默认禁用 + 充分测试

### 中风险项

4. **学习成本**：团队需要理解新的执行流程
   - **缓解**：清晰的文档 + 代码注释

5. **测试成本**：需要编写大量新测试
   - **缓解**：TDD 开发 + 测试复用

### 回滚计划

如果 Phase 0 出现严重问题：
1. **Step 1**：Feature flag 禁用执行引擎
2. **Step 2**：恢复 `Tool.apply_ex()` 原实现
3. **Step 3**：保留 `SerenaAgent.execute_task()`
4. **Step 4**：灰度回滚（逐步恢复旧代码）

---

## 📚 参考资料

### 设计模式

- **责任链模式**（Chain of Responsibility）
- **中间件模式**（Middleware Pattern）
- **管道模式**（Pipeline Pattern）
- **策略模式**（Strategy Pattern）

### 相关 ADR

- [ADR-003: 工具调用链路简化](./adrs/003-tool-execution-engine-simplification.md)
- [ADR-001: Graph-of-Thought over Sequential Thinking](./adrs/001-graph-of-thought-over-sequential-thinking.md)

### 技术文档

- [Epic-001: 行为约束系统](../../product/epics/epic-001-behavior-constraints/README.md)
- [TPST Metrics Reference](../../product/specs/metrics-reference.md)

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
