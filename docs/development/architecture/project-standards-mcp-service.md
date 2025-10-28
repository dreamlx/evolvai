# Project Standards MCP Service - Technical Architecture

**文档类型**: Technical Architecture
**关联Epic**: [Epic-002: 项目规范即服务](../../product/epics/epic-002-project-standards/README.md)
**创建日期**: 2025-10-27
**状态**: [DRAFT]

---

## 📋 架构概览

### 系统定位

**Project Standards MCP Service** 是一个独立的MCP服务，提供项目规范的"可执行约束"能力。

**核心特性**：
- 🚫 **物理删除错误路径**：AI无法创建不合规文档
- 📐 **原则驱动指导**：智能建议而非死板模板
- 🔄 **标准继承与合并**：组织级+项目级灵活组合
- 🎯 **Token效率优化**：减少文档返工，降低TPST

### 架构分层

```
┌───────────────────────────────────────────────────────┐
│                  AI Clients Layer                     │
│  (Claude Code, Cursor, Copilot, Custom Agents)       │
└──────────────────┬────────────────────────────────────┘
                   │ MCP Protocol
┌──────────────────▼────────────────────────────────────┐
│              MCP Server Interface                     │
│  ┌─────────────────────────────────────────────────┐ │
│  │  standards.get()        doc.suggest_location()  │ │
│  │  doc.template()         doc.validate()          │ │
│  │  git.guard.precommit()  doc.waive()             │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────┬────────────────────────────────────┘
                   │
┌──────────────────▼────────────────────────────────────┐
│              Business Logic Layer                     │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │   Standards  │  │  Validation  │  │    Git     │ │
│  │   Resolver   │  │    Engine    │  │  Guardian  │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
└──────────────────┬────────────────────────────────────┘
                   │
┌──────────────────▼────────────────────────────────────┐
│              Data & Config Layer                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Organization │  │   Project    │  │   Cache    │ │
│  │  Standards   │  │  Standards   │  │   Store    │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
└───────────────────────────────────────────────────────┘
```

---

## 🔧 核心组件设计

### 1. Standards Resolver

**职责**：解析、合并、验证标准定义

**核心功能**：
```python
class StandardsResolver:
    """标准解析器"""

    def resolve(self, project_path: Path) -> ResolvedStandards:
        """解析并合并标准

        优先级（低→高）：
        1. Built-in defaults
        2. Organization standards (via URL)
        3. Repository .project_standards.yml
        4. Environment overrides (dev/prod)
        """

    def merge_standards(
        self,
        base: Standards,
        override: Standards
    ) -> ResolvedStandards:
        """合并标准，处理冲突"""

    def validate_schema(self, standards: dict) -> ValidationResult:
        """验证标准文件格式"""
```

**标准文件Schema**：
```python
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Literal

class PrincipleChecker(BaseModel):
    """原则检查器定义"""
    type: Literal["regex_presence", "regex_absence", "llm_score"]
    patterns: Optional[List[str]] = None
    model: Optional[str] = None  # For llm_score
    threshold: Optional[float] = None

class Principle(BaseModel):
    """原则定义"""
    id: str = Field(..., description="原则唯一标识")
    desc: str = Field(..., description="原则描述")
    checker: PrincipleChecker
    examples: Optional[Dict[str, str]] = None  # {"good": "✅ 示例", "bad": "❌ 反例"}

class DocumentStandard(BaseModel):
    """文档类型标准"""
    location: str = Field(..., description="位置模式，支持变量 {num}, {kebab}")
    naming: str = Field(..., description="命名模式")
    required_sections: List[str] = Field(default_factory=list)
    optional_sections: Optional[List[str]] = None
    principles: List[Principle] = Field(default_factory=list)

class GuardConfig(BaseModel):
    """守卫配置"""
    root_allowlist: List[str] = Field(
        default_factory=lambda: ["README.md", "CLAUDE.md", "LICENSE"]
    )
    doc_dirs: List[str] = Field(default_factory=lambda: ["docs/"])
    max_new_docs_per_pr: int = 10
    strict_mode: bool = True

class ValidationConfig(BaseModel):
    """验证配置"""
    principle_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    strict_mode: bool = True
    waiver_required_roles: Optional[List[str]] = None

class ProjectStandards(BaseModel):
    """项目标准定义"""
    version: str = "1.0"
    extends: Optional[List[HttpUrl | str]] = None
    documents: Dict[str, DocumentStandard]
    guards: GuardConfig = Field(default_factory=GuardConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
```

