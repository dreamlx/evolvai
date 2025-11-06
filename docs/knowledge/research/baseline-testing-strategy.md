# 🧪 safe_search 基准测试和数据收集策略

**创建日期**: 2025-11-07
**讨论主题**: 如何在Dogfooding期间持续收集性能数据并优化工具参数
**关键问题**: 基准测试套件应该如何实现？

---

## 🎯 核心问题

### 用户质疑

> "我们要自己狗屎自己吃，但是我们工具使用中长期数据收集分析，具体参数优化，这些事情怎么实现？这个才是做基准测试的原因。关键是基准测试的专门测试套件如何实现？"

### 原始建议的问题

**我的建议**（preventive-analysis-safe-search.md）:
```
❌ MVP阶段：删除baseline_comparison字段
✅ 基准测试：专门测试套件做对比，不在生产工具中
```

**问题**:
1. ❌ "专门测试套件"过于抽象，没有具体方案
2. ❌ 删除baseline_comparison = 丢失真实使用数据
3. ❌ 没有考虑长期数据收集和参数优化需求
4. ❌ 没有区分"开发模式"和"生产模式"的需求差异

---

## 📊 四种数据收集策略对比

### 策略A: 每次调用都同步对比（产品定义原方案）

```python
def safe_search(query: str, scope: str = "**/*") -> SearchResult:
    """每次调用都运行rg和grep对比"""

    # 1. 运行ripgrep
    rg_start = time.time()
    rg_result = run_ripgrep(query, scope)
    rg_time = time.time() - rg_start

    # 2. 运行grep（对比基线）
    grep_start = time.time()
    grep_result = run_grep(query, scope)
    grep_time = time.time() - grep_start

    # 3. 返回对比数据
    return {
        "tool_used": "ripgrep",
        "result": rg_result,
        "baseline_comparison": {
            "grep_time_s": grep_time,
            "rg_time_s": rg_time,
            "speedup": f"{grep_time / rg_time:.1f}x"
        }
    }
```

**优点**:
- ✅ 真实使用场景数据（最准确）
- ✅ 数据量大，统计显著
- ✅ 每次调用都有完整对比

**缺点**:
- ❌ 性能开销翻倍（用户体验差）
- ❌ 用户每次等待时间 = rg_time + grep_time
- ❌ 违反"safe_search应该更快"的初衷
- ❌ Dogfooding时会感觉"这工具怎么这么慢"

**评估**: ❌ **不推荐** - 为了收集数据牺牲用户体验

---

### 策略B: 采样对比（部分调用做对比）

```python
import random

BENCHMARK_SAMPLE_RATE = 0.1  # 10%的调用做对比

def safe_search(query: str, scope: str = "**/*") -> SearchResult:
    """10%的调用运行对比，90%正常执行"""

    should_benchmark = random.random() < BENCHMARK_SAMPLE_RATE

    # 1. 运行ripgrep（主要工具）
    rg_start = time.time()
    rg_result = run_ripgrep(query, scope)
    rg_time = time.time() - rg_start

    # 2. 采样：10%的调用运行grep对比
    if should_benchmark:
        grep_start = time.time()
        grep_result = run_grep(query, scope)
        grep_time = time.time() - grep_start

        # 记录到TPST Tracker
        log_benchmark_data({
            "query": query,
            "scope": scope,
            "rg_time": rg_time,
            "grep_time": grep_time,
            "speedup": grep_time / rg_time
        })

    return {
        "tool_used": "ripgrep",
        "result": rg_result,
        "execution_time_ms": rg_time * 1000,
        # 不返回baseline_comparison（减少响应体积）
    }
```

**优点**:
- ✅ 90%的调用无额外开销（用户体验好）
- ✅ 仍能收集统计显著的数据（10%采样足够）
- ✅ 可动态调整采样率（环境变量控制）
- ✅ 真实使用场景数据

**缺点**:
- ⚠️ 10%的调用仍有性能损失
- ⚠️ 需要设计采样策略（均匀采样 vs 分层采样）

