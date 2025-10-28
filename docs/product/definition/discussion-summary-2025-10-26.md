# EvolvAI 项目讨论总结

**日期**: 2025-10-26
**状态**: ✅ 讨论定稿，进入实施阶段

---

## 🎯 **核心定位确定**

### **产品定位演进**
```
初始 → "AI工具导师"
最终 → "AI行为约束引擎"

EvolvAI = AI行为宪法 + 工具智能 + TPST优化器
```

### **独特价值**
> 用最少的tokens，完成可验证的真实改动

### **核心突破**
- **范式转移**: 从"提示词工程"到"行为工程"
- **物理删除**: 错误路径根本不存在（接口层约束）
- **工具确定性**: 工具智能 > 语言推理

---

## 📊 **北极星指标：TPST**

### **Tokens Per Solved Task**
```python
TPST = (input + output + tool_call) / solved_tasks

目标: 相比传统AI助手降低50%+
MVP: 降低30%+
```

### **配套指标**
- **First-Pass Success Rate**: >75% (MVP), >90% (Phase 2)
- **Model Hops**: <3 轮交互
- **Waste Ratio**: <10% 失败重试
- **Tool Offload Ratio**: >80% 本地计算
- **Search Speedup**: >5x (rg vs grep)

---

## 🏗️ **技术架构关键决策**

### **1. ExecutionPlan宪法系统**
- ✅ JSON Schema强制约束
- ✅ 自动拒绝机制（缺dry_run/validation/rollback）
- ✅ 分批处理策略（max_changes_per_batch）
- ✅ Scope强制黑名单（.git/node_modules自动排除）

### **2. safe_edit: Patch-First架构（关键改造）**
```
❌ 错误方案: 依赖sd --preview输出
✅ 正确方案: 自己生成统一diff + git apply

工作流程:
1. rg -l 找候选文件
2. difflib 生成统一diff
3. 保存 patch_id -> patch_content
4. git apply --3way 应用patch
```

**为什么Patch-First**:
- propose和apply完全一致
- 支持三方合并
- 不依赖工具的preview稳定性

### **3. Git Worktree策略（关键改造）**
```bash
✅ 使用: git worktree add -b evolvai/<id> .worktrees/<id> HEAD
❌ 不用: git checkout -b

优势:
- 主工作区不污染
- 支持并行任务
- 失败自动隔离
- 清理更简单
```

### **4. safe_search: 公平基线对比**
```bash
# 确保grep和rg用相同文件集
git ls-files -z | xargs -0 grep -nE "pattern"
git ls-files -z | xargs -0 rg -n "pattern"

# 对比实际执行时间
```

### **5. safe_exec: 进程组管理**
```python
# 创建新进程组
preexec_fn=os.setsid

# 超时杀整个进程树
os.killpg(os.getpgid(pid), signal.SIGTERM)
```

---

## 🚀 **MVP 2周计划**

### **Week 1: 核心约束 + Patch-First**
- Day 1-2: ExecutionPlan Schema（增强版）
- Day 3-4: safe_search（公平基线）
- Day 5-7: safe_edit（Patch-First + worktree）

### **Week 2: MCP集成 + 演示**
- Day 8-9: MCP服务端点（Claude优先）
- Day 10: safe_exec（进程组管理）
- Day 11-12: TPST审计系统
- Day 13-14: 英雄场景演示

### **英雄场景**
1. **大仓安全重命名** (pytest)
   - propose→diff→apply流程
   - TPST对比显示

2. **智能搜索** (fastapi)
   - rg vs grep性能对比
   - JSON统计输出

3. **性能基准** (superset)
   - 大仓搜索压力测试
   - 时间和命中率统计

---

## 📦 **基线仓库选择**

| 规模 | 仓库 | 用途 |
|------|------|------|
| 小 | pytest | 快速回归测试 |
| 中 | fastapi | 常见技术栈验证 |
| 大 | superset | 性能压力测试 |

---

## 🎯 **MVP成功标准**