**标准继承与合并逻辑**：
```python
def merge_standards(base: ProjectStandards, override: ProjectStandards) -> ProjectStandards:
    """
    合并标准，override优先级高于base

    合并规则：
    - documents: 按doc_type合并，override完全替换base
    - guards: 字段级合并，列表追加
    - validation: override字段替换base字段
    - principles: 按principle.id合并，override替换base
    """
    merged_documents = {**base.documents}
    for doc_type, doc_std in override.documents.items():
        if doc_type in merged_documents:
            # 原则按ID合并
            base_principles = {p.id: p for p in merged_documents[doc_type].principles}
            override_principles = {p.id: p for p in doc_std.principles}
            merged_principles = {**base_principles, **override_principles}

            # 创建新的DocumentStandard
            merged_documents[doc_type] = doc_std.model_copy(update={
                "principles": list(merged_principles.values())
            })
        else:
            merged_documents[doc_type] = doc_std

    return ProjectStandards(
        version=override.version,
        documents=merged_documents,
        guards=merge_guards(base.guards, override.guards),
        validation=override.validation or base.validation
    )
```

---

### 2. Validation Engine

**职责**：执行规则检查和原则评分

**核心功能**：
```python
class ValidationEngine:
    """验证引擎"""

    def __init__(self, standards: ResolvedStandards):
        self.standards = standards
        self.rule_checkers = self._init_rule_checkers()
        self.principle_scorer = PrincipleScorer()

    def validate(
        self,
        doc_type: str,
        path: Path,
        content_meta: DocumentMeta
    ) -> ValidationResult:
        """
        完整验证文档

        验证顺序：
        1. 位置验证（location pattern）
        2. 命名验证（naming pattern）
        3. 结构验证（required sections）
        4. 原则评分（principles）
        """
        violations = []

        # 1. 位置验证
        expected_location = self._expand_pattern(
            self.standards.documents[doc_type].location,
            context={"num": extract_number(path), ...}
        )
        if not path.match(expected_location):
            violations.append(Violation(
                rule="wrong_location",
                severity="error",
                message=f"文档位置不正确",
                suggested_fix=expected_location
            ))

        # 2. 命名验证
        expected_name = self._expand_pattern(
            self.standards.documents[doc_type].naming,
            context={...}
        )
        if path.name != expected_name:
            violations.append(Violation(
                rule="wrong_naming",
                severity="error",
                message=f"文档命名不符合规范",
                suggested_fix=expected_name
            ))

        # 3. 结构验证
        required_sections = self.standards.documents[doc_type].required_sections
        missing_sections = set(required_sections) - set(content_meta.sections)
        for section in missing_sections:
            violations.append(Violation(
                rule=f"missing_section:{section}",
                severity="error",
                message=f"缺少必填章节：{section}",
                hint=self._get_section_hint(doc_type, section)
            ))

        # 4. 原则评分
        principle_scores = {}
        for principle in self.standards.documents[doc_type].principles:
            score = self._check_principle(principle, content_meta)
            principle_scores[principle.id] = score

            if score < self.standards.validation.principle_threshold:
                violations.append(Violation(
                    rule=f"principle:{principle.id}",
                    severity="warning",
                    message=f"原则'{principle.desc}'得分过低: {score:.2f}",
                    hint=self._get_principle_hint(principle)
                ))

        overall_score = sum(principle_scores.values()) / len(principle_scores) if principle_scores else 1.0

        return ValidationResult(
            ok=len([v for v in violations if v.severity == "error"]) == 0,
            violations=violations,
            principle_scores=principle_scores,
            overall_score=overall_score,
            can_proceed=overall_score >= self.standards.validation.principle_threshold
        )
```

