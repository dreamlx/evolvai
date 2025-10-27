# [ACTIVE] Epic 002: 项目规范即服务 (Project Standards as MCP)

**Epic ID**: EPIC-002
**创建日期**: 2025-10-27
**负责人**: EvolvAI Team
**状态**: [ACTIVE]
**优先级**: [P1]
**估算**: 10人天 (2周 MVP)

---

## 📋 Epic概述

### 问题陈述

**当前困境**：AI助手频繁违反项目文档规范
- 📄 文档随意创建在错误位置（项目根目录、临时文件夹）
- 🏷️ 命名不一致（my-notes.md, temp.md, 随意命名）
- 📝 结构缺失（缺少必填章节、业务价值说明）
- 🔄 反复返工（创建→纠正→重写，token浪费严重）

**根本原因**：
```
静态文档规范（CLAUDE.md, .structure.md）
    ↓
AI阅读但无强制力
    ↓
依赖"自觉遵守"，经常失败
    ↓
隐形token浪费大户
```

### 业务价值

**核心理念**：**规范即服务 > 规范即文档**

将项目最优实践从"静态文档"升级为"可执行的行为约束服务"，让AI**想违反也做不到**。

**直接收益**：
- **减少返工token浪费**：少走弯路，减少"错误创建→纠正→重写"循环
- **提高首次成功率**：通过原则驱动的指导，首次创建即符合规范
- **降低TPST**：预计减少文档相关token消耗40%（目标）
- **跨项目复用**：标准可继承、可组合，适用于任何项目

**战略价值**：
- 与Epic-001形成"行为工程"双引擎：代码操作约束 + 文档规范约束
- 可独立部署为通用MCP服务，扩展到企业级行为治理
- 建立"原则驱动 > 模板填空"的新范式

### 目标用户

- **AI助手**：需要遵守项目规范的Claude Code、Cursor、Copilot
- **开发者**：希望团队统一文档风格的技术负责人
- **企业组织**：需要多项目规范治理的组织架构师

---

## 🎯 成功指标

### TPST影响（主指标）

| 指标 | 基线 | MVP目标 | 最终目标 |
|------|------|---------|----------|
| **reduced_rework_tokens** | - | -30% | -40% |
| **document_creation_success_rate** | ~60% | 85% | 95% |
| **avg_tokens_per_doc_task** | 1200 | 900 | 750 |

**测量方式**：
```python
# 对比实验：同一文档任务
baseline_tokens = create_doc_without_standards()  # ~1200 tokens（反复纠正）
optimized_tokens = create_doc_with_standards()    # ~750 tokens（一次成功）
reduction = (baseline - optimized) / baseline     # 37.5%
```

### 规范遵守指标（质量）

| 指标 | MVP目标 | 最终目标 |
|------|---------|----------|
| **document_placement_accuracy** | 90% | 95% |
| **naming_convention_adherence** | 90% | 95% |
| **structure_completeness** | 85% | 90% |
| **principle_score_avg** | 0.7 | 0.8 |

### 用户体验指标

| 指标 | MVP目标 |
|------|---------|
| **setup_time** | <5分钟（init向导） |
| **false_positive_rate** | <5%（误报过严） |
| **waiver_rate** | <10%（需要豁免） |

---

## 📦 包含的Features

### Feature 1: MCP Standards Service Core
- **Feature ID**: FEATURE-004
- **描述**: 实现核心MCP服务端点和标准定义系统
- **估算**: 4人天
- **状态**: [Backlog]
- **包含内容**:
  - `standards.get()` - 获取合并后的项目规范
  - `doc.suggest_location()` - 智能位置建议
  - `doc.template()` - 原则驱动的模板生成
  - `doc.validate()` - 实时验证和纠正建议
  - `.project_standards.yml` 标准文件定义

### Feature 2: Git Guard Integration
- **Feature ID**: FEATURE-005
- **描述**: 实现pre-commit钩子和Git工作流守卫
- **估算**: 2人天
- **状态**: [Backlog]
- **包含内容**:
  - `git.guard.precommit()` - pre-commit钩子
  - 自动阻止不合规文档提交
  - 提供一键修复建议
  - 审计日志记录

