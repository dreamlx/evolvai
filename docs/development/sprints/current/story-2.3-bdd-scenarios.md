# Story 2.3: safe_exec Command Execution Wrapper - BDD Scenarios

**Story ID**: STORY-2.3
**创建日期**: 2025-01-14
**状态**: [ACTIVE] - MVP Development
**决策**: KISS 原则优先，应用 Feature 2.2 经验教训

---

## 📋 Story概述

**用户故事**:
> 作为AI编程助手，我需要快速知道命令是否能执行、在timeout时自动清理进程、并限制输出长度，这样可以减少token浪费并加快迭代速度。

**核心价值**（Epic-001目标：减少TPST，不是系统安全）:
- ✅ 快速失败机制（依赖检查 + 工作目录验证 + 推理崩溃检测）
- ✅ Timeout管理（避免卡住浪费时间）
- ✅ 输出截断（head 50 + tail 50，减少token消耗）
- ✅ 有用错误信息（帮助AI快速修正路径）
- ✅ ExecutionPlan集成（仅timeout约束）

**架构简化（KISS原则）**:
- ✅ 直接使用 subprocess + os.setsid (避免复杂的进程树管理)
- ✅ 简单的黑名单机制（避免复杂的规则引擎）
- ✅ 固定输出截断（head 50 + tail 50，避免可配置复杂度）
- ✅ 复用 ToolExecutionEngine（避免重复审计系统）

**反模式**（故意不做的）:
- ❌ 环境检测系统（开发/生产/测试区分 - 不是工具层责任）
- ❌ allowed_commands白名单（过度设计，与黑名单重复）
- ❌ 复杂黑名单（3-5条极简规则足够）
- ❌ 系统安全防护（依赖OS权限 + Git版本控制）
- ❌ 可配置输出截断（固定 50 行足够）

---

## 🎯 验收标准（Definition of Done）

### 功能完整性 (F)

**F1: 快速失败机制**✅ (Target)
- 检测命令依赖存在性（shutil.which）→ 避免浪费token尝试
- 验证工作目录有效性 → 避免在错误位置执行
- 检测荒谬命令（3-5条规则：rm -rf /, mkfs, fork bomb）→ 检测AI推理崩溃
- 返回清晰错误信息（指向推理问题而非"危险"）

**F2: ProcessManager 管理进程组和 timeout** ✅ (Target)
- 使用 os.setsid 创建新进程组
- timeout 时使用 os.killpg 清理整个进程组
- 捕获 stdout 和 stderr
- 返回 exit code 和执行时长

**F3: SafeExecWrapper 提供统一接口** ✅ (Target)
- safe_exec(command, timeout, working_dir) 统一入口
- 自动调用 PreconditionChecker
- 自动管理进程生命周期
- 输出截断（head 50 + tail 50）

**F4: ExecutionPlan 集成（仅timeout约束）** ✅ (Target)
- 支持 execution_plan 参数（可选，向后兼容）
- 验证 timeout 约束（防止超出计划限制）
- 违规抛出 ConstraintViolationError
- 违规记录到审计日志

**F5: MCP 工具暴露** ✅ (Target)
- safe_exec 暴露为 MCP 工具
- AI 助手可以调用
- 自动注册到 Serena 工具系统

### 质量标准 (Q)

**Q1: 测试覆盖率 ≥ 90%** ✅ (Target)
- 所有核心 BDD 场景有对应测试
- 边界情况和错误处理覆盖
- Mock 复杂度 ≤ 3/10

**Q2: 代码质量** ✅ (Target)
- 通过 format/type-check/lint
- 符合 KISS 原则
- 无过度设计

**Q3: 向后兼容性** ✅ (Target)
- 不破坏现有工具接口
- ExecutionPlan 参数为可选
- 无现有测试回归

### 性能标准 (P)

**P1: Precondition 检查延迟** ✅ (Target)
- < 10ms（命令验证 + 依赖检查）

**P2: 命令执行延迟** ✅ (Target)
- < 100ms 额外开销（相比原生 subprocess）
- 进程组创建不影响性能

**P3: Timeout 清理速度** ✅ (Target)
- < 50ms（从 timeout 触发到所有进程终止）
- 无僵尸进程残留

---

## 🎬 BDD场景定义

### Scenario 1: 执行安全命令成功 ✅

**优先级**: P0 - 核心功能
**DoD映射**: F1, F2, F3, Q1, P2
**状态**: ⏳ Pending