**原则检查器实现**：
```python
class PrincipleScorer:
    """原则评分器"""

    def score_regex_presence(
        self,
        patterns: List[str],
        content: str
    ) -> float:
        """基于正则匹配的评分"""
        matches = sum(1 for p in patterns if re.search(p, content, re.IGNORECASE))
        return min(matches / len(patterns), 1.0)

    def score_with_llm(
        self,
        principle: Principle,
        content_meta: DocumentMeta
    ) -> float:
        """使用小模型评分（≤100 tokens）"""
        prompt = f"""
        评估文档是否符合原则：{principle.desc}

        文档元信息：
        - 标题: {content_meta.title}
        - 章节: {", ".join(content_meta.sections)}
        - 关键词: {", ".join(content_meta.keywords)}

        评分标准：
        - 1.0: 完全符合原则
        - 0.6-0.9: 基本符合，可改进
        - 0.0-0.5: 不符合原则

        只返回数字评分（0.0-1.0）
        """

        # 调用小模型（GPT-3.5-turbo或Claude Haiku）
        response = self.llm_client.complete(
            prompt=prompt,
            model=principle.checker.model or "gpt-3.5-turbo",
            max_tokens=10,
            temperature=0.0
        )

        try:
            score = float(response.strip())
            return max(0.0, min(1.0, score))
        except ValueError:
            logger.warning(f"Invalid LLM score response: {response}")
            return 0.0
```

---

### 3. Location Suggester

**职责**：智能推荐文档位置和结构

**核心功能**：
```python
class LocationSuggester:
    """位置建议器"""

    def suggest(
        self,
        doc_type: str,
        title: str,
        project_context: ProjectContext
    ) -> LocationSuggestion:
        """
        基于上下文推荐位置

        考虑因素：
        - 文档类型（epic, feature, story, adr）
        - 项目类型（technical_product, open_source, enterprise）
        - 团队规模（影响文档粒度）
        - 开发阶段（mvp, growth, mature）
        """
        doc_standard = self.standards.documents[doc_type]

        # 生成路径
        context_vars = self._generate_context_vars(title, project_context)
        suggested_path = self._expand_pattern(
            doc_standard.location,
            context_vars
        )

        # 生成指导原则
        guiding_principles = self._adapt_principles(
            doc_standard.principles,
            project_context
        )

        # 生成outline
        outline = self._generate_outline(
            doc_type,
            doc_standard.required_sections,
            doc_standard.optional_sections,
            project_context
        )

        return LocationSuggestion(
            suggested_path=suggested_path,
            naming_pattern=doc_standard.naming,
            required_sections=doc_standard.required_sections,
            guiding_principles=guiding_principles,
            outline=outline,
            examples=self._get_examples(doc_type)
        )

    def _adapt_principles(
        self,
        principles: List[Principle],
        context: ProjectContext
    ) -> List[AdaptedPrinciple]:
        """根据项目上下文调整原则"""
        adapted = []
        for principle in principles:
            # 根据项目类型调整示例
            if context.project_type == "technical_product":
                examples = {
                    "good": f"✅ {principle.id}: 量化TPST影响",
                    "bad": f"❌ {principle.id}: 只描述功能不说影响"
                }
            elif context.project_type == "open_source":
                examples = {
                    "good": f"✅ {principle.id}: 说明社区价值",
                    "bad": f"❌ {principle.id}: 只关注技术实现"
                }

            adapted.append(AdaptedPrinciple(
                id=principle.id,
                desc=principle.desc,
                examples=examples,
                importance=self._calculate_importance(principle, context)
            ))

        return adapted
```

---

### 4. Git Guardian

**职责**：Pre-commit钩子和Git工作流守卫

**核心功能**：
```python
class GitGuardian:
    """Git守卫"""

    def precommit_check(
        self,
        staged_files: List[Path]
    ) -> PrecommitResult:
        """
        Pre-commit钩子检查

        检查项：
        1. 文档文件是否在允许的目录
        2. 根目录文件是否在白名单
        3. 单次PR新增文档数量限制
        4. 每个文档是否通过validate()
        """
        allowed_files = []
        blocked_files = []

        for file in staged_files:
            # 跳过非文档文件
            if not self._is_doc_file(file):
                allowed_files.append(str(file))
                continue

            # 检查根目录白名单
            if file.parent == Path("."):
                if file.name not in self.standards.guards.root_allowlist:
                    blocked_files.append(BlockedFile(
                        path=str(file),
                        reason="根目录只允许特定文件",
                        fix=self._suggest_doc_location(file)
                    ))
                    continue

            # 检查文档目录限制
            if not any(str(file).startswith(d) for d in self.standards.guards.doc_dirs):
                blocked_files.append(BlockedFile(
                    path=str(file),
                    reason="文档必须在docs/目录下",
                    fix=self._suggest_doc_location(file)
                ))
                continue

            # 检查文档内容（如果可用）
            doc_type = self._infer_doc_type(file)
            if doc_type and doc_type in self.standards.documents:
                content_meta = self._extract_content_meta(file)
                validation_result = self.validator.validate(doc_type, file, content_meta)

                if not validation_result.ok:
                    blocked_files.append(BlockedFile(
                        path=str(file),
                        reason="文档不符合规范",
                        violations=validation_result.violations,
                        fix="修复上述违规项"
                    ))
                    continue

            allowed_files.append(str(file))

        # 检查新增文档数量限制
        new_docs_count = len([f for f in staged_files if self._is_new_doc(f)])
        if new_docs_count > self.standards.guards.max_new_docs_per_pr:
            return PrecommitResult(
                ok=False,
                action="abort_commit",
                message=f"单次提交新增文档过多({new_docs_count} > {self.standards.guards.max_new_docs_per_pr})",
                blocked_files=blocked_files,
                allowed_files=allowed_files
            )

        if blocked_files:
            return PrecommitResult(
                ok=False,
                action="abort_commit",
                message=f"{len(blocked_files)}个文件违反规范，请修复后重新提交",
                blocked_files=blocked_files,
                allowed_files=allowed_files
            )

        return PrecommitResult(
            ok=True,
            action="allow_commit",
            message="所有文件符合规范",
            blocked_files=[],
            allowed_files=allowed_files
        )
```