### Feature 3: Principle-Based Validation
- **Feature ID**: FEATURE-006
- **描述**: 实现原则驱动的智能验证系统
- **估算**: 3人天
- **状态**: [Backlog]
- **包含内容**:
  - 规则引擎（regex, 结构检查）
  - 原则评分系统（小模型，≤100 tokens）
  - 可配置验证器（组织级+项目级）
  - 受控豁免机制（`doc.waive()`）

### Feature 4: Standards Composition
- **Feature ID**: FEATURE-007
- **描述**: 实现标准继承、合并、可视化系统
- **估算**: 1人天
- **状态**: [Backlog]
- **包含内容**:
  - 标准继承机制（组织级→项目级）
  - 冲突解决策略
  - `standards.diff()` - 可视化差异
  - Init向导（生成初始标准文件）

---

## 🏗️ 技术架构

### 核心组件

```
┌─────────────────────────────────────────┐
│         MCP Standards Service           │
├─────────────────────────────────────────┤
│  standards.get()        ← 标准解析      │
│  doc.suggest_location() ← 位置推荐      │
│  doc.template()         ← 模板生成      │
│  doc.validate()         ← 实时验证      │
│  git.guard.precommit()  ← Git守卫       │
├─────────────────────────────────────────┤
│       Standards Resolver                │
│  ├─ Organization defaults               │
│  ├─ Repository overrides                │
│  └─ Merge + Conflict resolution         │
├─────────────────────────────────────────┤
│       Validation Engine                 │
│  ├─ Rule checkers (regex, structure)   │
│  ├─ Principle scorer (small LM)         │
│  └─ Waiver manager                      │
├─────────────────────────────────────────┤
│       Integration Layer                 │
│  ├─ Pre-commit hooks                    │
│  ├─ IDE plugins                         │
│  └─ CI/CD gates                         │
└─────────────────────────────────────────┘
```

### 标准文件示例

```yaml
# .project_standards.yml
version: 1
extends:
  - "https://org-standards.company/tech.yml"  # 可选

documents:
  epic:
    location: "docs/product/epics/epic-{num}-{kebab}/"
    naming: "epic-{num}-{kebab}.md"
    required_sections:
      - "业务价值"
      - "成功指标"
      - "Features(3-5)"
    principles:
      - id: "why-over-what"
        desc: "解释为什么，而不只是列出做什么"
        checker:
          type: "regex_presence"
          patterns: ["业务价值", "影响"]

      - id: "tpst-oriented"
        desc: "量化TPST影响"
        checker:
          type: "regex_presence"
          patterns: ["TPST", "tokens", "token浪费"]

  adr:
    location: "docs/development/architecture/adrs/"
    naming: "{seq:03d}-{kebab}.md"
    required_sections: ["Context", "Decision", "Consequences"]

guards:
  root_allowlist: ["README.md", "CLAUDE.md", "pyproject.toml"]
  doc_dirs: ["docs/"]
  max_new_docs_per_pr: 10

validation:
  strict_mode: true  # dev可设false
  principle_threshold: 0.6
```

### MCP端点设计

#### 1. standards.get()
```json
// Request
{
  "project_path": "/path/to/project",
  "include_inherited": true
}

// Response
{
  "version": "1.0",
  "source": "merged",
  "documents": {...},
  "guards": {...},
  "inherited_from": ["org-defaults", "repo-local"]
}
```

#### 2. doc.suggest_location()
```json
// Request
{
  "doc_type": "epic",
  "title": "Tool Intelligence",
  "project_context": {
    "project_type": "technical_product",
    "team_size": "small",
    "development_stage": "mvp"
  }
}

// Response
{
  "suggested_path": "docs/product/epics/epic-002-tool-intelligence/",
  "naming_pattern": "epic-{num}-{kebab}",
  "required_sections": ["业务价值", "成功指标", "Features"],
  "guiding_principles": [
    {
      "id": "why-over-what",
      "desc": "解释为什么，而不只是列出做什么",
      "example": "✅ '降低TPST 30%' vs ❌ '实现缓存功能'"
    },
    {
      "id": "tpst-oriented",
      "desc": "量化TPST影响",
      "example": "✅ 'reduce_tokens: 1200→750' vs ❌ '提升性能'"
    }
  ],
  "outline": [
    "## 业务价值",
    "## 成功指标（TPST）",
    "## Features（3-5个）",
    "## 技术架构",
    "## 风险与对策（可选）"
  ]
}
```