```gherkin
Feature: 安全命令执行
  作为AI助手，我想执行经过验证的安全命令
  这样我可以完成需要系统操作的任务

Scenario: 成功执行 echo 命令
  Given 命令 "echo 'Hello World'"
    And timeout 为 5 秒
    And 工作目录 "/tmp"
  When 我调用 safe_exec(command="echo 'Hello World'", timeout=5, working_dir="/tmp")
  Then 返回成功结果
    And exit_code 为 0
    And stdout 包含 "Hello World"
    And stderr 为空
    And precondition_passed 为 True
    And duration_ms < 100ms
```

**测试函数名**: `test_safe_exec_simple_command_success`
**实现状态**: ⏳ Pending
**关键验证点**:
- ✅ 命令成功执行
- ✅ 正确捕获输出
- ✅ Precondition 检查通过
- ✅ 性能符合 P2 标准

---

### Scenario 2: 检测AI推理崩溃信号 ✅

**优先级**: P0 - TPST优化核心
**DoD映射**: F1, Q1
**状态**: ⏳ Pending

```gherkin
Feature: AI推理崩溃检测
  作为开发者，我需要知道AI的推理是否出现问题
  这样我可以快速介入而不是浪费token

Scenario: 检测荒谬命令（推理崩溃信号）
  Given 命令 "rm -rf /"
  When 我调用 safe_exec(command="rm -rf /")
  Then 抛出 ConstraintViolationError
    And 错误信息包含 "Absurd command detected"
    And 错误信息包含 "This suggests AI reasoning failure"
    And 建议 "Please reconsider the task goal"
    And 审计日志记录推理崩溃事件

Examples:
  | command              | pattern      |
  | rm -rf /             | rm.*-rf.*/   |
  | mkfs.ext4 /dev/sda   | mkfs\.       |
  | :(){ :\|:& };:       | fork bomb    |
```

**测试函数名**: `test_detects_absurd_commands` (参数化测试)
**实现状态**: ⏳ Pending
**关键验证点**:
- ✅ 识别荒谬命令模式（3-5条规则）
- ✅ 阻止执行
- ✅ 错误信息强调"推理失败"而非"危险"
- ✅ 审计日志记录

---

### Scenario 3: Timeout 时完全清理子进程 ✅

**优先级**: P0 - 进程管理核心
**DoD映射**: F2, P3, Q1
**状态**: ⏳ Pending

```gherkin
Feature: 进程超时清理
  作为系统管理员，我需要确保超时命令的所有子进程被清理
  这样我可以避免僵尸进程和资源泄漏

Scenario: 超时命令及其子进程全部终止
  Given 命令 "sleep 100 & sleep 100 & wait"
    And timeout 为 1 秒
  When 我调用 safe_exec(command="sleep 100 & sleep 100 & wait", timeout=1)
  Then 抛出 TimeoutError
    And 主进程被终止
    And 所有子进程被终止（通过 killpg）
    And 清理耗时 < 50ms
    And 无僵尸进程残留
```

**测试函数名**: `test_safe_exec_timeout_kills_process_group`
**实现状态**: ⏳ Pending
**关键验证点**:
- ✅ os.setsid 创建进程组
- ✅ os.killpg 被正确调用（通过Mock验证，避免ps/proc跨平台问题）
- ✅ TimeoutError 正确抛出
- ✅ 清理速度符合 P3 标准

---

### Scenario 4: 检测命令依赖缺失 ✅

**优先级**: P0 - Precondition 核心
**DoD映射**: F1, Q1
**状态**: ⏳ Pending

```gherkin
Feature: 依赖检查
  作为AI助手，我需要在执行前知道命令是否可用
  这样我可以给用户明确的错误信息

Scenario: 检测到不存在的命令
  Given 命令 "nonexistent_command_xyz"
  When 我调用 safe_exec(command="nonexistent_command_xyz")
  Then 抛出 ConstraintViolationError
    And 错误信息包含 "Command not found"
    And 错误信息包含 "nonexistent_command_xyz"
    And 建议安装方法（如果已知）
```

**测试函数名**: `test_safe_exec_detects_missing_command`
**实现状态**: ⏳ Pending
**关键验证点**:
- ✅ shutil.which 检测命令存在性
- ✅ 清晰错误信息
- ✅ 友好的建议（可选）

---

### Scenario 5: ExecutionPlan timeout约束验证 ✅

**优先级**: P1 - Epic-001 集成
**DoD映射**: F4, Q3
**状态**: ⏳ Pending

