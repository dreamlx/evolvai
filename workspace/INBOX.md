# INBOX - 临时想法和待反思问题

**目的**: 存放未分类的想法、待深入分析的问题、临时笔记等
**整理周期**: 定期（每周/每次重大决策后）整理到对应的 docs/ 目录

---

## 🤔 2025-11-19 - MCP 工具暴露优化后的反思

### 问题：高层工具是否真正使用了符号操作？

**背景**:
- Phase 1-4 完成后，我们隐藏了 6 个符号操作工具
- 理由：符号操作应该是底层实现，LLM 应该只调用高层工具（batch_edit, safe_search）
- **假设**: batch_edit 内部使用了 find_symbol, replace_symbol_body 等符号工具

**需要验证**:
1. **batch_edit 实现**: 是否使用符号工具？还是纯文本替换？
   - 文件：`src/evolvai/tools/batch_edit_tool.py` 或相关实现
   - 查找：是否调用 `find_symbol()`, `replace_symbol_body()` 等

2. **safe_search 实现**: 是否使用符号工具来理解代码结构？
   - 文件：`src/evolvai/tools/safe_search.py`
   - 查找：是否使用符号级搜索

3. **propose_edit / apply_edit**: 是否使用符号工具？
   - 文件：`src/serena/tools/patch_editor_tools.py`

**可能的结果**:

**情况 A**: ✅ 高层工具确实使用了符号操作
- 结论：Phase 4 正确，符号操作作为内部实现
- 行动：无需修改

**情况 B**: ❌ 高层工具只是纯文本操作，没有用符号工具
- 结论：我们的架构有问题！
- 问题：
  1. 为什么开发了符号工具但不用？
  2. 高层工具（batch_edit）如何保证精确性？
  3. 是否应该重构 batch_edit 来使用符号工具？
- 行动：
  1. 重新评估工具分层设计
  2. 考虑重构 batch_edit 使用符号操作
  3. 或者，重新暴露符号工具（如果 batch_edit 无法实现符号级精确）

**情况 C**: 🤔 部分使用符号工具
- 结论：需要更细致的分析
- 行动：记录哪些场景用了符号工具，哪些没用

---

### 待验证检查清单

- [x] 读取 `batch_edit_tool.py` 源码
- [x] 读取 `batch_editor.py` 实现（如果有）
- [x] 搜索 `find_symbol` 在 evolvai 工具中的使用
- [x] 搜索 `replace_symbol_body` 在 evolvai 工具中的使用
- [x] 读取 `safe_search.py` 实现
- [x] 读取 `patch_editor_tools.py` 实现
- [ ] 总结：绘制实际的工具调用关系图

### ⚠️ 验证结果（2025-11-19）

**结论：情况 B - ❌ 高层工具只是纯文本操作，没有用符号工具！**

**证据**：

1. **batch_edit**:
   - 文件：`src/evolvai/tools/batch_editor.py:196`
   - 实现：`regex.subn(replacement, original_content)` - **纯正则替换**
   - ❌ 没有使用 `find_symbol`, `replace_symbol_body`

2. **safe_search**:
   - Grep 搜索：在 `evolvai/tools/` 中没有找到任何符号工具调用
   - ❌ 没有使用符号级搜索

3. **patch_editor (propose_edit/apply_edit)**:
   - Grep 搜索：在 `patch_editor_tools.py` 中没有找到符号工具调用
   - ❌ 没有使用符号操作

**架构现状**：
```
EvolvAI 高层工具 (batch_edit, safe_search, safe_exec)
   ↓ (不依赖)
   ✗ (隔离)
   ↓
Serena 符号工具 (find_symbol, replace_symbol_body, ...)
   ↓ (基于)
   LSP (Language Server Protocol)
```

**关键发现**：
- EvolvAI 和 Serena 是**两套独立的工具体系**
- EvolvAI 使用**文本级操作**（regex, glob, ripgrep）
- Serena 使用**符号级操作**（LSP-based）
- 两者之间**没有集成**！

---

### 相关设计原则问题

**问题 1**: Serena 的符号工具 vs EvolvAI 的高层工具
- Serena：基于 LSP (Language Server Protocol) 的符号操作
- EvolvAI：基于什么实现的？是否依赖 Serena 的符号工具？
- 架构问题：EvolvAI 应该是 Serena 的"上层"还是"独立"模块？

**问题 2**: 如果 batch_edit 不用符号工具，为什么？
- 技术原因：实现困难？性能问题？
- 设计原因：认为不需要符号级精确？
- 历史原因：开发顺序导致的？

**问题 3**: 工具暴露策略应该基于什么？
- 当前策略：LLM 调用意图（编辑/搜索/执行）
- 备选策略：功能完整性（如果 batch_edit 不够精确，暴露符号工具）
- 权衡：简洁性 vs 精确性

---

## 下一步行动

1. ✅ **完成**: 验证上述问题（读取源码） - 确认两套工具体系独立
2. **决策点**: 需要讨论的架构问题
   - **选项 A**: 保持现状 - EvolvAI(文本级) 和 Serena(符号级) 独立共存
     - 优点：各自独立，互不干扰
     - 缺点：功能重叠，LLM 需要选择用哪套工具

   - **选项 B**: 集成架构 - EvolvAI 底层使用 Serena 符号工具
     - 优点：统一架构，batch_edit 获得符号级精确性
     - 缺点：需要重构 EvolvAI，增加复杂度

   - **选项 C**: 暴露两套工具 - 给 LLM 选择权
     - 优点：灵活性最高，适应不同场景
     - 缺点：认知负担重，Token 消耗大

   - **选项 D (当前)**: 只暴露 EvolvAI - 隐藏 Serena 符号工具
     - 优点：简洁，Token 最优
     - 缺点：失去符号级精确操作能力

3. **待讨论**: 与用户讨论架构方向
4. **最后**: 将分析结果整理到 `docs/development/architecture/adrs/` 作为 ADR

---

## 其他待整理的想法

（留空，用于随时记录其他临时想法）