**评估**: ✅ **推荐（MVP方案）** - 平衡数据收集和用户体验

---

### 策略C: 异步对比（后台线程运行grep）

```python
import threading
from queue import Queue

benchmark_queue = Queue()

def background_benchmark_worker():
    """后台线程运行grep对比"""
    while True:
        task = benchmark_queue.get()
        if task is None:
            break

        query, scope, rg_time = task

        # 后台运行grep（不阻塞主线程）
        grep_start = time.time()
        grep_result = run_grep(query, scope)
        grep_time = time.time() - grep_start

        # 记录对比数据
        log_benchmark_data({
            "query": query,
            "rg_time": rg_time,
            "grep_time": grep_time,
            "speedup": grep_time / rg_time
        })

        benchmark_queue.task_done()

# 启动后台worker
threading.Thread(target=background_benchmark_worker, daemon=True).start()

def safe_search(query: str, scope: str = "**/*") -> SearchResult:
    """主线程运行rg，后台线程异步运行grep对比"""

    # 1. 运行ripgrep（主线程，快速返回）
    rg_start = time.time()
    rg_result = run_ripgrep(query, scope)
    rg_time = time.time() - rg_start

    # 2. 异步：将grep任务放入后台队列
    if os.getenv("EVOLVAI_BENCHMARK_MODE") == "async":
        benchmark_queue.put((query, scope, rg_time))

    # 3. 立即返回rg结果（不等待grep）
    return {
        "tool_used": "ripgrep",
        "result": rg_result,
        "execution_time_ms": rg_time * 1000,
    }
```

**优点**:
- ✅ 用户体验无损（0额外等待时间）
- ✅ 收集100%调用的对比数据
- ✅ 后台线程不影响主流程

**缺点**:
- ❌ 实现复杂度高（线程管理、队列、错误处理）
- ❌ 后台CPU占用（可能影响其他任务）
- ❌ 不适合频繁调用场景（队列堆积）

**评估**: ⚠️ **可选（Phase 2+）** - 实现复杂，收益不明显

---

### 策略D: 模式切换（开发模式 vs 生产模式）

```python
class BenchmarkMode(Enum):
    PRODUCTION = "production"    # 生产模式：只记录实际使用数据
    DEVELOPMENT = "development"  # 开发模式：完整对比
    SAMPLING = "sampling"        # 采样模式：10%对比

def get_benchmark_mode() -> BenchmarkMode:
    """从环境变量读取基准测试模式"""
    mode = os.getenv("EVOLVAI_BENCHMARK_MODE", "production")
    return BenchmarkMode(mode)

def safe_search(query: str, scope: str = "**/*") -> SearchResult:
    """根据模式决定是否运行对比"""

    mode = get_benchmark_mode()

    # 1. 运行ripgrep（所有模式都执行）
    rg_start = time.time()
    rg_result = run_ripgrep(query, scope)
    rg_time = time.time() - rg_start

    baseline_comparison = None

    # 2. 根据模式决定是否运行grep对比
    if mode == BenchmarkMode.DEVELOPMENT:
        # 开发模式：完整对比（100%）
        grep_time = run_grep_benchmark(query, scope)
        baseline_comparison = {
            "grep_time_s": grep_time,
            "rg_time_s": rg_time,
            "speedup": f"{grep_time / rg_time:.1f}x"
        }

    elif mode == BenchmarkMode.SAMPLING:
        # 采样模式：10%对比
        if random.random() < 0.1:
            grep_time = run_grep_benchmark(query, scope)
            log_benchmark_data(query, scope, rg_time, grep_time)

    # 3. 生产模式：只记录rg数据，不运行grep
    log_tool_usage({
        "tool": "ripgrep",
        "query": query,
        "execution_time": rg_time,
        "mode": mode.value
    })

    return {
        "tool_used": "ripgrep",
        "result": rg_result,
        "execution_time_ms": rg_time * 1000,
        "baseline_comparison": baseline_comparison  # 可能为None
    }
```