```gherkin
Feature: ExecutionPlan 集成
  作为系统架构师，我需要 safe_exec 遵守 ExecutionPlan 的 timeout 约束
  这样我可以确保 AI 不会超出计划的时间限制

Scenario: 验证 timeout 约束
  Given execution_plan 限制 timeout ≤ 10 秒
    And 命令 "sleep 5"
  When 我调用 safe_exec(command="sleep 5", timeout=15, execution_plan=plan)
  Then 抛出 ConstraintViolationError
    And 错误信息包含 "Timeout exceeds plan limit"
    And 错误信息包含 "plan: 10s, requested: 15s"
    And 违规记录到审计日志

Scenario: 无ExecutionPlan时向后兼容
  Given 无 execution_plan 参数
  When 我调用 safe_exec(command="echo test", timeout=5)
  Then 返回成功结果
    And 无约束验证
```

**测试函数名**:
- `test_safe_exec_enforces_timeout_constraint`
- `test_safe_exec_backward_compatible_no_plan`

**实现状态**: ⏳ Pending
**关键验证点**:
- ✅ ExecutionPlan 参数为可选（向后兼容）
- ✅ 仅验证timeout约束（不做allowed_commands）
- ✅ 违规记录到审计日志

---

### Scenario 6: 输出截断防止 token 浪费 ✅

**优先级**: P1 - TPST 优化
**DoD映射**: F3, Q1
**状态**: ⏳ Pending

```gherkin
Feature: 输出截断
  作为成本优化者，我需要限制命令输出长度
  这样我可以避免 token 浪费和上下文窗口污染

Scenario: 长输出被截断为 head 50 + tail 50
  Given 命令生成 200 行输出
  When 我调用 safe_exec(command="seq 1 200")
  Then 返回成功结果
    And stdout 只包含前 50 行
    And stdout 包含 "... (100 lines omitted) ..."
    And stdout 包含后 50 行
    And 总行数为 101（50 + 1 + 50）
```

**测试函数名**: `test_safe_exec_truncates_long_output`
**实现状态**: ⏳ Pending
**关键验证点**:
- ✅ 固定截断策略（head 50 + tail 50）
- ✅ 中间省略提示
- ✅ 不影响短输出（≤ 100 行）

---

### Scenario 7: MCP 工具暴露和调用 ✅

**优先级**: P0 - MCP 集成
**DoD映射**: F5, Q3
**状态**: ⏳ Pending

```gherkin
Feature: MCP 工具暴露
  作为AI助手，我需要通过 MCP 协议调用 safe_exec
  这样我可以在任何支持 MCP 的客户端中使用

Scenario: SafeExecTool 注册到 MCP 服务器
  Given SerenaAgent 已初始化
  When MCP 服务器启动
  Then SafeExecTool 在工具列表中
    And 工具名称为 "safe_exec"
    And 工具描述清晰说明功能和约束
    And 参数 schema 包含 command, timeout, working_dir

Scenario: 通过 MCP 调用 safe_exec
  Given MCP 客户端连接到服务器
  When 客户端调用 safe_exec(command="echo test", timeout=5)
  Then 返回成功结果
    And 结果包含 stdout, stderr, exit_code
    And 审计日志记录 MCP 调用
```

**测试函数名**:
- `test_safe_exec_tool_registered_in_mcp`
- `test_safe_exec_tool_called_via_mcp`

**实现状态**: ⏳ Pending
**关键验证点**:
- ✅ SafeExecTool 继承 Tool 基类
- ✅ 自动注册到工具系统
- ✅ MCP schema 正确定义
- ✅ 端到端调用成功

---

## 📊 测试实施路线图

**总体策略**: 应用KISS原则，参数化测试减少重复，总测试数 14-17个（从20-25个优化）

### Day 1: PreconditionChecker TDD
**Scenarios**: 1, 2, 4
**Tests**: 5-6 tests
**Focus**: 快速失败机制（依赖、工作目录、推理崩溃检测）

**Test List**:
1. `test_safe_exec_simple_command_success` (Scenario 1)
2. `test_detects_absurd_commands` (Scenario 2 - **参数化测试**，覆盖3-5条规则)
3. `test_detects_missing_command` (Scenario 4)
4. `test_validates_working_directory_invalid`
5. `test_validates_working_directory_relative`
6. `test_precondition_check_performance` (< 10ms)

---

### Day 2: ProcessManager TDD
**Scenarios**: 3, 6
**Tests**: 5-6 tests
**Focus**: 进程组管理、timeout、输出截断

**Test List**:
1. `test_safe_exec_timeout_kills_process_group` (Scenario 3 - Mock验证)
2. `test_safe_exec_captures_stdout_stderr`
3. `test_safe_exec_returns_exit_code`
4. `test_safe_exec_truncates_long_output` (Scenario 6)
5. `test_safe_exec_handles_command_failure`
6. `test_process_cleanup_performance` (< 50ms)

