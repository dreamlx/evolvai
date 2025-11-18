# Memory Bank MCP 与 AI 工具触发机制对齐分析

**Status**: [ANALYSIS]
**Last Updated**: 2025-11-18
**Purpose**: 分析 custom-instructions.md 原始设计与我们当前实现的差异

---

## 🎯 关键发现：我们偏离了原始设计

### Memory Bank MCP 原始设计

根据 [Memory Bank MCP GitHub](https://github.com/alioshr/memory-bank-mcp) README：

```markdown
## Custom AI instructions

This section contains the instructions that should be pasted on the AI custom instructions,
either for Cline, Claude or Cursor, or any other MCP client. You should copy and paste these rules.
For reference, see [custom-instructions.md](custom-instructions.md) which contains these rules.
```

**原始意图**：
1. `custom-instructions.md` 是给 **AI 工具本身** 的指令
2. 应该粘贴到 Cline/Claude/Cursor 的 **Custom Instructions** 设置中
3. AI 工具会 **自动** 根据这些指令触发 Memory Bank 操作

---

## 🔄 当前实现 vs 原始设计

### 我们当前的实现（偏离）

```yaml
当前做法:
  - 手动在 CLAUDE.md 中定义触发规则
  - 使用自定义 slash commands (/memory-bank-load)
  - AI 需要"记住"执行这些命令

问题:
  - 依赖 AI 记忆和主动执行
  - 不是真正的"自动"触发
  - 偏离了 Memory Bank 的设计理念
```

### Memory Bank 原始设计（正确）

```yaml
正确做法:
  1. Memory Bank 生成 custom-instructions.md
  2. 用户复制内容到 AI 工具的 Custom Instructions
  3. AI 工具自动遵循这些指令
  4. 真正的自动触发，无需 AI "记住"

工具配置位置:
  - Cline: Extension settings → Custom Instructions
  - Claude Desktop: Settings → Custom Instructions
  - Cursor: Settings → AI → Rules for AI
  - Claude.ai: Project Knowledge or Custom Instructions
```

---

## 📋 正确的集成流程

### Step 1: Memory Bank 生成 custom-instructions.md

Memory Bank MCP 应该为 `serena` 项目生成类似这样的文件：

```markdown
# Custom Instructions for serena Project

## Automatic Behaviors

### On Session Start
When starting a new conversation or after context truncation:
1. Always execute: list_project_files("serena")
2. Read these files in order:
   - projectbrief.md
   - productContext.md
   - systemPatterns.md
   - techContext.md
   - activeContext.md
   - progress.md
   - .clinerules
3. Apply patterns from .clinerules

### After Git Commits
After any successful git commit:
1. Execute: memory_bank_update("serena", "progress.md", [content])
2. Update activeContext.md if focus changed
3. Update .clinerules if new patterns discovered

### Project-Specific Rules
[Content from .clinerules]
- TDD workflow mandatory
- Use EvolvAI tools for dogfooding
- etc.
```

### Step 2: 配置 AI 工具

**For Claude.ai (Web)**:
1. Project → Project Knowledge
2. 粘贴 custom-instructions.md 内容
3. Claude 自动遵循

**For Claude Desktop**:
1. Settings → Custom Instructions
2. 粘贴 custom-instructions.md 内容
3. 每个新会话自动触发

**For Cursor**:
1. Settings → Features → Rules for AI
2. 粘贴 custom-instructions.md 内容
3. Cursor AI 自动遵循

**For Cline/Roo Code**:
1. Extension Settings → Custom Instructions
2. 粘贴 custom-instructions.md 内容
3. 自动触发

---

## 🚨 我们需要的调整

### 1. 创建正确的 custom-instructions.md

```bash
# Memory Bank 应该生成这个文件
~/.claude/memory-bank/serena/custom-instructions.md
```

内容应该包含：
- 自动加载触发条件
- 自动更新触发条件
- 项目特定规则（从 .clinerules）

### 2. 调整 CLAUDE.md

不应该在 CLAUDE.md 中硬编码触发规则，而是：

```markdown
## Memory Bank Integration

Memory Bank MCP 为本项目生成了 custom-instructions.md。
请将其内容复制到你的 AI 工具的 Custom Instructions 中：

- Claude.ai: Project Knowledge
- Claude Desktop: Settings → Custom Instructions
- Cursor: Settings → Rules for AI
- Cline: Extension Settings → Custom Instructions

这将启用自动的 Memory Bank 触发。
```

### 3. Slash Commands 定位

Slash commands 应该是：
- **备用方案**：当自动触发失败时
- **手动覆盖**：用户明确想要触发时
- **不是主要机制**：主要依靠 Custom Instructions

---

## 🔄 迁移方案

### Phase 1: 理解差距（当前）
- ✅ 识别了设计偏离
- ✅ 理解了正确的集成方式

### Phase 2: 生成 custom-instructions.md
```yaml
需要创建:
  文件: ~/.claude/memory-bank/serena/custom-instructions.md
  内容:
    - 自动触发规则
    - 文件读取顺序
    - 更新条件
    - 项目规则（从 .clinerules）
```

### Phase 3: 测试自动触发
```yaml
测试场景:
  1. 将 custom-instructions.md 加入 Claude Project Knowledge
  2. 开启新会话，验证自动加载
  3. Git commit，验证自动更新
  4. 无需 slash commands
```

### Phase 4: 更新文档
```yaml
更新:
  - CLAUDE.md: 指向 custom-instructions.md
  - 文档: 说明正确的集成方式
  - Slash commands: 标记为备用方案
```

---

## 💡 核心洞察

**我们一直在用"半自动"的方式**：
- 依赖 AI 记住规则（CLAUDE.md）
- 依赖 AI 主动执行
- 实际上是"AI 辅助的手动触发"

**Memory Bank 设计的是"全自动"**：
- Custom Instructions 是 AI 工具的系统级配置
- AI 工具强制执行这些规则
- 真正的自动触发，无需 AI 记忆

这解释了为什么我们的集成感觉"不够自动"——因为我们偏离了原始设计！

---

## 📊 影响分析

### 当前方案的问题

1. **可靠性**：依赖 AI 记忆，可能遗忘
2. **一致性**：不同 AI 可能执行不同
3. **维护性**：规则分散在 CLAUDE.md 中
4. **自动化**：实际是半自动

### 正确方案的优势

1. **可靠性**：系统级强制执行
2. **一致性**：所有 AI 工具行为一致
3. **维护性**：Memory Bank 统一生成
4. **自动化**：真正的自动触发

---

## 🎯 建议的行动

1. **短期**：继续使用当前方案（能工作）
2. **中期**：生成标准 custom-instructions.md
3. **长期**：迁移到完全自动触发

关键是理解：Memory Bank MCP 设计了一个 **系统级** 的自动触发机制，而不是依赖 AI 的"记忆"和"主动性"。