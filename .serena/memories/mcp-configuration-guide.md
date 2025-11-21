# EvolvAI MCP 配置指南

**创建日期**: 2025-11-17  
**类型**: 配置文档  
**状态**: [ACTIVE]

---

## 问题诊断与解决记录

### 原始问题

用户尝试连接 EvolvAI MCP server 到 Claude Desktop，但连接失败。

### 诊断过程

发现了 **3 个配置错误**：

#### 1. 参数格式错误
```json
// ❌ 错误
"args": ["--context", "ide-assistant-dogfooding", "--modes", "interactive,editing"]

// ✅ 正确
"args": ["--context", "ide-assistant-dogfooding", "--mode", "interactive", "--mode", "editing"]
```

**关键点**: 
- `--modes` → `--mode` (单数形式)
- 逗号分隔 → 多次指定参数

#### 2. 旧版项目配置格式
```yaml
# ❌ 旧格式 (ai_overseer 项目)
languages:
- python

# ✅ 新格式
language: python
```

**影响**: 导致 SerenaAgent 初始化时 `KeyError: 'language'`

#### 3. .claude.json 配置未同步
配置文件位置: `/Users/dreamlinx/.claude.json`
结构: 按项目路径分级存储 MCP 配置

**修复方法**: Python 脚本自动更新

---

## 正确的 MCP 配置

### Claude Desktop 配置文件

文件位置: `/Users/dreamlinx/.claude.json`

```json
{
  "projects": {
    "/Users/dreamlinx/Dropbox/Projects/opensource/serena": {
      "mcpServers": {
        "evolvai": {
          "type": "stdio",
          "command": "/Users/dreamlinx/Dropbox/Projects/opensource/serena/.venv/bin/evolvai-mcp-server",
          "args": [
            "--context",
            "ide-assistant-dogfooding",
            "--mode",
            "interactive",
            "--mode",
            "editing"
          ],
          "env": {}
        }
      }
    }
  }
}
```

### 验证启动成功

```bash
# 测试命令
timeout 3 /path/to/.venv/bin/evolvai-mcp-server \
  --context ide-assistant-dogfooding \
  --mode interactive \
  --mode editing

# 成功标志
✅ INFO ... Starting Serena server (version=0.1.4-...)
✅ INFO ... Loaded tools (49): ...
✅ INFO ... Active tools (32): ...
✅ INFO ... Starting MCP server with 32 tools: [...]
```

---

## MCP Servers 使用策略

### Serena vs EvolvAI 工具分工

#### Serena MCP (23 工具)
**优势**: 成熟稳定的 LSP 工具集
- ✅ 符号操作: `find_symbol`, `replace_symbol_body`, `rename_symbol`
- ✅ 文件操作: `list_dir`, `find_file`, `search_for_pattern`
- ✅ **记忆系统**: `read_memory`, `write_memory`, `list_memories`, `edit_memory`
- ✅ 项目管理: `activate_project`, `onboarding`

#### EvolvAI MCP (32 工具)
**优势**: 行为优化和智能约束
- ✅ 所有 Serena 基础工具（继承）
- 🆕 **行为约束**: `safe_search`, `safe_exec`, `batch_edit`
- 🆕 **代码编辑优化**: `propose_edit`, `apply_edit`
- 🆕 **智能记忆增强**:
  - `detect_environment` - 环境偏好学习
  - `analyze_coding_standards` - 编码规范学习
  - `generate_optimized_code` - 智能代码生成
  - `show_intelligent_memory_status` - 记忆状态查看

### 当前使用建议 (Epic-001 开发阶段)

```
优先使用: Serena MCP
场景补充: EvolvAI MCP
```

**具体场景**:

| 任务类型 | 使用 MCP | 理由 |
|---------|---------|------|
| 读取项目记忆 | Serena | 稳定，直接访问 `.serena/memories/` |
| 符号级代码编辑 | Serena | 成熟的 LSP 集成 |
| 批量文件修改 | EvolvAI | `batch_edit` 更高效 |
| 测试命令执行 | EvolvAI | `safe_exec` 带超时保护 |
| 代码搜索（大量结果） | EvolvAI | `safe_search` 带结果限制 |
| 学习编码规范 | EvolvAI | 智能记忆功能 |