---

### Day 3: ExecutionPlan Integration & MCP Tools
**Scenarios**: 5, 7
**Tests**: 5-6 tests
**Focus**: ExecutionPlan 集成（仅timeout）、MCP 工具

**Test List**:
1. `test_safe_exec_enforces_timeout_constraint` (Scenario 5)
2. `test_safe_exec_backward_compatible_no_plan` (Scenario 5)
3. `test_safe_exec_audit_log_integration`
4. `test_safe_exec_tool_registered_in_mcp` (Scenario 7)
5. `test_safe_exec_tool_called_via_mcp` (Scenario 7)
6. `test_safe_exec_tool_schema_validation`

**删除的测试** (应用KISS原则):
- ❌ `test_safe_exec_enforces_allowed_commands` (白名单过度设计)
- ❌ `test_safe_exec_no_zombie_processes` (与timeout测试重复)
- ❌ 多个单独的黑名单测试 (合并为参数化测试)

---

## 🎯 成功标准检查清单

### 功能验收
- [ ] F1: 快速失败机制工作正常（依赖检查 + 工作目录 + 推理崩溃检测）
- [ ] F2: Timeout 清理 100% 成功（Mock验证os.killpg调用）
- [ ] F3: 输出截断正确工作（head 50 + tail 50）
- [ ] F4: ExecutionPlan timeout约束正确验证（无allowed_commands）
- [ ] F5: MCP 工具正确暴露和调用

### 质量验收
- [ ] Q1: 测试通过率 ≥ 95% (应用 Feature 2.2 教训)
- [ ] Q2: format ✅ type-check ✅ lint ✅
- [ ] Q3: Mock 复杂度评分 ≤ 3/10
- [ ] 所有测试有 Story/Scenario/DoD 映射
- [ ] 无 Feature 2.2 的过度设计问题

### 性能验收
- [ ] P1: Precondition 检查 < 10ms (平均)
- [ ] P2: 命令执行开销 < 100ms
- [ ] P3: Timeout 清理 < 50ms

---

## 🚨 KISS 原则检查点

### 核心设计原则（基于深度反思）

**Epic-001 真正目标**: 减少TPST（Token浪费），不是系统安全防护

**在Git + 开发环境下的"不可逆"重定义**:
- ✅ 大部分"危险命令"在开发环境都可逆（有Git + 备份）
- ✅ 真正不可逆：删除.git、push --force污染远程、生产环境操作
- ✅ 环境隔离是部署架构层责任，不是safe_exec职责

**黑名单的真正价值**:
- ❌ 不是"阻止危险操作"
- ✅ 是"检测AI推理崩溃"
- 例如：AI想执行 `rm -rf /` → 说明推理已经出问题

### 避免过度设计（应用深度反思）

**❌ 不要做**:
- ❌ 环境检测系统（开发/生产区分 - 架构层责任）
- ❌ allowed_commands白名单（过度设计，与黑名单重复）
- ❌ 复杂黑名单（3-5条规则足够，不要30-50条）
- ❌ 系统安全防护（依赖OS权限 + Git）
- ❌ 可配置输出截断（固定 50 行足够）

**✅ 应该做**:
- ✅ 极简黑名单（3-5条：rm -rf /, mkfs, fork bomb）
- ✅ 错误信息强调"推理失败"而非"危险"
- ✅ 固定输出截断策略
- ✅ 直接使用 subprocess + os 模块
- ✅ 复用 ToolExecutionEngine 审计
- ✅ 参数化测试减少重复

---

## 📚 相关文档

- [Story 2.3 TDD Plan](./story-2.3-tdd-plan.md)
- [Feature 2.2 TDD Lessons Learned](.serena/memories/feature-2.2-tdd-lessons-learned)
- [TDD Refactoring Guidelines](../../testing/standards/tdd-refactoring-guidelines.md)
- [Epic-001 Definition](../../product/epics/epic-001-behavior-constraints/README.md)

---

**最后更新**: 2025-01-14 (深度反思后修订)
**修订理由**: 应用Epic-001核心目标（减少TPST，不是系统安全）重新设计
**关键变化**:
- 删除 allowed_commands 白名单（过度设计）
- 黑名单重定位为"推理崩溃检测"（3-5条规则）
- 测试数量优化：20-25个 → 14-17个
- 不做环境检测（架构层责任）

**维护者**: EvolvAI Team
**下一步**: Day 1 TDD 实施 - PreconditionChecker