**使用场景**:
```bash
# 1. Dogfooding生产使用（默认）
export EVOLVAI_BENCHMARK_MODE=production
evolvai-agent  # 不运行对比，用户体验最优

# 2. 开发调试（需要完整对比）
export EVOLVAI_BENCHMARK_MODE=development
evolvai-agent  # 每次调用都对比，数据完整

# 3. 采样收集（长期监控）
export EVOLVAI_BENCHMARK_MODE=sampling
evolvai-agent  # 10%采样，平衡数据和性能
```

**优点**:
- ✅ 灵活：不同场景不同策略
- ✅ 生产模式无性能损失
- ✅ 开发模式获得完整数据
- ✅ 简单：环境变量控制

**缺点**:
- ⚠️ 需要文档说明各模式用途
- ⚠️ 用户可能不知道如何切换模式

**评估**: ✅ **强烈推荐（最优方案）** - 兼顾所有需求

---

## 🧪 基准测试套件设计

### 问题重新定义

> "基准测试的专门测试套件如何实现？"

### 三层基准测试架构

```
┌─────────────────────────────────────────────────────┐
│ Layer 1: 单元基准测试（Unit Benchmarks）              │
│ - 固定测试集（静态代码库 + 搜索模式）                   │
│ - CI/CD自动运行                                      │
│ - 检测性能回归                                       │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Layer 2: 真实使用日志回放（Usage Log Replay）         │
│ - 记录Dogfooding期间的真实search调用                  │
│ - 定期回放评估性能变化                                │
│ - A/B测试参数优化                                    │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ Layer 3: 持续监控（Continuous Monitoring）            │
│ - TPST Tracker集成                                  │
│ - 实时性能指标                                       │
│ - 异常检测和告警                                     │
└─────────────────────────────────────────────────────┘
```

---

### Layer 1: 单元基准测试（静态测试集）

**目标**: 固定的测试集，检测性能回归

**实现**:
```python
# test/evolvai/benchmarks/test_safe_search_benchmarks.py

import pytest
import time
from pathlib import Path

# 固定的测试代码库（check in到repo）
BENCHMARK_REPOS = [
    "test/resources/benchmark-repos/small-python-project",   # 100 files
    "test/resources/benchmark-repos/medium-typescript-project",  # 1000 files
    "test/resources/benchmark-repos/large-monorepo",  # 10000 files
]

# 固定的搜索模式
BENCHMARK_QUERIES = [
    "def test_",           # 高频模式
    "class.*Component",    # 正则表达式
    "import.*from",        # 常见语法
    "TODO|FIXME",          # 多关键词
]

@pytest.mark.benchmark
class TestSafeSearchBenchmarks:

    def test_benchmark_small_repo_high_frequency_pattern(self, benchmark):
        """基准测试：小项目 + 高频模式"""

        def run_search():
            return safe_search(
                query="def test_",
                scope="test/resources/benchmark-repos/small-python-project/**/*.py"
            )

        result = benchmark(run_search)

        # 性能断言
        assert result["execution_time_ms"] < 100  # 小项目应该<100ms

    def test_benchmark_comparison_rg_vs_grep(self):
        """对比基准：rg vs grep"""

        query = "class.*Component"
        scope = "test/resources/benchmark-repos/medium-typescript-project/**/*.ts"

        # 1. 运行ripgrep
        rg_start = time.time()
        rg_result = run_ripgrep(query, scope)
        rg_time = time.time() - rg_start

        # 2. 运行grep（公平对比：使用git ls-files）
        grep_start = time.time()
        grep_result = run_grep_fair(query, scope)
        grep_time = time.time() - grep_start

        # 3. 验证结果一致性
        assert rg_result["hits_count"] == grep_result["hits_count"]

        # 4. 性能断言
        speedup = grep_time / rg_time
        assert speedup > 3.0  # ripgrep至少快3倍

        # 5. 记录基准数据
        log_benchmark({
            "query": query,
            "repo_size": "medium",
            "rg_time": rg_time,
            "grep_time": grep_time,
            "speedup": speedup,
            "timestamp": datetime.now().isoformat()
        })
```

