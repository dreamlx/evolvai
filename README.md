# EvolvAI

<div align="center">
  <h3>AI 工具使用策略引擎</h3>
  <p>让 AI 更聪明地使用工具，而非提供更多工具</p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Tests](https://img.shields.io/badge/Tests-326%20passed-brightgreen.svg)](tests/)
  [![Based on](https://img.shields.io/badge/Based%20on-Serena-orange.svg)](https://github.com/oraios/serena)
</div>

---

## 核心价值

EvolvAI 是基于 [Serena](https://github.com/oraios/serena) 的 AI 工具使用策略引擎，专注于优化 AI 编程助手的工具调用效率。

### 优化层次

```
┌─────────────────────────────────────────────┐
│  EvolvAI (策略层)                            │
│  • 约束系统 - 控制操作边界                    │
│  • TPST分析 - 识别 token 浪费                │
│  • 区域检测 - 智能搜索范围                    │
│  • Propose/Apply - 安全两阶段编辑             │
├─────────────────────────────────────────────┤
│  Serena (执行层)                             │
│  • LSP 符号分析 - 精准代码理解                │
│  • 缓存优化 - 减少重复计算                    │
│  • 多语言支持 - 30+ 编程语言                  │
└─────────────────────────────────────────────┘
```

**关键区别**：
- Serena 优化**执行效率**（每次调用更快）
- EvolvAI 优化**使用策略**（调用更少、更精准）

---

## 核心功能

### 1. ExecutionPlan 约束系统

防止 AI 失控修改，提供可预测的操作边界：

```python
from evolvai.core.execution_plan import ExecutionPlan, ExecutionLimits

plan = ExecutionPlan(
    limits=ExecutionLimits(
        max_files=10,      # 最多修改10个文件
        max_changes=50,    # 最多50处变更
        timeout_seconds=60 # 60秒超时
    ),
    rollback=RollbackStrategy(strategy=RollbackStrategyType.GIT_REVERT)
)

# AI 使用受约束的工具
result = batch_edit(
    pattern=r"oldFunc",
    replacement="newFunc",
    execution_plan=plan
)
```

### 2. TPST 分析 (Tokens Per Successful Task)

识别 token 浪费，优化工具使用效率：

```python
# 获取工具使用统计
stats = engine.analyze_tpst()

# 识别 token 浪费的工具
slow_tools = engine.get_slow_tools(threshold_ms=1000)
token_wasters = engine.get_token_wasters(threshold=5000)
```

### 3. 区域检测 (Area Detection)

智能限定搜索范围，减少无效扫描：

```python
# 自动检测项目区域
areas = detector.detect_areas()
# → [ProjectArea(name="backend-python", ...),
#    ProjectArea(name="frontend-react", ...)]

# 智能搜索（只在相关区域）
result = safe_search(
    query="database connection",
    area_selector="auto"  # 自动选择 backend 区域
)
```

### 4. Propose/Apply 安全编辑

两阶段编辑，预览后再应用：

```python
# Phase 1: 提议变更（生成 diff）
proposal = propose_edit(
    pattern=r"TODO",
    replacement="DONE",
    scope="**/*.py"
)
# → 返回 unified_diff 和 patch_id

# Phase 2: 确认后应用
result = apply_edit(patch_id=proposal.patch_id)
```

---

## 快速开始

### 安装

```bash
# 使用 uv（推荐）
uv pip install evolvai

# 或使用 pip
pip install evolvai
```

### MCP 服务器配置

在 Claude Desktop 或其他 MCP 客户端中配置：

```json
{
  "mcpServers": {
    "evolvai": {
      "command": "uv",
      "args": ["run", "evolvai", "mcp"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

### 基础使用

```bash
# 启动 MCP 服务器
evolvai mcp

# 或带 Dashboard
evolvai mcp --dashboard
```

---

## 工具列表

### 高级策略工具（EvolvAI 独有）

| 工具 | 功能 | 差异化价值 |
|------|------|-----------|
| `batch_edit` | 多文件批量编辑 | ExecutionPlan 约束 + 自动回滚 |
| `safe_search` | 智能搜索 | 区域检测 + 预算分配 |
| `propose_edit` | 提议编辑 | 预览 diff，不直接修改 |
| `apply_edit` | 应用编辑 | 约束验证 + 回滚支持 |
| `safe_exec` | 安全执行 | 命令白名单 + 超时保护 |

### 基础符号工具（继承自 Serena）

| 工具 | 功能 |
|------|------|
| `find_symbol` | LSP 符号查找 |
| `get_symbols_overview` | 文件符号概览 |
| `find_referencing_symbols` | 引用查找 |
| `replace_symbol_body` | 符号替换 |
| 更多... | 参见 [Serena 文档](https://github.com/oraios/serena) |

---

## 架构

```
evolvai/
├── core/                    # 核心引擎
│   ├── execution.py         # ToolExecutionEngine (4阶段执行)
│   ├── execution_plan.py    # ExecutionPlan 约束定义
│   └── constraint_exceptions.py  # 约束异常
├── area_detection/          # 区域检测
│   ├── detector.py          # AreaDetector
│   ├── query_router.py      # QueryRouter
│   └── feedback_system.py   # FeedbackSystem
├── tools/                   # 高级工具
│   ├── batch_edit_tool.py   # BatchEditTool
│   ├── safe_exec_tool.py    # SafeExecTool
│   └── patch_editor.py      # PatchEditor
└── ...
```

---

## 与 Serena 的关系

EvolvAI 是 Serena 的**策略层扩展**，而非替代品：

| 方面 | Serena | EvolvAI |
|------|--------|---------|
| 定位 | 执行层 | 策略层 |
| 优化目标 | 每次调用更快 | 调用更少更精准 |
| 核心能力 | LSP、符号分析、缓存 | 约束、TPST、区域检测 |
| 关系 | 基础设施 | 上层策略 |

我们定期同步上游 Serena 的改进，同时保持策略层的差异化。

---

## 开发

### 环境设置

```bash
# 克隆仓库
git clone https://github.com/dreamlx/evolvai.git
cd evolvai

# 安装依赖
uv sync

# 运行测试
uv run poe test

# 代码格式化
uv run poe format

# 类型检查
uv run poe type-check
```

### 项目结构

- `src/evolvai/` - EvolvAI 核心代码
- `src/serena/` - Serena 基础代码（同步自上游）
- `src/solidlsp/` - LSP 协议实现
- `test/evolvai/` - EvolvAI 测试
- `docs/` - 文档

---

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 贡献方向

- 约束系统增强（更多预设配置）
- TPST Dashboard 可视化
- 区域检测优化（更多语言支持）
- 文档和示例

---

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 致谢

- [Serena](https://github.com/oraios/serena) - 提供强大的 LSP 基础能力
- [Oraios AI](https://oraios-ai.de/) - Serena 的创建者

---

<div align="center">
  <p>让 AI 更聪明地使用工具</p>
</div>
