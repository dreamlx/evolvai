---
type: decision
category: architecture
decision_id: ADR-002
status: accepted
date: 2025-10-27
related: [epic-003]
---

# ADR 002: 单仓库架构与Epic-003后期拆分策略

**状态**: [ACCEPTED]
**日期**: 2025-10-27
**决策者**: EvolvAI Team
**标签**: `Repository-Organization`, `Monorepo`, `Architecture`, `Epic-003`, `Scalability`

---

## 📋 背景 (Context)

### 问题描述

EvolvAI包含三个相对独立的Epic（Epic-001行为约束、Epic-002文档规范、Epic-003思维优化），需要决定代码仓库组织策略：

**核心问题**：
1. 是否应该为每个Epic创建独立的GitHub仓库？
2. 三个Epic之间有协同关系，如何平衡独立性与集成便利性？
3. Epic-003涉及企业级算力调度，是否需要特殊考虑？

**技术考量**：
- 开发顺序：Epic-001（基础工具箱）→ Epic-002（文档规范）→ Epic-003（思维优化）
- 依赖关系：三Epic是协同增强，不是强依赖（Epic-001独立可用）
- 商业模式：Epic-001/002开源获客，Epic-003可能需要企业级私有部署

### 业务影响

**单仓库方案**：
- ✅ 降低初期开发复杂度，快速迭代
- ✅ 便于三Epic协同测试和集成
- ❌ 可能限制Epic-003的企业级部署灵活性

**多仓库方案**：
- ✅ 各Epic独立演进，清晰边界
- ✅ 便于独立发版和商业化授权
- ❌ 增加跨仓库集成复杂度
- ❌ 早期开发效率降低

### 当前状况

- EvolvAI项目刚启动，代码量<5000行
- Epic-001/002预计2-4周完成，Epic-003需要2-3个月
- 团队规模：1-2人，需要最大化开发效率
- Epic-003的企业级算力调度功能在Month 2-3才会启动

---

## 🎯 决策 (Decision)

### 选择的方案

**阶段性策略：先单仓库，Epic-003后期按需拆分**

**Phase 1（当前 - Month 2）：单仓库架构**
```
evolvai/
├── src/evolvai/
│   ├── constraints/      # Epic-001: 行为约束系统
│   │   ├── safe_search.py
│   │   ├── safe_edit.py
│   │   └── safe_exec.py
│   ├── standards/        # Epic-002: 项目规范服务
│   │   ├── doc_suggest.py
│   │   ├── doc_validate.py
│   │   └── doc_template.py
│   └── got/              # Epic-003: Graph-of-Thought引擎
│       ├── session.py
│       ├── event_store.py
│       └── parallel.py
├── tests/
└── docs/
```

**Phase 2（Month 2+，触发条件：Epic-003企业级功能开发）：拆分Epic-003**
```
evolvai/                  # 基础工具箱（开源）
└── src/evolvai/
    ├── constraints/      # Epic-001
    └── standards/        # Epic-002

evolvai-got-enterprise/   # 企业级思维引擎（可选私有）
└── src/evolvai_got/
    ├── scheduler/        # 算力调度
    ├── distributed/      # 分布式部署
    └── enterprise/       # 企业级功能
```

### 核心理由

1. **YAGNI原则**（You Aren't Gonna Need It）：不提前设计复杂的多仓库架构
2. **渐进式复杂度**：从简单开始，复杂度按需增长
3. **商业模式适配**：基础开源 + 高级企业版，仓库结构匹配商业策略
4. **开发效率优先**：小团队早期聚焦功能实现，不在架构上过度设计

---

## 🔍 考虑的方案 (Considered Options)

### 方案A: 三个独立仓库（从一开始）

**描述**:
从项目启动就创建三个独立仓库：
- `evolvai-constraints` (Epic-001)
- `evolvai-standards` (Epic-002)
- `evolvai-got` (Epic-003)