**目录结构**:
```
test/
├── resources/
│   └── benchmark-repos/
│       ├── small-python-project/     # 100 files, 10K LOC
│       ├── medium-typescript-project/ # 1000 files, 100K LOC
│       └── large-monorepo/           # 10000 files, 1M LOC
└── evolvai/
    └── benchmarks/
        ├── test_safe_search_benchmarks.py
        ├── test_safe_edit_benchmarks.py
        └── benchmark_data/
            └── baseline.json  # 基线数据
```

**CI/CD集成**:
```yaml
# .github/workflows/benchmarks.yml
name: Performance Benchmarks

on:
  pull_request:
    branches: [develop, main]
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点运行

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run benchmarks
        run: |
          uv run poe test -m benchmark --benchmark-compare

      - name: Check for regressions
        run: |
          # 对比baseline.json，检测>10%的性能下降
          python scripts/check_benchmark_regression.py
```

---

### Layer 2: 真实使用日志回放（Usage Log Replay）

**目标**: 记录Dogfooding期间的真实调用，定期回放评估

**实现**:
```python
# src/evolvai/tpst/usage_logger.py

class UsageLogger:
    """记录真实使用场景的search调用"""

    def __init__(self, log_dir: Path = Path(".evolvai/usage_logs")):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_search_call(self, query: str, scope: str, result: SearchResult):
        """记录一次search调用"""

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "scope": scope,
            "tool_used": result["tool_used"],
            "hits_count": result["stats"]["hits_count"],
            "execution_time_ms": result["execution_time_ms"],
            "project_path": os.getcwd(),  # 哪个项目调用的
        }

        # 写入日志文件（按日期分片）
        log_file = self.log_dir / f"usage_{datetime.now().date()}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

# src/evolvai/tpst/usage_replayer.py

class UsageReplayer:
    """回放真实使用日志，评估性能变化"""

    def replay_logs(self, log_file: Path) -> BenchmarkReport:
        """回放一天的使用日志"""

        results = []

        with open(log_file) as f:
            for line in f:
                entry = json.loads(line)

                # 重新执行相同的search（在相同的项目路径）
                with chdir(entry["project_path"]):
                    new_result = safe_search(
                        query=entry["query"],
                        scope=entry["scope"]
                    )

                # 对比性能变化
                old_time = entry["execution_time_ms"]
                new_time = new_result["execution_time_ms"]

                results.append({
                    "query": entry["query"],
                    "old_time": old_time,
                    "new_time": new_time,
                    "change_pct": (new_time - old_time) / old_time * 100
                })

        return BenchmarkReport(results)

# 定期任务：每周回放
def weekly_replay_task():
    """每周回放上周的使用日志"""

    replayer = UsageReplayer()

    for log_file in Path(".evolvai/usage_logs").glob("usage_*.jsonl"):
        report = replayer.replay_logs(log_file)

        # 检测性能回归
        if report.avg_change_pct > 10:
            send_alert(f"Performance regression detected: {report.avg_change_pct:.1f}% slower")
```

**使用流程**:
```bash
# 1. Dogfooding期间自动记录（默认开启）
export EVOLVAI_LOG_USAGE=true
evolvai-agent  # 所有search调用自动记录到.evolvai/usage_logs/

# 2. 每周回放评估
evolvai-replay --logs .evolvai/usage_logs/usage_2025-11-*.jsonl

# 3. 生成性能趋势报告
evolvai-report --type performance-trend --output reports/weekly_trend.md
```

---

### Layer 3: 持续监控（TPST Tracker集成）

**目标**: 实时监控性能指标，异常检测