### 未来使用策略 (Epic-001 完成后)

```
主要使用: EvolvAI MCP
后备使用: Serena MCP (仅在 EvolvAI 工具失败时)
```

---

## 记忆系统架构

### 共享存储

两个 MCP 共享同一个记忆存储位置:

```
.serena/memories/
├── serena_repository_structure.md
├── project-history-and-repositioning.md
├── feature-2.2-tdd-lessons-learned.md
├── mcp-configuration-guide.md  ← 本文档
└── ...
```

### 工具可用性验证

**Serena MCP**:
- ✅ `read_memory`, `write_memory`, `list_memories`, `edit_memory`
- 直接访问 `.serena/memories/`

**EvolvAI MCP**:
- ✅ 继承所有 Serena 工具，同样可以访问
- ✅ Memory 工具**未**被 `ide-assistant-dogfooding` context 排除
- 🆕 智能记忆（环境偏好、编码规范）存储在独立位置

**排除的是文件工具，不是记忆工具**:
```yaml
excluded_tools:
  - create_text_file      # ← 文件操作
  - read_file             # ← 文件操作
  - execute_shell_command # ← Shell 操作
  - prepare_for_new_conversation
  - replace_regex         # ← 编辑操作

# Memory 工具 NOT in exclude list → 可用！
✅ read_memory
✅ write_memory
✅ list_memories
✅ edit_memory
```

---

## EvolvAI Dogfooding 最佳实践

### Dogfooding 目标

用 EvolvAI 工具改进 EvolvAI 本身，验证 TPST 优化假设。

### 推荐工具使用

**批量代码修改**:
```python
# 使用 batch_edit 而非手动逐文件编辑
batch_edit(
    pattern=r"old_pattern",
    replacement=r"new_pattern",
    scope="src/**/*.py",
    preview=True  # 先预览再应用
)
```

**安全测试执行**:
```python
# 使用 safe_exec 带超时保护
safe_exec(
    command="uv run poe test",
    timeout=120,  # 2分钟超时
    working_dir="."
)
```

**受限结果搜索**:
```python
# 使用 safe_search 避免结果爆炸
safe_search(
    query="find authentication handler",
    max_results=50,
    mode="balanced"
)
```

### 数据收集重点

1. **TPST 追踪**: 记录每个工具的 token 消耗和执行时间
2. **效率对比**: 对比使用 EvolvAI 工具 vs 传统方法的 TPST
3. **约束验证**: 验证 ExecutionPlan 是否有效防止低效行为
4. **痛点记录**: 文档工具使用中的问题和改进机会

---

## 故障排查清单

### MCP 连接失败

1. **检查命令格式**
   ```bash
   # 验证 help 输出
   /path/to/.venv/bin/evolvai-mcp-server --help
   ```

2. **检查项目配置**
   ```bash
   # 验证 language 字段存在
   cat .serena/project.yml | grep "language:"
   ```

3. **查看日志**
   ```bash
   # 最新日志
   tail -50 ~/.serena/logs/$(date +%Y-%m-%d)/mcp_*.txt
   ```

4. **测试手动启动**
   ```bash
   timeout 3 /path/to/evolvai-mcp-server \
     --context ide-assistant-dogfooding \
     --mode interactive \
     --mode editing
   ```

### 常见错误

**错误**: `Mode interactive,editing not found`
- **原因**: 使用逗号分隔模式
- **修复**: 分开指定 `--mode interactive --mode editing`

**错误**: `KeyError: 'language'`
- **原因**: 项目配置使用旧格式 `languages: [...]`
- **修复**: 更新为 `language: python`

**错误**: `Command not found: evolvai-mcp-server`
- **原因**: 使用相对路径或 PATH 不正确
- **修复**: 使用绝对路径到 `.venv/bin/evolvai-mcp-server`

---

## 相关文档

- **CLAUDE.md**: MCP Servers Configuration 章节
- **project-history-and-repositioning.md**: EvolvAI 项目定位
- **ide-assistant-dogfooding.yml**: EvolvAI context 配置
- **docs/development/git-workflow.md**: Git 工作流程

---

**维护者**: EvolvAI Team  
**最后更新**: 2025-11-17  
**下次审查**: Epic-001 完成后