#### 3. doc.validate()
```json
// Request
{
  "path": "docs/my-random-doc.md",
  "content_meta": {
    "sections": ["概述", "实现"],
    "word_count": 500
  }
}

// Response
{
  "ok": false,
  "violations": [
    {
      "rule": "wrong_location",
      "severity": "error",
      "message": "文档必须在docs/目录的子分类下",
      "suggested_fix": "docs/product/specs/my-random-doc.md"
    },
    {
      "rule": "missing_section:业务价值",
      "severity": "error",
      "message": "Epic必须包含'业务价值'章节",
      "hint": "解释为什么做这个，对用户/业务的价值"
    }
  ],
  "principle_scores": {
    "why-over-what": 0.4,  // 低于阈值0.6
    "tpst-oriented": 0.0   // 完全缺失
  },
  "overall_score": 0.2,
  "can_proceed": false
}
```

#### 4. git.guard.precommit()
```json
// Request
{
  "staged_files": [
    "docs/temp.md",
    "docs/product/epics/epic-002-project-standards/README.md"
  ]
}

// Response
{
  "ok": false,
  "blocked_files": [
    {
      "path": "docs/temp.md",
      "reason": "违反命名规范",
      "fix": "重命名为 docs/knowledge/lessons-learned/temp-notes.md"
    }
  ],
  "allowed_files": [
    "docs/product/epics/epic-002-project-standards/README.md"
  ],
  "action": "abort_commit",
  "message": "1个文件违反规范，请修复后重新提交"
}
```

---

## 🎯 原则评分检查器详细设计

### 设计理念

**核心原则**: 规则优先，小模型辅助

```
┌──────────────────────────────────────┐
│  规则引擎（Rule Engine）               │  ← 确定性检查，快速、可靠
│  ├─ 位置验证：regex匹配               │
│  ├─ 命名验证：pattern匹配              │
│  ├─ 结构验证：必填章节检查             │
│  └─ 格式验证：语法、链接有效性         │
├──────────────────────────────────────┤
│  原则评分器（Principle Scorer）        │  ← 语义检查，≤100 tokens
│  ├─ 小模型调用（GPT-3.5/Claude Haiku）│
│  ├─ 评分维度：why-over-what, tpst等   │
│  └─ 阈值判断：≥0.6通过                │
└──────────────────────────────────────┘
```

**策略**:
- **90%靠规则**：位置、命名、结构、格式等确定性检查
- **10%靠模型**：语义质量、原则遵守等需要理解的部分
- **小模型足够**：评分任务简单，无需大模型（降低成本和延迟）

---

### 规则引擎实现

#### 1. 位置验证器

```python
class LocationValidator:
    """位置规则验证"""
    def __init__(self, standards: ProjectStandards):
        self.standards = standards

    def validate(self, file_path: Path) -> ValidationResult:
        """验证文件位置是否符合规范"""
        # 检查是否在docs/目录下
        if not str(file_path).startswith("docs/"):
            return ValidationResult(
                ok=False,
                violations=[Violation(
                    rule="wrong_location",
                    severity="error",
                    message="文档必须在docs/目录下",
                    suggested_fix=f"docs/{file_path.name}"
                )]
            )

        # 检查是否在根目录白名单中
        if file_path.parent == Path("."):
            if file_path.name not in self.standards.guards.root_allowlist:
                return ValidationResult(
                    ok=False,
                    violations=[Violation(
                        rule="root_not_allowed",
                        severity="error",
                        message=f"项目根目录只允许: {', '.join(self.standards.guards.root_allowlist)}",
                        suggested_fix=self._suggest_category(file_path)
                    )]
                )

        # 检查文档类型匹配
        doc_type = self._detect_doc_type(file_path)
        if doc_type:
            expected_location = self.standards.documents[doc_type].location
            if not self._matches_pattern(file_path, expected_location):
                return ValidationResult(
                    ok=False,
                    violations=[Violation(
                        rule=f"wrong_location_for_{doc_type}",
                        severity="error",
                        message=f"{doc_type}必须在{expected_location}",
                        suggested_fix=self._generate_correct_path(file_path, doc_type)
                    )]
                )

        return ValidationResult(ok=True, violations=[])

    def _detect_doc_type(self, file_path: Path) -> Optional[str]:
        """从文件名检测文档类型"""
        name = file_path.name
        if name.startswith("epic-"):
            return "epic"
        elif re.match(r"\d{3}-", name):
            return "adr"
        elif name.startswith("story-"):
            return "story"
        # ... 更多类型
        return None

    def _suggest_category(self, file_path: Path) -> str:
        """根据文件名建议分类"""
        name = file_path.stem.lower()
        if "meeting" in name or "notes" in name:
            return f"docs/knowledge/lessons-learned/{file_path.name}"
        elif "test" in name or "benchmark" in name:
            return f"docs/testing/reports/{file_path.name}"
        else:
            return f"docs/knowledge/research/{file_path.name}"
```

