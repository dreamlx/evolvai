# EvolvAI 产品定义文档 v1.0

**文档日期**: 2025-10-26
**版本**: 1.0
**状态**: MVP设计定稿

---

## 🎯 产品定位

### **从"AI工具导师"到"AI行为约束引擎"**

**EvolvAI = AI行为宪法 + 工具智能 + TPST优化器**

### **核心价值主张**
> 用最少的tokens，完成可验证的真实改动

### **独特壁垒**
- 物理删除错误路径 > 语言提示
- 工具确定性 > 语言不确定性
- 行为工程 > 提示词工程

---

## 🔥 **范式转移：从"说教AI"到"约束AI行为架构"**

### **传统范式的致命缺陷**
```
❌ "提示词工程"依赖模型的"自觉性"
❌ 期望AI通过"学习"避免错误
❌ 用更多tokens换取"更谨慎的回答"
❌ 每次对话都要重新"教育"AI
```

### **EvolvAI的"行为工程"范式**
```
✅ 接口层物理删除错误路径
✅ 强制dry-run→diff→apply流程
✅ JSON Schema约束而非道德劝说
✅ 工具智能优先而非语言推理
✅ 一次约束，永久生效
```

---

## 📊 **北极星指标体系**

### **Primary Metric: TPST (Tokens Per Solved Task)**
```python
TPST = (input_tokens + output_tokens + tool_call_tokens) / solved_tasks

目标：相比传统AI助手降低50%+
MVP目标：降低30%+
```

### **Secondary Metrics**
```yaml
success_metrics:
  first_pass_success_rate: ">75%"  # MVP: 75%, Phase 2: 90%
  model_hops_per_task: "<3"        # 模型交互轮数
  waste_ratio: "<10%"               # 失败重试token占比
  tool_offload_ratio: ">80%"       # 本地工具计算占比
  rollback_rate: "<5%"              # 回滚操作比例

performance_metrics:
  search_speedup: ">5x"             # rg vs grep
  p50_completion_time: "对比基线"
  p95_completion_time: "对比基线"
  cold_start_time: "<2s"
```

---

## 🏗️ **三层约束体系架构**

### **Layer 1: 接口层约束（物理删除错误路径）**
```python
# 错误选项根本不存在
class SafeEditor:
    # ❌ 没有"直接写入"方法
    # ✅ 只有propose→diff→apply路径

    def propose_edit() -> PatchProposal:
        """生成diff，不执行"""
        pass

    def apply_edit(patch_id: str) -> ApplyResult:
        """只接受patch_id，无法绕过"""
        pass
```

### **Layer 2: 控制器约束（执行前强制验证）**
```python
class ExecutionPlan(BaseModel):
    # 所有字段都是required，缺一不可
    dry_run: DryRun = Field(required=True)
    validation: Validation = Field(required=True)
    rollback: Rollback = Field(required=True)
    limits: Limits = Field(required=True)

    def validate_constraints(self) -> tuple[bool, List[str]]:
        """自动拒绝不符合约束的计划"""
        pass
```

### **Layer 3: 激励层约束（成功模式记忆强化）**
```python
class BehaviorOptimizer:
    def learn_from_execution(self, execution_record: dict):
        """记录成功模式，强化最优路径"""
        pass
```

---

## 🔧 **核心技术架构**

### **1. ExecutionPlan宪法系统**

**设计原则**：
- JSON Schema强制约束
- 自动拒绝机制
- 分批处理策略
- 工具智能决策

**关键字段**：
```python
{
    "intent": "批量替换user为username",
    "scope": {
        "include_globs": ["src/**/*.py"],
        "exclude_globs": [".git/**", "node_modules/**"]  # 强制黑名单
    },
    "tools": {
        "search": "rg",      # 枚举类型
        "replace": "comby"   # 枚举类型
    },
    "limits": {
        "max_files": 20,
        "max_lines": 100,
        "max_hunks_per_file": 10,
        "timeout_s": 30
    },
    "batch": {
        "enabled": true,
        "max_changes_per_batch": 200,
        "auto_split": true
    },
    "dry_run": {
        "sample_preview_n": 10,
        "required": true  # 强制必须
    },
    "validation": {
        "commands": ["pytest", "mypy"],
        "required": true,  # 强制必须
        "auto_run_tests": true
    },
    "rollback": {
        "worktree_path": ".worktrees/evolvai",
        "branch_prefix": "evolvai",
        "auto_revert_on_fail": true
    }
}
```