**Pre-commit钩子安装**：
```bash
# .git/hooks/pre-commit
#!/bin/bash
set -e

# 获取staged文件列表
STAGED_FILES=$(git diff --cached --name-only)

# 调用MCP服务
RESULT=$(echo "$STAGED_FILES" | project-standards-guard precommit)

# 解析结果
if ! echo "$RESULT" | jq -e '.ok' > /dev/null; then
    echo "❌ Pre-commit检查失败:"
    echo "$RESULT" | jq -r '.message'
    echo ""
    echo "阻止的文件:"
    echo "$RESULT" | jq -r '.blocked_files[] | "  - \(.path): \(.reason)"'
    echo ""
    echo "修复建议:"
    echo "$RESULT" | jq -r '.blocked_files[] | "  - \(.fix)"'
    exit 1
fi

echo "✅ Pre-commit检查通过"
exit 0
```

---

### 5. Waiver Manager

**职责**：管理规范豁免请求

**核心功能**：
```python
class WaiverManager:
    """豁免管理器"""

    def request_waiver(
        self,
        doc_path: Path,
        policy_id: str,
        reason: str,
        requester: str
    ) -> WaiverRequest:
        """
        请求豁免

        记录内容：
        - 文档路径
        - 豁免的策略ID
        - 豁免原因
        - 请求者
        - 时间戳
        """
        waiver = WaiverRequest(
            id=generate_waiver_id(),
            doc_path=str(doc_path),
            policy_id=policy_id,
            reason=reason,
            requester=requester,
            requested_at=datetime.utcnow(),
            status="pending"
        )

        # 保存到审计日志
        self.audit_logger.log_waiver_request(waiver)

        # 如果strict_mode=False，自动批准
        if not self.standards.validation.strict_mode:
            waiver.status = "auto_approved"
            waiver.approved_at = datetime.utcnow()

        return waiver

    def is_waived(self, doc_path: Path, policy_id: str) -> bool:
        """检查是否已豁免"""
        waivers = self.audit_logger.get_waivers(doc_path)
        return any(
            w.policy_id == policy_id and w.status in ["approved", "auto_approved"]
            for w in waivers
        )
```

---

## 🌐 MCP服务接口

### API端点定义

#### 1. standards.get
**用途**：获取解析后的项目标准

```python
@mcp_tool
def standards_get(
    project_path: str,
    include_inherited: bool = True
) -> dict:
    """
    获取项目标准

    Args:
        project_path: 项目根目录路径
        include_inherited: 是否包含继承的标准

    Returns:
        {
            "version": "1.0",
            "source": "merged",
            "documents": {...},
            "guards": {...},
            "validation": {...},
            "inherited_from": ["org-defaults", "repo-local"]
        }
    """
    resolver = StandardsResolver()
    standards = resolver.resolve(Path(project_path))

    return standards.model_dump(
        include_inherited=include_inherited
    )
```

#### 2. doc.suggest_location
**用途**：智能推荐文档位置和结构