**优点**:
- ✅ 清晰的模块边界，独立演进
- ✅ 便于独立发版和版本管理
- ✅ 符合微服务架构理念
- ✅ 便于后期商业化授权（Epic分别定价）

**缺点**:
- ❌ **集成测试复杂**：三Epic协同需要跨仓库测试
- ❌ **依赖管理繁琐**：需要管理三个package的依赖关系
- ❌ **开发效率低**：小团队需要频繁切换仓库，context switch成本高
- ❌ **共享代码重复**：公共工具、类型定义可能重复（需要额外的shared库）
- ❌ **文档分散**：架构文档、ADR、Epic关系分散在三个仓库

**选择原因**: ❌ **不选择**
虽然长期看边界清晰，但对于早期1-2人团队，管理三个仓库的开销远大于收益。Epic-001/002/003的协同关系强，分离反而增加集成成本。

---

### 方案B: 完全单仓库（永久）

**描述**:
所有Epic永久保持在单一仓库`evolvai/`中，包括Epic-003的企业级功能。

**优点**:
- ✅ **极简架构**：永远只有一个仓库，管理成本最低
- ✅ **集成便利**：所有代码在同一codebase，测试和调试简单
- ✅ **共享基础设施**：工具、测试框架、CI/CD完全共享
- ✅ **文档统一**：所有ADR、架构文档集中管理

**缺点**:
- ❌ **商业模式受限**：开源与企业版代码混在一起，授权管理复杂
- ❌ **部署灵活性差**：Epic-003企业级需要独立部署，单仓库限制灵活性
- ❌ **访问控制困难**：企业级代码与开源代码在同一仓库，权限管理复杂
- ❌ **规模膨胀**：随着Epic-003企业级功能增加，仓库会变得臃肿

**选择原因**: ❌ **不选择**
虽然简单，但忽略了Epic-003企业级功能的特殊性。企业级算力调度、分布式部署等功能与基础工具箱的定位不同，长期混在一起不利于商业化。

---

### 方案C: 单仓库 + Epic-003后期拆分 ⭐

**描述**:
- **Phase 1（Month 0-2）**：单仓库`evolvai/`包含所有三个Epic
- **Phase 2（Month 2+）**：当Epic-003启动企业级功能开发时，拆分为：
  - `evolvai/` - 基础工具箱（Epic-001 + Epic-002 + Epic-003核心引擎）
  - `evolvai-got-enterprise/` - 企业级思维引擎（算力调度、分布式部署）

**优点**:
- ✅ **早期效率高**：单仓库开发，快速迭代
- ✅ **按需复杂化**：只在确实需要时才拆分，不提前设计
- ✅ **商业模式适配**：开源基础版 + 企业增强版，仓库结构匹配
- ✅ **部署灵活**：企业版可独立部署、定价、授权
- ✅ **清晰边界**：基础引擎（开源）vs 企业调度（商业），边界明确
- ✅ **兼容性保持**：基础版仍可单独使用，企业版作为可选增强

**缺点**:
- ❌ **拆分成本**：Month 2需要进行仓库拆分，迁移代码和CI/CD
- ❌ **依赖管理变化**：拆分后`evolvai-got-enterprise`依赖`evolvai`
- ❌ **历史记录分离**：拆分后Git历史需要特殊处理

**选择原因**: ✅ **选择**
平衡了早期开发效率与长期商业化需求：
- Phase 1集中精力实现功能，不分散在架构设计
- Phase 2按商业模式自然拆分，边界清晰
- 符合YAGNI原则，复杂度按需增长
- 支持"开源获客 + 企业增值"的商业路径

---

## ⚖️ 决策权衡 (Trade-offs)

### 短期影响（0-2个月）

**正面**:
- ✅ **开发效率最大化**：单仓库无需管理多个项目，专注功能实现
- ✅ **集成测试简单**：三Epic在同一codebase，协同测试零成本
- ✅ **文档集中**：所有ADR、Epic关系文档统一维护
- ✅ **CI/CD简化**：一套pipeline覆盖所有Epic