#### 2. 结构验证器

```python
class StructureValidator:
    """文档结构验证"""
    def validate(
        self,
        content: str,
        doc_type: str,
        standards: ProjectStandards
    ) -> ValidationResult:
        """验证必填章节是否完整"""
        required_sections = standards.documents[doc_type].required_sections

        violations = []
        for section in required_sections:
            # 支持正则模式匹配
            if isinstance(section, str):
                pattern = rf"^##\s+{re.escape(section)}"
            else:
                pattern = section["pattern"]

            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                violations.append(Violation(
                    rule=f"missing_section:{section}",
                    severity="error",
                    message=f"缺少必填章节: {section}",
                    hint=self._get_section_hint(section)
                ))

        return ValidationResult(
            ok=len(violations) == 0,
            violations=violations
        )

    def _get_section_hint(self, section: str) -> str:
        """返回章节填写提示"""
        hints = {
            "业务价值": "解释为什么做这个功能，对用户/业务的价值",
            "成功指标": "量化的验收标准，尤其是TPST相关指标",
            "Features": "列出3-5个主要功能，每个包含描述和估算",
            "Context": "描述需要做出决策的技术问题或挑战",
            "Decision": "说明最终选择的技术方案和核心理由",
            "Consequences": "分析技术后果、团队后果、业务后果",
        }
        return hints.get(section, f"参考模板填写{section}章节")
```

---

### 原则评分器实现

#### 评分维度定义

```python
from pydantic import BaseModel, Field
from typing import List, Literal

class PrincipleDefinition(BaseModel):
    """原则定义"""
    id: str = Field(..., description="原则ID")
    description: str = Field(..., description="原则描述")
    examples_good: List[str] = Field(default_factory=list, description="正面示例")
    examples_bad: List[str] = Field(default_factory=list, description="反面示例")
    weight: float = Field(default=1.0, description="权重")
    threshold: float = Field(default=0.6, description="通过阈值")

# 内置原则库
BUILTIN_PRINCIPLES = {
    "why-over-what": PrincipleDefinition(
        id="why-over-what",
        description="解释为什么做，而不只是列出做什么。强调业务价值、用户影响、问题解决。",
        examples_good=[
            "✅ '降低TPST 30%，减少API成本' - 清晰的业务价值",
            "✅ '解决用户频繁返工的痛点' - 明确的问题导向",
        ],
        examples_bad=[
            "❌ '实现缓存功能' - 只说做什么，没说为什么",
            "❌ '添加日志记录' - 缺乏业务价值说明",
        ],
        weight=1.5,  # 高权重
        threshold=0.6
    ),

    "tpst-oriented": PrincipleDefinition(
        id="tpst-oriented",
        description="量化TPST影响。必须包含具体的token数字、百分比降低、或性能指标。",
        examples_good=[
            "✅ 'TPST从1200降至750，减少37%'",
            "✅ '思考token占比从40%降至15%'",
        ],
        examples_bad=[
            "❌ '提升性能' - 没有量化指标",
            "❌ '优化体验' - 缺乏TPST数据",
        ],
        weight=1.5,  # 高权重
        threshold=0.6
    ),

    "actionable-over-abstract": PrincipleDefinition(
        id="actionable-over-abstract",
        description="具体可执行的描述，而不是抽象概念。包含清晰的验收标准。",
        examples_good=[
            "✅ 'safe_edit必须先dry_run，展示diff后才允许apply'",
            "✅ '位置建议准确率 ≥ 95%'",
        ],
        examples_bad=[
            "❌ '提供智能建议' - 太抽象",
            "❌ '确保高质量' - 没有验收标准",
        ],
        weight=1.0,
        threshold=0.5
    ),

    "evidence-based": PrincipleDefinition(
        id="evidence-based",
        description="基于证据的陈述。引用数据、测试结果、基准对比、学术论文。",
        examples_good=[
            "✅ '基准测试显示P95延迟降低50%（见docs/benchmarks/）'",
            "✅ '参考Graph-of-Thought论文（arXiv:2305.16582）'",
        ],
        examples_bad=[
            "❌ '应该会更快' - 没有证据",
            "❌ '大家都这么做' - 缺乏依据",
        ],
        weight=1.0,
        threshold=0.5
    ),
}
```