**实现**:
```python
# src/evolvai/tpst/tpst_tracker.py（已存在，增强）

class TPSTTracker:
    """TPST监控和分析"""

    def track_search_execution(
        self,
        query: str,
        tool_used: str,
        execution_time: float,
        baseline_time: Optional[float] = None  # 如果有对比数据
    ):
        """记录一次search执行"""

        record = TPSTRecord(
            tool_name="safe_search",
            operation=query,
            execution_time=execution_time,
            tokens_estimated=self._estimate_tokens(query),
            metadata={
                "tool_used": tool_used,
                "baseline_time": baseline_time,
                "speedup": baseline_time / execution_time if baseline_time else None
            }
        )

        self.records.append(record)

        # 实时异常检测
        if execution_time > self._get_p95_threshold():
            self._alert_slow_query(query, execution_time)

    def generate_weekly_report(self) -> TPSTReport:
        """生成每周性能报告"""

        return {
            "total_searches": len(self.records),
            "avg_execution_time": self._avg_time(),
            "p50_time": self._p50_time(),
            "p95_time": self._p95_time(),
            "p99_time": self._p99_time(),
            "tool_distribution": self._tool_distribution(),
            "slow_queries": self._get_slow_queries(top_n=10),
            "optimization_suggestions": self._suggest_optimizations()
        }
```

**Grafana Dashboard集成**（可选，Phase 2+）:
```yaml
# grafana/dashboards/evolvai-performance.json
{
  "dashboard": {
    "title": "EvolvAI Performance Monitoring",
    "panels": [
      {
        "title": "safe_search P50/P95/P99 Latency",
        "type": "graph",
        "metrics": [
          "evolvai.safe_search.latency.p50",
          "evolvai.safe_search.latency.p95",
          "evolvai.safe_search.latency.p99"
        ]
      },
      {
        "title": "Tool Usage Distribution",
        "type": "pie",
        "metrics": ["evolvai.safe_search.tool.{ripgrep,ugrep,grep}"]
      },
      {
        "title": "Speedup Trend (rg vs grep)",
        "type": "graph",
        "metrics": ["evolvai.safe_search.speedup"]
      }
    ]
  }
}
```

---

## 🎯 最终推荐方案

### MVP阶段（Level 2 Dogfooding）

**数据收集策略**: **策略D（模式切换）**

```python
# 配置文件：.evolvai/config.yml
benchmark:
  mode: sampling  # production | development | sampling
  sampling_rate: 0.1  # 10%采样
  log_usage: true  # 记录所有调用到usage_logs
  async_benchmark: false  # Phase 2再考虑

# 环境变量（覆盖配置文件）
# EVOLVAI_BENCHMARK_MODE=development  # 开发时完整对比
# EVOLVAI_BENCHMARK_MODE=production   # 生产时无对比
# EVOLVAI_BENCHMARK_MODE=sampling     # 长期监控采样
```

**基准测试套件**: **三层架构**

1. **Layer 1**: 单元基准测试（CI/CD自动运行）
   - 固定测试集（small/medium/large repos）
   - 固定搜索模式（高频/正则/多关键词）
   - 性能回归检测（>10%告警）

2. **Layer 2**: 使用日志回放（每周回放）
   - 记录Dogfooding的真实调用
   - 定期回放评估性能变化
   - A/B测试参数优化

3. **Layer 3**: 持续监控（TPST Tracker）
   - 实时性能指标（P50/P95/P99）
   - 异常检测和告警
   - 每周性能报告

---

## 📋 实施计划

### Story 2.1 实施中包含（4人天）

**Day 1-4**: 基础功能 + MVP数据收集
- ✅ 实现safe_search核心功能
- ✅ 集成策略D（模式切换）
- ✅ 基础TPST Tracker集成
- ✅ 开发模式完整对比（--benchmark flag）

### Story 2.1.1: 基准测试套件（额外2人天）

**Day 1**: Layer 1 单元基准测试
- 准备3个benchmark repos（small/medium/large）
- 编写基准测试用例（10-15个）
- CI/CD集成和回归检测

**Day 2**: Layer 2 使用日志回放
- 实现UsageLogger（记录真实调用）
- 实现UsageReplayer（回放评估）
- 定期任务脚本

### Phase 2: 高级监控（可选）

- Layer 3增强：Grafana Dashboard
- 策略C：异步对比（后台线程）
- 参数优化实验框架

---

## 🎯 修正后的产品定义建议

### baseline_comparison字段：条件返回