**负面**:
- ❌ **未来拆分预期**：团队需要预期Month 2可能的拆分工作
- ❌ **代码耦合风险**：需要有意识保持Epic间边界清晰

### 长期影响（2-12个月）

**正面**:
- ✅ **商业模式清晰**：基础版开源（获客）+ 企业版商业（盈利）
- ✅ **部署灵活**：企业版可独立部署、定价、私有化
- ✅ **访问控制明确**：开源代码公开，企业代码可选私有
- ✅ **规模可控**：基础版保持轻量，企业版独立膨胀

**负面**:
- ❌ **拆分成本**：Month 2需要1-2周进行仓库拆分和CI/CD迁移
- ❌ **依赖管理**：拆分后需要管理`evolvai-got-enterprise`对`evolvai`的依赖
- ❌ **版本同步**：两个仓库的版本发布需要协调

---

## 🎯 后果 (Consequences)

### 技术后果

**正面**:
1. **简洁架构**：早期避免过度设计，专注核心功能
2. **清晰边界**：拆分后基础引擎vs企业调度边界明确
3. **兼容性**：基础版永久开源，企业版作为可选增强

**负面**:
1. **拆分工程**：Month 2需要投入1-2周进行拆分
2. **依赖管理**：拆分后增加跨仓库依赖管理复杂度

### 团队后果

**正面**:
1. **效率提升**：早期单仓库开发，减少context switch
2. **学习成本低**：团队不需要一开始就学习多仓库管理
3. **渐进式成长**：随着项目成熟，团队能力同步提升

**负面**:
1. **拆分学习**：Month 2需要学习仓库拆分最佳实践
2. **规范意识**：需要有意识保持Epic间代码边界清晰

### 业务后果

**正面**:
1. **快速验证**：单仓库加速MVP上市（Week 2-3）
2. **商业路径清晰**：开源基础版获客 → 企业版变现
3. **灵活定价**：企业版可独立定价和授权
4. **部署选择**：企业客户可选SaaS或私有部署

**负面**:
1. **拆分时机风险**：如果拆分过早或过晚，可能影响商业化节奏

---

## 📊 度量指标 (Metrics)

### 成功指标

**Phase 1（单仓库阶段）**:
- 开发效率：Story平均完成时间 < 3天
- 集成测试覆盖率 ≥ 85%
- 跨Epic接口稳定性（无破坏性变更）

**Phase 2（拆分后）**:
- 拆分迁移时间 ≤ 2周
- 基础版独立可用（无企业版依赖）
- 企业版兼容性（支持基础版所有功能）

### 监控方式

**代码边界监控**:
- 每周检查：Epic间import关系，避免循环依赖
- 定期审查：公共接口稳定性，准备拆分

**拆分触发条件**:
- Epic-003启动企业级算力调度功能开发
- 企业版功能代码量 > 基础版的50%
- 有企业客户明确需求私有部署

---

## 🔗 相关决策 (Related Decisions)

### 依赖的ADR
- [ADR-001](./001-graph-of-thought-over-sequential-thinking.md) - Epic-003技术选型（GoT引擎）
- ADR-003（待创建）- Epic-003企业级功能范围定义

### 被依赖的ADR
- 未来的部署架构ADR将依赖本决策（开源vs企业版部署）

### 相关文档
- [Three Epics Relationship](../../product/roadmap/three-epics-relationship.md) - 三Epic协同关系
- [Metrics Reference](../../product/specs/metrics-reference.md) - TPST指标定义

---

## 📚 参考资料 (References)