### **2. safe_search：工具智能编排**

**核心理念**：编排现有工具，不造轮子

**工具选择策略**：
```python
优先级：ripgrep > ugrep > grep
- ripgrep: 极速JSON输出，尊重ignore规则
- ugrep: 高性能替代方案
- grep: 降级兜底（提示性能损失）
```

**公平基线对比**：
```python
# 确保grep和rg使用相同文件集
git ls-files -z | xargs -0 grep -nE "pattern"
git ls-files -z | xargs -0 rg -n "pattern"

# 对比指标：
- 搜索时间（real time）
- 文件命中数
- 结果准确性
```

**返回结构**：
```json
{
    "tool_used": "ripgrep",
    "stats": {
        "hits_count": 127,
        "files_matched": 23
    },
    "top_matches": [
        {"file": "src/auth.py", "line": 45, "snippet": "..."}
    ],
    "execution_time_ms": 280,
    "baseline_comparison": {
        "grep_time_s": 5.2,
        "rg_time_s": 0.28,
        "speedup": "18.6x"
    }
}
```

### **3. safe_edit：Patch-First架构**

**关键改造**：
- ❌ 不依赖sd的--preview输出
- ✅ 自己生成统一diff
- ✅ 用git apply确保一致性

**工作流程**：
```
1. propose_replace:
   ├─ rg -l 找候选文件
   ├─ 读取原文件内容
   ├─ 执行替换生成新内容
   ├─ difflib生成unified diff
   └─ 保存patch_id -> patch_content

2. apply_edit(patch_id):
   ├─ 创建git worktree
   ├─ git apply --3way 应用patch
   ├─ git commit 提交变更
   └─ 返回commit SHA和branch
```

**Comby优先级**：
```python
if has_tool("comby"):
    # comby原生支持统一diff
    use_comby_diff()
else:
    # patch-first策略
    use_unified_diff_generation()
```

### **4. Git Worktree策略**

**为什么用worktree**：
- ✅ 主工作区不被污染
- ✅ 支持并行任务
- ✅ 安全隔离
- ✅ 失败自动回滚

**工作流程**：
```bash
# 创建worktree
git worktree add -b evolvai/patch_abc123 .worktrees/patch_abc123 HEAD

# 在worktree中应用变更
cd .worktrees/patch_abc123
git apply --3way .evolvai_patch
git add -A
git commit -m "EvolvAI: patch_abc123"

# 清理（成功后）
git worktree remove .worktrees/patch_abc123

# 回滚（失败后）
git worktree remove --force .worktrees/patch_abc123
```

### **5. safe_exec：进程组管理**

**关键技术**：
```python
# 创建新进程组，避免僵尸进程
subprocess.run(
    command,
    preexec_fn=os.setsid  # 新会话
)

# 超时杀整个进程树
os.killpg(os.getpgid(pid), signal.SIGTERM)
```

**输出截断**：
```python
# 前50行 + 后50行 + 省略统计
head_lines = stdout[:50]
tail_lines = stdout[-50:]
omitted = len(stdout) - 100

output = "\n".join(head_lines)
output += f"\n... ({omitted} lines omitted) ...\n"
output += "\n".join(tail_lines)
```

---

## 🚀 **MVP 2周实施计划**

### **Week 1: 核心约束层 + Patch-First**

#### **Day 1-2: ExecutionPlan宪法系统**
**交付物**：
- `src/evolvai/core/execution_plan.py`
- JSON Schema定义（增强版）
- 自动验证器
- 20+测试用例

**验收标准**：
- ✅ 拒绝无dry_run的计划
- ✅ 拒绝无validation的计划
- ✅ 超限自动分批
- ✅ scope强制黑名单注入

#### **Day 3-4: safe_search智能编排**
**交付物**：
- `src/evolvai/tools/safe_search.py`
- ripgrep JSON包装
- 公平基线对比脚本
- 统计输出（无大文本）

**验收标准**：
- ✅ 智能选择rg/ugrep/grep
- ✅ 返回JSON统计
- ✅ 搜索速度>5x
- ✅ 公平基线可复现