```python
def safe_search(
    query: str,
    scope: str = "**/*",
    execution_plan: Optional[ExecutionPlan] = None
) -> SearchResult:
    """根据benchmark mode决定是否返回对比数据"""

    mode = get_benchmark_mode()

    # 1. 运行ripgrep（所有模式）
    rg_result, rg_time = run_ripgrep(query, scope)

    baseline_comparison = None

    # 2. 根据模式运行对比
    if mode == BenchmarkMode.DEVELOPMENT:
        # 开发模式：完整对比
        grep_time = run_grep_fair(query, scope)
        baseline_comparison = {
            "grep_time_s": grep_time,
            "rg_time_s": rg_time,
            "speedup": f"{grep_time / rg_time:.1f}x"
        }
    elif mode == BenchmarkMode.SAMPLING:
        # 采样模式：10%记录到日志
        if random.random() < 0.1:
            grep_time = run_grep_fair(query, scope)
            log_benchmark_data(query, scope, rg_time, grep_time)

    # 3. 记录使用日志（所有模式）
    if os.getenv("EVOLVAI_LOG_USAGE") == "true":
        usage_logger.log_search_call(query, scope, rg_result)

    return {
        "tool_used": "ripgrep",
        "stats": rg_result["stats"],
        "top_matches": rg_result["top_matches"][:50],
        "execution_time_ms": rg_time * 1000,
        "baseline_comparison": baseline_comparison  # 可能为None
    }
```

### MVP阶段JSON Schema

```json
{
  "tool_used": "ripgrep",
  "stats": {
    "hits_count": 127,
    "files_matched": 23
  },
  "top_matches": [...],  // 最多50个
  "execution_time_ms": 280,

  // 条件字段：只在development mode返回
  "baseline_comparison": {  // Optional
    "grep_time_s": 5.2,
    "rg_time_s": 0.28,
    "speedup": "18.6x"
  }
}
```

---

## 📊 数据收集和参数优化流程

### 完整流程图

```
┌─────────────────────────────────────────────────────┐
│ 1. Dogfooding使用（EVOLVAI_BENCHMARK_MODE=sampling） │
│    - 90%正常执行（用户体验好）                         │
│    - 10%采样对比（收集数据）                          │
│    - 100%记录使用日志（真实场景）                      │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 2. 每周回放分析                                      │
│    - 回放上周使用日志                                 │
│    - 对比性能变化（old_time vs new_time）            │
│    - 识别慢查询和异常模式                             │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 3. 参数优化实验                                      │
│    - A/B测试不同参数（timeout, max_files等）         │
│    - 评估TPST影响                                   │
│    - 选择最优参数组合                                │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ 4. 持续监控和改进                                    │
│    - TPST Tracker实时监控                           │
│    - 异常告警（P95 > threshold）                    │
│    - 每月性能报告和优化建议                           │
└─────────────────────────────────────────────────────┘
```

---

## ✅ 结论

### 原建议的问题

❌ "删除baseline_comparison + 专门测试套件"过于简化
❌ 没有考虑长期数据收集需求
❌ 没有具体的基准测试实施方案

### 修正后的方案

✅ **数据收集**: 策略D（模式切换） - 开发/生产/采样三种模式
✅ **基准测试**: 三层架构 - 单元测试 + 日志回放 + 持续监控
✅ **用户体验**: 生产模式无性能损失，采样模式90%正常
✅ **数据驱动**: 真实使用日志 + 定期回放 + 参数优化

### 实施优先级

**MVP（Story 2.1, 4人天）**:
- ✅ 模式切换（development/production/sampling）
- ✅ 基础TPST Tracker集成
- ✅ 使用日志记录

**Story 2.1.1（2人天）**:
- ✅ 单元基准测试套件
- ✅ 使用日志回放系统
- ✅ CI/CD集成

**Phase 2（可选）**:
- ⚠️ Grafana Dashboard
- ⚠️ 异步对比（后台线程）
- ⚠️ 高级参数优化框架

---

**感谢您的质疑！这个修正方案更完整、更实用。**