```python
@mcp_tool
def doc_suggest_location(
    doc_type: Literal["epic", "feature", "story", "task", "adr", "sprint"],
    title: str,
    project_context: dict
) -> dict:
    """
    推荐文档位置

    Args:
        doc_type: 文档类型
        title: 文档标题
        project_context: 项目上下文
            - project_type: "technical_product" | "open_source" | "enterprise"
            - team_size: "small" | "medium" | "large"
            - development_stage: "mvp" | "growth" | "mature"

    Returns:
        {
            "suggested_path": "docs/product/epics/epic-002-...",
            "naming_pattern": "epic-{num}-{kebab}",
            "required_sections": [...],
            "guiding_principles": [...],
            "outline": [...]
        }
    """
    suggester = LocationSuggester(standards)
    context = ProjectContext(**project_context)

    return suggester.suggest(
        doc_type=doc_type,
        title=title,
        project_context=context
    ).model_dump()
```

#### 3. doc.validate
**用途**：验证文档是否符合规范

```python
@mcp_tool
def doc_validate(
    path: str,
    content_meta: dict
) -> dict:
    """
    验证文档

    Args:
        path: 文档路径
        content_meta: 文档元信息
            - title: str
            - sections: List[str]
            - keywords: List[str]
            - word_count: int

    Returns:
        {
            "ok": false,
            "violations": [
                {
                    "rule": "wrong_location",
                    "severity": "error",
                    "message": "...",
                    "suggested_fix": "..."
                }
            ],
            "principle_scores": {
                "why-over-what": 0.7,
                "tpst-oriented": 0.4
            },
            "overall_score": 0.55,
            "can_proceed": false
        }
    """
    validator = ValidationEngine(standards)
    doc_type = infer_doc_type(Path(path))
    meta = DocumentMeta(**content_meta)

    return validator.validate(
        doc_type=doc_type,
        path=Path(path),
        content_meta=meta
    ).model_dump()
```

#### 4. git.guard.precommit
**用途**：Pre-commit钩子检查

```python
@mcp_tool
def git_guard_precommit(
    staged_files: List[str]
) -> dict:
    """
    Pre-commit守卫

    Args:
        staged_files: Git staged文件列表

    Returns:
        {
            "ok": false,
            "action": "abort_commit",
            "message": "1个文件违反规范",
            "blocked_files": [
                {
                    "path": "docs/temp.md",
                    "reason": "违反命名规范",
                    "fix": "重命名为 docs/knowledge/..."
                }
            ],
            "allowed_files": [...]
        }
    """
    guardian = GitGuardian(standards)

    return guardian.precommit_check(
        staged_files=[Path(f) for f in staged_files]
    ).model_dump()
```

---

## 📊 性能优化

### 缓存策略

```python
class StandardsCache:
    """标准缓存"""

    def __init__(self):
        self.cache = {}
        self.ttl = 3600  # 1小时

    @lru_cache(maxsize=128)
    def get_resolved_standards(self, project_path: str) -> ResolvedStandards:
        """缓存解析后的标准"""
        cache_key = self._generate_cache_key(project_path)

        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            if time.time() - cached_item.timestamp < self.ttl:
                return cached_item.standards

        # 解析标准
        resolver = StandardsResolver()
        standards = resolver.resolve(Path(project_path))

        # 更新缓存
        self.cache[cache_key] = CacheItem(
            standards=standards,
            timestamp=time.time()
        )

        return standards
```

### 异步验证

```python
class AsyncValidator:
    """异步验证器"""

    async def validate_async(
        self,
        doc_type: str,
        path: Path,
        content_meta: DocumentMeta
    ) -> ValidationResult:
        """异步验证，不阻塞主流程"""

        # 快速验证（同步）
        quick_checks = self._quick_validate(doc_type, path, content_meta)
        if not quick_checks.ok:
            return quick_checks

        # 原则评分（异步）
        principle_scores = await self._score_principles_async(
            doc_type, content_meta
        )

        return ValidationResult(
            ok=True,
            violations=[],
            principle_scores=principle_scores,
            overall_score=sum(principle_scores.values()) / len(principle_scores)
        )
```

---

## 🧪 测试策略

### 单元测试