#### **Day 5-7: safe_edit Patch-First**
**交付物**：
- `src/evolvai/tools/safe_edit.py`
- 统一diff生成
- Git worktree管理
- patch_id机制

**验收标准**：
- ✅ propose生成统一diff
- ✅ apply只接受patch_id
- ✅ worktree隔离执行
- ✅ 失败自动回滚

### **Week 2: MCP集成 + 演示**

#### **Day 8-9: MCP服务端点**
**交付物**：
- `src/evolvai/mcp_server.py`
- 三大工具MCP端点
- Claude Desktop集成

**验收标准**：
- ✅ MCP工具注册成功
- ✅ Claude可调用工具
- ✅ JSON输入输出正确

#### **Day 10: safe_exec进程管理**
**交付物**：
- `src/evolvai/tools/safe_exec.py`
- 进程组管理
- 超时熔断
- 输出截断

**验收标准**：
- ✅ 超时杀进程组
- ✅ 输出智能截断
- ✅ 资源使用统计

#### **Day 11-12: TPST审计系统**
**交付物**：
- `src/evolvai/audit/tpst_tracker.py`
- 任务记录数据库
- 指标计算引擎
- 简单Web面板

**验收标准**：
- ✅ 记录model_hops
- ✅ 计算tool_offload_ratio
- ✅ 对比基线显示

#### **Day 13-14: 英雄场景演示**
**交付物**：
- 演示脚本
- 基线对比报告
- 视频录制

**场景**：
1. 大仓安全重命名（pytest）
2. 智能搜索（fastapi）
3. 性能对比（superset）

---

## 📦 **交付物清单**

### **核心代码**
```
src/evolvai/
├── core/
│   └── execution_plan.py      # ExecutionPlan Schema + 验证
├── tools/
│   ├── safe_search.py          # rg/fd智能编排
│   ├── safe_edit.py            # Patch-First编辑器
│   └── safe_exec.py            # 进程组管理执行器
├── audit/
│   └── tpst_tracker.py         # TPST审计追踪
└── mcp_server.py               # MCP集成服务
```

### **测试与基准**
```
tests/
├── unit/
│   ├── test_execution_plan.py  # 20+验证场景
│   ├── test_safe_search.py     # 搜索工具测试
│   └── test_safe_edit.py       # 编辑流程测试
├── integration/
│   └── test_mcp_integration.py # MCP端到端测试
└── benchmarks/
    ├── search_baseline.py       # grep vs rg公平对比
    ├── replace_baseline.py      # sed vs sd对比
    └── repos/
        ├── pytest/              # 小型仓库
        ├── fastapi/             # 中型仓库
        └── superset/            # 大型仓库
```

### **文档**
```
docs/
├── product-definition-v1.md     # 本文档
├── technical-architecture.md    # 技术架构详细设计
├── mvp-implementation-guide.md  # MVP实施指南
└── api-reference.md             # MCP工具API文档
```

---

## 🎯 **MVP成功标准**

### **必达指标（硬性要求）**
```yaml
constraints:
  - ExecutionPlan强制约束生效 100%
  - safe_search返回JSON统计（不返回大文本）
  - safe_edit的propose→apply流程完整
  - Git worktree隔离执行
  - Claude MCP集成成功

performance:
  - 搜索速度提升 ≥5x (rg vs grep)
  - TPST降低 ≥30%
  - 一次成功率 ≥75%
  - Tool offload比例 ≥80%
```

### **可选指标（Phase 2目标）**
```yaml
stretch_goals:
  - TPST降低 ≥50%
  - 一次成功率 ≥90%
  - AST级安全合并
  - 小模型路由优化
```

---

## 🛡️ **风险与对策**

### **技术风险**

#### **Risk 1: 大diff应用冲突**
- **影响**: 批量替换可能导致合并冲突
- **对策**:
  - 分批处理（每批≤200处）
  - git apply --3way自动三方合并
  - 失败即停，生成人工确认任务

#### **Risk 2: Token度量争议**
- **影响**: MVP阶段拿不到真实token数据
- **对策**:
  - 使用代理指标（model_hops、时间）
  - 本地tokenizer估算
  - Phase 2接入真实API

#### **Risk 3: 工具依赖缺失**
- **影响**: 用户环境可能缺少rg/sd/comby
- **对策**:
  - 一键安装脚本
  - 降级策略（但提示性能损失）
  - 提供Docker镜像