### **必达指标**
```yaml
✅ ExecutionPlan强制约束生效 100%
✅ safe_search返回JSON（不返回大文本）
✅ safe_edit的propose→apply流程完整
✅ Git worktree隔离执行
✅ Claude MCP集成成功
✅ 搜索速度提升 ≥5x
✅ TPST降低 ≥30%
✅ 一次成功率 ≥75%
```

### **Phase 2目标**
```yaml
⏳ TPST降低 ≥50%
⏳ 一次成功率 ≥90%
⏳ AST级安全
⏳ 小模型路由
```

---

## 🛡️ **关键风险与对策**

### **Risk 1: 大diff冲突**
- **对策**: 分批≤200处，git apply --3way

### **Risk 2: Token度量**
- **对策**: MVP用代理指标，Phase 2接真实API

### **Risk 3: 工具依赖缺失**
- **对策**: 一键安装 + 降级策略 + Docker镜像

### **Risk 4: 约束太强**
- **对策**: 提供"研究模式"，仍强制验证

---

## ✅ **关键决策确认**

### **Q1: Comby优先级？**
**A**: ✅ 检测到comby则优先，否则patch-first，MVP不强制

### **Q2: 验证策略？**
**A**: ✅ MVP支持语法检查+pytest/jest，AST级Phase 2

### **Q3: 基线仓库？**
**A**: ✅ pytest/fastapi/superset

### **Q4: Token估算？**
**A**: ✅ MVP用model_hops估算，Phase 2接真实API

### **Q5: 索引系统？**
**A**: ✅ 编排现有工具（rg/fd/ctags），不造轮子

### **Q6: 小模型路由？**
**A**: ✅ 延后到Phase 2，MVP聚焦工具智能

---

## 📚 **核心术语**

| 术语 | 定义 |
|------|------|
| TPST | Tokens Per Solved Task - 完成任务的token效率 |
| 行为工程 | 通过接口约束AI行为，而非提示词说教 |
| Patch-First | 先生成diff，再git apply确保一致性 |
| Tool IQ | AI选择和使用开发工具的能力 |
| Model Hops | 完成任务所需的模型交互轮数 |

---

## 🎪 **产品差异化**

### **vs Vibe Coding阵营**
```
他们: 更多上下文 → 更智能对话
我们: 更少对话 → 更多执行

他们: 注入代码，多轮交互
我们: 约束行为，工具智能

他们: 对话质量
我们: TPST + 执行成功率
```

---

## 💰 **商业化方向**

### **护城河**
1. **数据壁垒**: 任务执行审计库
2. **工具适配壁垒**: macOS/zsh/GNU-BSD差异
3. **策略壁垒**: Tool IQ决策引擎
4. **集成壁垒**: MCP深度集成

### **定价策略**
- **个人**: 免费基础版 + $19/月专业版
- **团队**: $49/user/月
- **企业**: 定制报价

---

## 📈 **后续Phase预览**

### **Phase 2: 最小上下文 (3-4周)**
- ContextPack引擎
- 小模型路由
- LSIF索引
- TPST→50%

### **Phase 3: Tool IQ (4-6周)**
- 环境指纹
- 微基准选择
- 团队策略
- 持久化学习

---

## 🎉 **讨论成果**

### **达成共识**
✅ 产品定位清晰（行为工程）
✅ 北极星指标明确（TPST）
✅ 技术架构完整（三大安全器）
✅ MVP计划可行（2周交付）
✅ 风险对策充分（5大风险）

### **关键文档**
- ✅ `docs/product-definition-v1.md` - 完整产品定义
- ✅ `docs/discussion-summary-2025-10-26.md` - 本文档

### **下一步行动**
1. 初始化项目结构
2. 设置开发环境
3. Week 1 Day 1开始实施
4. 每日同步进度

---

**讨论状态**: ✅ 完成定稿
**准备状态**: ✅ 可进入实施
**信心指数**: ⭐⭐⭐⭐⭐

---

**END OF SUMMARY**