#### 小模型评分实现

```python
import anthropic
from openai import OpenAI

class PrincipleScorer:
    """原则评分器（使用小模型）"""
    def __init__(
        self,
        model: Literal["gpt-3.5-turbo", "claude-haiku"] = "claude-haiku",
        principles: dict[str, PrincipleDefinition] = BUILTIN_PRINCIPLES
    ):
        self.model = model
        self.principles = principles

        # 初始化客户端
        if model.startswith("gpt"):
            self.client = OpenAI()
        else:
            self.client = anthropic.Anthropic()

    def score(
        self,
        content: str,
        doc_type: str,
        principles_to_check: List[str]
    ) -> dict[str, float]:
        """评分文档内容（批量评分以节省调用）"""
        # 构建评分prompt
        prompt = self._build_scoring_prompt(content, doc_type, principles_to_check)

        # 调用小模型
        response = self._call_model(prompt)

        # 解析评分结果
        scores = self._parse_scores(response, principles_to_check)

        return scores

    def _build_scoring_prompt(
        self,
        content: str,
        doc_type: str,
        principles_to_check: List[str]
    ) -> str:
        """构建评分prompt（≤100 tokens目标）"""
        # 提取关键内容（前500字符）
        excerpt = content[:500] + ("..." if len(content) > 500 else "")

        # 构建原则说明
        principles_desc = "\n".join([
            f"- {p_id}: {self.principles[p_id].description}"
            for p_id in principles_to_check
        ])

        prompt = f"""评分任务：检查{doc_type}文档是否遵守以下原则。

文档摘要：
{excerpt}

评分原则：
{principles_desc}

请为每个原则打分（0.0-1.0），只返回JSON格式：
{{"principle_id": score, ...}}

评分标准：
- 1.0: 完全符合，有清晰证据
- 0.6-0.9: 基本符合，有部分证据
- 0.3-0.5: 部分符合，证据不足
- 0.0-0.2: 不符合或完全缺失

只返回JSON，无需解释。"""

        return prompt

    def _call_model(self, prompt: str) -> str:
        """调用小模型"""
        if self.model == "claude-haiku":
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,  # 只需要返回JSON评分
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        else:  # gpt-3.5-turbo
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content

    def _parse_scores(
        self,
        response: str,
        principles_to_check: List[str]
    ) -> dict[str, float]:
        """解析模型返回的评分"""
        import json

        try:
            scores = json.loads(response.strip())
            # 验证并规范化评分
            return {
                p_id: float(scores.get(p_id, 0))
                for p_id in principles_to_check
            }
        except (json.JSONDecodeError, ValueError):
            # 如果解析失败，返回默认低分
            return {p_id: 0.3 for p_id in principles_to_check}
```

#### 综合评分逻辑