### 仓库组织最佳实践
- [Monorepo vs Polyrepo - Martin Fowler](https://martinfowler.com/bliki/MonolithFirst.html)
- [Google's Monorepo Philosophy](https://cacm.acm.org/magazines/2016/7/204032-why-google-stores-billions-of-lines-of-code-in-a-single-repository/fulltext)
- [Splitting a Repository - GitHub Docs](https://docs.github.com/en/get-started/using-git/splitting-a-subfolder-out-into-a-new-repository)

### 开源商业化模式
- [Open Core Business Model](https://en.wikipedia.org/wiki/Open-core_model)
- [MongoDB Open Source Strategy](https://www.mongodb.com/licensing/server-side-public-license)

---

## 📝 备注 (Notes)

### 实施建议

**Phase 1 当前阶段（单仓库开发）**:

**代码组织规范**:
```python
# 保持Epic间清晰边界
src/evolvai/
├── constraints/         # Epic-001独立模块
│   ├── __init__.py
│   └── ...
├── standards/          # Epic-002独立模块
│   ├── __init__.py
│   └── ...
├── got/                # Epic-003独立模块
│   ├── __init__.py
│   └── core/          # 核心引擎（拆分后保留）
│   └── enterprise/    # 企业功能（拆分后移出）
└── shared/            # 共享工具（拆分后成为evolvai-core）
```

**依赖原则**:
- ✅ Epic-001/002可以依赖`shared/`
- ✅ Epic-003可以依赖Epic-001/002的公共接口
- ❌ 避免Epic-001 ↔ Epic-002循环依赖
- ❌ 企业功能不应依赖基础Epic实现细节

**Phase 2 拆分阶段（Month 2触发）**:

**拆分步骤**:
1. **准备**（Week 1）:
   - 识别Epic-003中的核心vs企业代码
   - 设计`evolvai-got-enterprise`的API接口
   - 准备Git拆分脚本（保留历史）

2. **执行**（Week 2）:
   - 使用`git filter-repo`拆分Epic-003企业代码
   - 创建`evolvai-got-enterprise`仓库
   - 更新`evolvai`的pyproject.toml（移除企业依赖）
   - 配置CI/CD（两个仓库独立pipeline）

3. **验证**（Week 3）:
   - 测试基础版独立可用
   - 测试企业版兼容性
   - 更新文档和部署指南

### 潜在风险

**风险1: 过早拆分**
- **表现**：在Epic-003企业功能尚未成熟时就拆分
- **后果**：拆分后频繁需要跨仓库协调，效率降低
- **缓解**：严格遵循拆分触发条件，不提前行动

**风险2: 拆分延迟**
- **表现**：Epic-003企业功能已经很大，但仍在单仓库
- **后果**：代码耦合严重，拆分难度指数级增长
- **缓解**：设置代码量阈值监控（企业代码>5000行触发告警）

**风险3: 边界不清**
- **表现**：Epic间相互依赖，难以解耦
- **后果**：拆分时需要大量重构，风险高
- **缓解**：每月代码审查，检查Epic间依赖关系，及时重构

**风险4: 历史记录丢失**
- **表现**：拆分后Git历史断裂，难以追溯
- **后果**：代码考古困难，影响维护
- **缓解**：使用`git filter-repo`保留历史，在README中记录拆分点

### 回滚计划

**如果拆分后出现严重问题**:

1. **短期应急**（24小时内）:
   - 将企业版代码临时合并回`evolvai/`主仓库
   - 继续单仓库开发，推迟拆分

2. **问题诊断**（1周）:
   - 分析拆分失败原因（依赖管理？API设计？）
   - 识别需要修复的技术债务

3. **重新拆分**（2-4周后）:
   - 修复识别的问题
   - 准备更完善的拆分方案
   - 执行第二次拆分

**最坏情况（拆分完全失败）**:
- 永久保持单仓库，但在内部严格保持Epic-003企业代码的目录隔离
- 通过CI/CD和部署脚本实现"逻辑拆分"（同一仓库，不同部署产物）
- 使用Git submodules或subtree作为中间方案

---

**创建日期**: 2025-10-27
**最后审查**: 2025-10-27
**下次审查**: 2025-12-27（Month 2开始Epic-003企业级开发时）
