# Feature 2.3: Safe Exec Wrapper - TDD Plan

**版本**: 1.0
**创建日期**: 2025-11-01
**状态**: [DRAFT]
**适用范围**: Epic-001 Phase 2 Safe Operations

---

## 📋 Feature概述

### 功能描述
实现 `safe_exec` 包装器，为命令执行增加 precondition 检查，确保AI助手只能执行安全的、经过验证的命令。

### 核心价值
- **物理删除错误路径**: 从接口层面阻止危险命令执行
- **Precondition验证**: 执行前检查系统状态、权限、依赖
- **进程组管理**: 确保timeout时完全清理子进程
- **审计集成**: 与ToolExecutionEngine完整集成

---

## 🎯 设计原则 (KISS指导)

### 核心原则
- ✅ **行为验证**: 测试"做什么"而非"怎么做"
- ✅ **最小Mock**: 只mock必要的系统调用
- ✅ **简单接口**: 避免过度参数化
- ✅ **业务语言**: 测试用例描述用户故事

### 避免的陷阱（Feature 2.2教训）
- ❌ 复杂的mock链设置
- ❌ 测试内部实现细节
- ❌ 过度设计的接口参数
- ❌ 强制性参数过多

---

## 🏗️ 架构设计

### 核心组件
```
SafeExecWrapper
├── PreconditionChecker    # 前置条件检查器
├── ProcessManager        # 进程管理器
├── ExecutionValidator     # 执行验证器
└── AuditLogger           # 审计日志（集成ToolExecutionEngine）
```

### 数据模型（基于现有data_models.py扩展）
```python
@dataclass
class ExecutionPrecondition:
    """执行前置条件"""
    command: str
    working_directory: str
    timeout_seconds: int
    required_permissions: List[str]
    system_dependencies: List[str]
    environment_variables: Dict[str, str]

@dataclass
class ExecutionResult:
    """执行结果"""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    precondition_passed: bool
    error_message: Optional[str] = None
```

---

## 🧪 TDD实施计划

### Phase 1: PreconditionChecker TDD

#### 测试用例设计（KISS原则）

##### 1. 核心功能测试
```python
def test_basic_command_execution_succeeds(self):
    """测试基本命令执行成功"""
    # 用户故事：用户可以执行安全的系统命令

def test_dangerous_command_blocked(self):
    """测试危险命令被阻止"""
    # 用户故事：系统阻止删除重要文件的命令

def test_missing_dependency_detected(self):
    """测试依赖缺失被检测"""
    # 用户故事：系统检测到命令依赖不存在时给出明确错误
```

##### 2. 错误处理测试
```python
def test_permission_denied_handled_gracefully(self):
    """测试权限不足被优雅处理"""

def test_timeout_cleanup_complete(self):
    """测试超时时完全清理进程"""

def test_invalid_working_directory_handled(self):
    """测试无效工作目录被处理"""
```

#### 实现要点
- 使用简单Mock模拟`os.access`, `shutil.which`
- 避免复杂的进程Mock，专注结果验证
- 测试业务逻辑而非系统调用细节

### Phase 2: ProcessManager TDD

#### 测试用例设计
```python
def test_process_group_management(self):
    """测试进程组管理"""

def test_timeout_kills_all_children(self):
    """测试超时时杀死所有子进程"""

def test_cleanup_on_failure(self):
    """测试失败时的清理"""
```

#### 实现要点
- Mock `subprocess.Popen` 和 `os.killpg`
- 专注进程管理行为验证
- 避免测试具体的PID值

### Phase 3: SafeExecWrapper集成TDD

#### 测试用例设计
```python
def test_safe_exec_success_flow(self):
    """测试安全执行成功流程"""

def test_precondition_failure_blocks_execution(self):
    """测试前置条件失败阻止执行"""

def test_audit_logging_integrated(self):
    """测试审计日志集成"""
```

---

## 📝 具体实施步骤

### Step 1: 创建测试文件（Red Phase）
```bash
touch test/evolvai/area_detection/test_safe_exec_wrapper.py
```

### Step 2: 编写测试用例（Red Phase）
- 按照KISS原则编写测试用例
- 确保测试失败（功能未实现）
- 提交测试用例设计

### Step 3: 实现核心组件（Green Phase）
- PreconditionChecker
- ProcessManager
- SafeExecWrapper
- 逐个通过测试

### Step 4: 集成验证（Green Phase）
- 与ToolExecutionEngine集成
- 验证审计日志功能
- 性能测试

### Step 5: 重构优化（Refactor Phase）
- 应用KISS重构原则
- 简化复杂逻辑
- 提升可读性

---

## 🔧 成功标准

### 功能标准
- ✅ 所有测试通过（目标≥90%通过率）
- ✅ 危险命令100%阻止率
- ✅ 进程清理完整性验证
- ✅ 审计日志完整记录

### 质量标准（KISS指标）
- ✅ Mock复杂度评分 ≤ 3/10
- ✅ 测试用例可读性评分 ≥ 8/10
- ✅ 新团队成员理解时间 ≤ 30分钟
- ✅ 测试代码行数 ≤ 实现代码行数的50%

### 性能标准
- ✅ 命令执行延迟 < 100ms
- ✅ Precondition检查 < 10ms
- ✅ 进程清理 < 50ms

---

## 🚨 风险控制

### 技术风险
- **进程权限问题**: 提供权限检查和错误提示
- **系统依赖差异**: 使用可配置的依赖检查
- **并发执行冲突**: 使用进程隔离

### TDD风险
- **过度设计**: 严格按照KISS原则
- **Mock复杂性**: 定期审查Mock设置
- **测试覆盖率**: 专注核心业务逻辑

---

## 📊 与其他Feature的协调

### 与safe_edit协调
- 共享AreaDetector和ProjectArea
- 统一的错误处理模式
- 一致的审计日志格式

### 与safe_search协调
- 共享QueryRouting逻辑
- 统一的权限检查机制
- 一致的性能监控

### 与ToolExecutionEngine集成
- 使用统一的ExecutionContext
- 集成审计日志API
- 遵循4阶段执行流程

---

## 📚 相关文档

- [TDD重构指南](../testing/standards/tdd-refactoring-guidelines.md)
- [Epic-001定义](../../product/epics/epic-001-behavior-constraints/README.md)
- [Phase 2实施计划](../sprints/current/phase-2-implementation-plan.md)

---

## 🎯 下一步行动

1. **立即**: 创建测试文件和基础测试用例
2. **今天**: 完成PreconditionChecker TDD
3. **明天**: 完成ProcessManager TDD
4. **本周**: 完成SafeExecWrapper集成
5. **下周**: Phase 2重构计划实施

---

**最后更新**: 2025-11-01
**维护者**: EvolvAI Team