```python
class ComprehensiveValidator:
    """综合验证器（规则+原则）"""
    def __init__(self, standards: ProjectStandards):
        self.location_validator = LocationValidator(standards)
        self.structure_validator = StructureValidator()
        self.principle_scorer = PrincipleScorer()
        self.standards = standards

    def validate(
        self,
        file_path: Path,
        content: str
    ) -> ValidationResult:
        """综合验证（规则优先，原则辅助）"""
        doc_type = self._detect_doc_type(file_path)

        violations = []
        principle_scores = {}

        # 1. 规则验证（必须通过）
        location_result = self.location_validator.validate(file_path)
        violations.extend(location_result.violations)

        structure_result = self.structure_validator.validate(
            content, doc_type, self.standards
        )
        violations.extend(structure_result.violations)

        # 如果规则验证失败，不进行原则评分（节省成本）
        if violations and all(v.severity == "error" for v in violations):
            return ValidationResult(
                ok=False,
                violations=violations,
                principle_scores={},
                overall_score=0.0,
                can_proceed=False
            )

        # 2. 原则评分（语义质量）
        if doc_type in self.standards.documents:
            doc_standard = self.standards.documents[doc_type]
            principles_to_check = [p.id for p in doc_standard.principles]

            if principles_to_check:
                principle_scores = self.principle_scorer.score(
                    content, doc_type, principles_to_check
                )

                # 检查是否低于阈值
                for p_id, score in principle_scores.items():
                    principle = next(
                        p for p in doc_standard.principles if p.id == p_id
                    )
                    if score < principle.threshold:
                        violations.append(Violation(
                            rule=f"principle:{p_id}",
                            severity="warning",  # 原则评分失败是警告，不是错误
                            message=f"原则'{principle.description}'评分偏低（{score:.2f} < {principle.threshold}）",
                            hint=f"正面示例: {principle.examples_good[0]}"
                        ))

        # 3. 计算总分
        overall_score = self._calculate_overall_score(
            violations, principle_scores
        )

        # 4. 判断是否可以继续
        can_proceed = (
            len([v for v in violations if v.severity == "error"]) == 0
            and overall_score >= self.standards.validation.principle_threshold
        )

        return ValidationResult(
            ok=can_proceed,
            violations=violations,
            principle_scores=principle_scores,
            overall_score=overall_score,
            can_proceed=can_proceed
        )

    def _calculate_overall_score(
        self,
        violations: List[Violation],
        principle_scores: dict[str, float]
    ) -> float:
        """计算总分"""
        # 规则错误扣分
        error_penalty = len([v for v in violations if v.severity == "error"]) * 0.3
        warning_penalty = len([v for v in violations if v.severity == "warning"]) * 0.1

        # 原则评分加权平均
        if principle_scores:
            principle_avg = sum(principle_scores.values()) / len(principle_scores)
        else:
            principle_avg = 0.5  # 没有原则评分时默认中等

        # 综合评分
        score = max(0, principle_avg - error_penalty - warning_penalty)
        return round(score, 2)
```

---

### Token成本优化

**评分成本分析**:
```python
# 单次评分token消耗
prompt_tokens = 150  # 包含文档摘要+原则说明
completion_tokens = 50  # JSON评分结果

total_per_validation = 200 tokens

# 每日成本估算（假设10次文档创建）
daily_validations = 10
daily_tokens = 10 * 200 = 2000 tokens

# 小模型成本（Claude Haiku）
cost_per_1M_tokens = $0.25
daily_cost = 2000 / 1_000_000 * 0.25 = $0.0005

# 月成本
monthly_cost = 0.0005 * 30 = $0.015
```

**对比大模型**:
- 如果使用Claude Sonnet评分：月成本 ~$0.45（30x差距）
- 小模型足够准确（评分任务简单），无需大模型

---

### 可配置性

#### 项目级原则定义