```python
# test_standards_resolver.py
def test_resolve_with_inheritance():
    """测试标准继承和合并"""
    # Given: 组织级+项目级标准
    org_standards = load_standards("org_defaults.yml")
    project_standards = load_standards(".project_standards.yml")

    # When: 解析合并
    resolver = StandardsResolver()
    resolved = resolver.merge_standards(org_standards, project_standards)

    # Then: 项目级覆盖组织级
    assert resolved.documents["epic"].location == project_standards.documents["epic"].location
    assert "org-principle" in [p.id for p in resolved.documents["epic"].principles]
    assert "project-principle" in [p.id for p in resolved.documents["epic"].principles]

# test_validation_engine.py
def test_validate_missing_section():
    """测试缺失必填章节检测"""
    # Given: Epic缺少"业务价值"章节
    content_meta = DocumentMeta(
        title="Test Epic",
        sections=["概述", "Features"],
        keywords=[]
    )

    # When: 验证
    validator = ValidationEngine(standards)
    result = validator.validate("epic", Path("docs/product/epics/epic-001/"), content_meta)

    # Then: 应该报错
    assert not result.ok
    assert any("missing_section:业务价值" in v.rule for v in result.violations)
```

### 集成测试

```python
# test_mcp_integration.py
def test_full_workflow():
    """测试完整的建议→验证→守卫流程"""
    # 1. 建议位置
    suggestion = doc_suggest_location(
        doc_type="epic",
        title="Tool Intelligence",
        project_context={
            "project_type": "technical_product",
            "team_size": "small"
        }
    )

    assert "docs/product/epics/" in suggestion["suggested_path"]

    # 2. 创建文档（模拟）
    doc_path = suggestion["suggested_path"] + "README.md"

    # 3. 验证文档
    validation = doc_validate(
        path=doc_path,
        content_meta={
            "title": "Tool Intelligence",
            "sections": ["业务价值", "成功指标", "Features"],
            "keywords": ["TPST", "tokens"],
            "word_count": 500
        }
    )

    assert validation["ok"]
    assert validation["principle_scores"]["tpst-oriented"] >= 0.6

    # 4. Pre-commit守卫
    guard_result = git_guard_precommit(staged_files=[doc_path])

    assert guard_result["ok"]
    assert doc_path in guard_result["allowed_files"]
```

### TPST基准测试

```python
# test_tpst_benchmark.py
def test_tpst_comparison():
    """对比有/无约束的TPST"""
    # Baseline: 无约束创建文档
    baseline_tokens = simulate_doc_creation_without_standards(
        task="创建Epic关于工具智能"
    )
    # 预期: ~1200 tokens（多次返工）

    # Optimized: 有约束创建文档
    optimized_tokens = simulate_doc_creation_with_standards(
        task="创建Epic关于工具智能"
    )
    # 预期: ~750 tokens（首次成功）

    reduction_percentage = (baseline_tokens - optimized_tokens) / baseline_tokens

    assert reduction_percentage >= 0.30, f"TPST降低不足30%: {reduction_percentage:.1%}"

    print(f"✅ TPST降低: {reduction_percentage:.1%}")
    print(f"   Baseline: {baseline_tokens} tokens")
    print(f"   Optimized: {optimized_tokens} tokens")
```

---

## 🚀 部署方案

### 独立MCP服务部署

```bash
# 1. 安装
pip install project-standards-mcp

# 2. 配置
cat > ~/.config/project-standards/config.yml <<EOF
service:
  host: localhost
  port: 8080

cache:
  enabled: true
  ttl_seconds: 3600

logging:
  level: INFO
  file: ~/.config/project-standards/logs/service.log
EOF

# 3. 启动服务
project-standards-mcp serve

# 4. 配置Claude Code使用此MCP
cat >> ~/.config/claude-code/mcp_servers.json <<EOF
{
  "project-standards": {
    "url": "http://localhost:8080",
    "enabled": true
  }
}
EOF
```

### 项目初始化

```bash
# 项目中初始化标准
cd /path/to/project
project-standards init

# 选择模板
? 选择项目类型:
  ❯ Technical Product
    Open Source
    Enterprise Application
    Research Project

? 团队规模:
  ❯ Small (1-5人)
    Medium (6-20人)
    Large (>20人)

# 生成 .project_standards.yml
✅ 已生成 .project_standards.yml
✅ 已安装 pre-commit 钩子
✅ 已添加到 .gitignore
```

---

## 📚 参考资料

### 相关文档
- [Epic-002: 项目规范即服务](../../product/epics/epic-002-project-standards/README.md)
- [Epic-001: 行为约束系统](../../product/epics/epic-001-behavior-constraints/README.md)
- [ExecutionPlan Schema](../../product/epics/epic-001-behavior-constraints/story-001-execution-plan-schema.md)

### 外部资源
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Git Hooks Documentation](https://git-scm.com/docs/githooks)

---

**最后更新**: 2025-10-27
**更新人**: EvolvAI Team