### **产品风险**

#### **Risk 4: 约束太强，阻断探索**
- **影响**: 创意型任务受限
- **对策**:
  - 提供"研究模式"（放宽上下文）
  - 仍强制验证与临时分支
  - 明确适用场景边界

#### **Risk 5: 评测被质疑**
- **影响**: 基线对比不公平
- **对策**:
  - 公开基准脚本
  - 使用git ls-files统一文件集
  - 允许第三方复现实验

---

## 💰 **商业化路径**

### **目标用户分层**
1. **个人开发者**: 免费基础版 + 专业版订阅
2. **团队**: 按席位付费 + 企业级功能
3. **企业**: 私有部署 + 定制开发

### **定价策略**
```yaml
individual:
  free_tier:
    - 基础工具包装
    - 10次/月任务限制
    - 社区支持

  pro: $19/month
    - 无限任务
    - TPST优化引擎
    - 优先支持

team: $49/user/month
  - 团队行为策略
  - 审计报告
  - SSO集成

enterprise: 定制报价
  - 私有部署
  - 专属支持
  - 定制开发
```

### **护城河**
1. **数据壁垒**: 任务执行审计库（越用越准）
2. **工具适配壁垒**: macOS/zsh/GNU-BSD差异处理
3. **策略壁垒**: Tool IQ决策引擎（微基准学习）
4. **集成壁垒**: MCP深度集成（多IDE支持）

---

## 📈 **Phase 2-3路线图预览**

### **Phase 2: 最小上下文与小模型路由 (3-4周)**
- ContextPack最小上下文引擎
- 小模型路由决策器
- LSIF索引集成
- TPST优化到50%+

### **Phase 3: Tool IQ与个性化 (4-6周)**
- 环境指纹探测器
- 微基准自动选择
- 团队策略引擎
- 持久化偏好学习

---

## 🤝 **关键决策记录**

### **Decision 1: Patch-First架构**
- **决策**: 用difflib生成统一diff，git apply应用
- **原因**: 确保propose和apply完全一致
- **替代方案**: 依赖sd/comby的preview（不稳定）

### **Decision 2: Git Worktree策略**
- **决策**: 使用worktree而非checkout -b
- **原因**: 主工作区不污染，支持并行
- **替代方案**: 直接checkout（风险高）

### **Decision 3: TPST作为北极星**
- **决策**: Tokens Per Solved Task作为首要指标
- **原因**: 直接衡量AI效率，可量化对比
- **替代方案**: 任务完成时间（不够精准）

### **Decision 4: MVP不做索引**
- **决策**: 不从零构建语义索引
- **原因**: 编排现有工具更快，造轮子风险高
- **替代方案**: 自建索引（延期到Phase 2）

### **Decision 5: 小模型路由延后**
- **决策**: MVP不做模型路由优化
- **原因**: 早期重点是工具智能>语言推理
- **替代方案**: 立即做路由（复杂度高，收益不明显）

---

## 📝 **附录：核心术语表**

### **TPST (Tokens Per Solved Task)**
- 完成一个任务所消耗的总token数（输入+输出+工具调用）
- 越低越好，表示AI效率越高

### **行为工程 (Behavior Engineering)**
- 通过接口约束、控制器验证、激励强化来约束AI行为
- 区别于"提示词工程"（依赖AI自觉）

### **Patch-First架构**
- 先生成完整diff patch，再用git apply应用
- 确保propose和apply的一致性

### **Tool IQ (工具智商)**
- AI选择和使用开发工具的能力
- 包括工具选择、参数优化、性能预测

### **Model Hops**
- 完成任务所需的模型交互轮数
- 越少越好，表示任务规划更高效

### **Tool Offload Ratio**
- 本地工具计算占总计算的比例
- 越高越好，表示更少依赖语言推理

---

## ✅ **文档变更历史**

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| 1.0 | 2025-10-26 | 初始版本，MVP设计定稿 | EvolvAI Team |

---

**文档状态**: ✅ 已定稿，可进入实施阶段

**下一步行动**:
1. 创建GitHub仓库并初始化项目结构
2. 设置开发环境和CI/CD流程
3. 按照Week 1计划开始实施
4. 每日站会同步进度和风险

---

**END OF DOCUMENT**