```yaml
# .project_standards.yml
documents:
  epic:
    location: "docs/product/epics/epic-{num}-{kebab}/"
    naming: "epic-{num}-{kebab}.md"
    required_sections:
      - "业务价值"
      - "成功指标"
      - "Features(3-5)"

    # 自定义原则
    principles:
      - id: "why-over-what"
        desc: "解释为什么，而不只是列出做什么"
        checker:
          type: "llm_scorer"  # 使用小模型评分
          model: "claude-haiku"  # 可选：gpt-3.5-turbo
          threshold: 0.6
          weight: 1.5
        examples_good:
          - "✅ '降低TPST 30%，减少API成本'"
        examples_bad:
          - "❌ '实现缓存功能'"

      - id: "tpst-oriented"
        desc: "量化TPST影响"
        checker:
          type: "regex_presence"  # 简单的regex检查
          patterns: ["TPST", "tokens", "token浪费", "\\d+%"]
        # regex检查更快更便宜，适合确定性检查

validation:
  strict_mode: true  # 开发阶段可设为false（宽松模式）
  principle_threshold: 0.6  # 原则评分总分阈值
  enable_llm_scoring: true  # 是否启用小模型评分（可关闭以节省成本）
```

---

### 最佳实践建议

1. **规则优先**: 能用regex/pattern检查的，不用小模型
2. **批量评分**: 一次调用评估多个原则，节省API调用
3. **缓存结果**: 同一文档短期内不重复评分
4. **宽松模式**: 开发阶段降低阈值，避免过度打断
5. **豁免机制**: 特殊情况允许豁免，记录审计日志

---

## 🔗 依赖关系

### 依赖的Epic
- **Epic-001: 行为约束系统** - 共享"行为工程"底盘和ExecutionPlan验证模式

### 与Epic-001的关系

| 维度 | Epic-001 | Epic-002 |
|------|----------|----------|
| **约束对象** | 代码操作（search, edit, exec） | 文档操作（create, structure） |
| **约束方式** | ExecutionPlan + dry_run | DocPlan + validate |
| **物理删除路径** | 禁止直接执行，必须先预览 | 禁止直接创建，必须先验证 |
| **验证机制** | pre_conditions + rollback | location + structure + principles |
| **TPST影响** | 减少盲目重试 | 减少文档返工 |

**共享基础设施**：
- Pydantic validation模式
- MCP service架构
- dry_run → validate → execute流程
- 审计日志系统

### 被依赖的Feature
- Epic-003: 可能需要扩展到代码规范约束
- 企业级行为治理中心（长期规划）

---

## 📊 时间线

### 预计时间
- **开始日期**: 2025-11-04（Epic-001完成后）
- **结束日期**: 2025-11-15
- **总工作量**: 10人天 (2周 MVP)

### 里程碑

#### Week 1: 核心服务实现
- [ ] Feature-004 完成：MCP端点和标准系统 - 2025-11-08
  - [ ] Story-004: standards.get() + Resolver
  - [ ] Story-005: doc.suggest_location()
  - [ ] Story-006: doc.template() 原则驱动生成
  - [ ] Story-007: doc.validate() 核心验证

#### Week 2: Git集成和验证优化
- [ ] Feature-005 完成：Git守卫集成 - 2025-11-12
  - [ ] Story-008: pre-commit钩子
  - [ ] Story-009: 一键修复建议
- [ ] Feature-006 完成：原则评分系统 - 2025-11-15
  - [ ] Story-010: 规则引擎
  - [ ] Story-011: 原则评分（小模型）
  - [ ] Story-012: 豁免机制

### 演示场景
**英雄场景**：AI助手尝试创建文档
1. AI: "我要创建一个Epic关于工具智能"
2. 调用 `doc.suggest_location()` → 返回建议路径和原则
3. AI: 按照原则创建文档
4. 调用 `doc.validate()` → 检测缺少"TPST指标"章节
5. AI: 补充缺失章节
6. 调用 `doc.validate()` → ✅ 通过
7. Git提交 → pre-commit钩子自动验证 → ✅ 允许提交

**对比TPST**：
- 无约束：1200 tokens（3次返工）
- 有约束：750 tokens（首次成功）
- **降低37.5%**

---

## 🛡️ 风险与对策

### 技术风险

| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| 规则过于僵化 | High | Medium | 提供waiver机制，记录审计痕迹 | Team |
| 多项目差异大 | Medium | High | 标准继承+局部覆盖，Resolver合并 | Team |
| 原则评分不准 | Medium | Medium | 优先用规则引擎，小模型仅辅助 | Team |
| 性能开销 | Low | Low | 缓存标准解析，异步验证 | Team |

### 进度风险

| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| 与Epic-001时间重叠 | Medium | Low | Epic-001优先，002并行准备 | Team |
| 标准定义难以收敛 | High | Medium | 先实现3种文档类型（epic/adr/story） | Team |

### 用户体验风险

| 风险 | 影响 | 概率 | 对策 | 负责人 |
|------|------|------|------|--------|
| 上手成本高 | Medium | Medium | 提供init向导，内置3-5套模板 | Team |
| 误报率高 | High | Medium | 初期宽松模式，逐步收紧 | Team |

---

## 🔄 长期演进路线

### Phase 1: 文档规范约束（MVP - 2周）
✅ 当前Epic范围
- 位置、命名、结构、必填章节验证
- Pre-commit守卫
- 原则驱动的指导

### Phase 2: 代码行为规范（Month 2）
📋 扩展到代码提交规范
- **Conventional Commits** 校验与建议
- **PR模板/检查清单** 自动化
  - 必须包含：验证结果、TPST影响评估
- **ADR流程守卫**
  - 命名、索引、交叉引用自动化
- **Commit message质量评分**

### Phase 3: CI/CD行为治理（Month 3）
🚀 企业级治理
- **CI/CD Gates**：不合规直接fail
- **审计报告**：
  - 规范遵守度趋势
  - TPST影响分析
  - 返工率热力图
- **组织级标准注册表**
  - 中心化管理
  - 仓库继承策略
  - 差异可视化

### Phase 4: 通用行为工程平台（长期）
🌟 产品化
- 支持任意规范类型（API设计、测试覆盖率）
- 插件系统（自定义验证器）
- SaaS化部署（企业多租户）
- 开源社区版本

---

## 🧪 测试策略

### 测试范围
- MCP端点的请求/响应正确性
- 标准解析和合并逻辑
- 验证引擎的规则覆盖
- Pre-commit钩子集成
- 原则评分准确性

### 测试类型
- [x] 单元测试 - 每个MCP端点独立测试
- [x] 集成测试 - 完整的建议→验证→守卫流程
- [x] TPST基准测试 - 对比有/无约束的token消耗
- [ ] 用户体验测试 - 实际文档创建场景

### 测试覆盖率目标
- 核心模块: 95%
- 整体: 90%

---

## 📝 实现备注

### 设计决策

1. **为什么独立MCP服务而不是集成到Serena？**
   - 更通用：适用于任何项目，不限于Serena用户
   - 可组合：可与其他MCP服务配合使用
   - 独立部署：企业可单独部署标准服务

2. **为什么原则驱动而不是固定模板？**
   - 灵活性：不同项目类型有不同需求
   - 可理解性：AI理解"为什么"而不只是"填空"
   - 可扩展性：添加新原则无需改模板

3. **为什么使用小模型做原则评分？**
   - Token效率：评分≤100 tokens，不让大模型长篇判读
   - 速度：快速反馈，不阻塞创建流程
   - 成本：小模型成本低，可频繁调用

4. **为什么提供waiver机制？**
   - 避免过度僵化：特殊情况需要豁免
   - 审计透明：记录豁免原因和决策者
   - 平衡控制与灵活性

---

## 📚 相关文档

### 内部文档
- [Epic 001: 行为约束系统](../epic-001-behavior-constraints/README.md)
- [产品定义 v1.0](../../definition/product-definition-v1.md)
- [TPST指标体系](../../../development/architecture/behavior-engineering.md)

### 外部参考
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [ADR (Architecture Decision Records)](https://adr.github.io/)

---

## 🎯 下一步行动

### 立即行动（本周）
1. ✅ 创建Epic-002文档（当前文档）
2. 📋 创建技术架构设计文档
3. 📋 创建Feature-004详细规格
4. 📋 制定并行开发计划

### 短期行动（2周内）
1. 实现核心MCP端点（Feature-004）
2. 建立基准测试（TPST对比）
3. 完成MVP演示场景

### 问题待澄清
1. 是否与Epic-001并行开发？还是顺序开发？
2. 初始标准文件应该包含哪些文档类型？
3. 原则评分使用哪个小模型？（GPT-3.5-turbo? Claude Haiku?）

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
