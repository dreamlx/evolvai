# MCP接口整理 - 2025-01-07

## 概述

对EvolvAI项目的MCP工具接口进行了整理，解决了命名冲突和定位不清的问题。

## 修复的问题

### P0问题 - 立即修复

#### 1. Memory工具命名冲突
**问题**: `memory_tools.py` 和 `legacy_memory_tools.py` 导出了相同的4个工具名称
```
write_memory, read_memory, list_memories, delete_memory
```

**解决方案**: 采用方案A - 从MCP暴露中移除Memory工具
- 移除 `src/serena/tools/__init__.py` 中的 `from .legacy_memory_tools import *`
- 保留文件用于向后兼容，但不再通过MCP暴露
- 添加注释说明Memory是AI助手内部机制，不是用户工具

**影响**:
- MCP工具数量: 53 → 45 (减少8个)
- 命名冲突: ✅ 已解决
- 符合EvolvAI定位: Memory是AI内部机制

#### 2. optimize_a_i_tools命名错误
**问题**: `OptimizeAIToolsTool` 自动转换为 `optimize_a_i_tools` (错误)
**原因**: "AI"被识别为两个独立大写字母

**解决方案**: 覆盖 `get_name()` 方法
```python
def get_name(self) -> str:
    """Override default conversion to fix AI naming issue."""
    return "optimize_ai_tools"
```

**结果**: `optimize_ai_tools` (正确)

## 最终MCP工具状态

### 工具数量
- **修复前**: 53个工具 (包含4个重复memory工具)
- **修复后**: 45个工具 (无重复)
- **净减少**: 8个工具

### 工具分布
```
advanced_intelligent_tools: 4个
cmd_tools: 1个
coding_standards_tools: 3个
config_tools: 4个
file_tools: 9个
intelligent_tools: 3个
jetbrains_tools: 3个
patch_editor_tools: 2个
symbol_tools: 8个
workflow_tools: 8个
```

### 质量指标
- ✅ 命名冲突: 0个
- ✅ 所有工具名清晰规范
- ✅ 符合EvolvAI AI优化定位
- ✅ Memory正确定位为内部机制

## 设计决策

### Memory工具定位
**决策**: Memory是AI助手内部机制，不应暴露给用户

**理由**:
1. **EvolvAI定位**: AI行为优化平台，不是通用存储
2. **实际用途**: AI跨会话记忆、经验积累、任务状态追踪
3. **用户需求**: docs/文件夹用于文档，Git用于版本控制
4. **避免混乱**: 防止用户误删AI需要的记忆

### 向后兼容性
- 保留 `memory_tools.py` 和 `legacy_memory_tools.py` 文件
- Agent内部仍可通过 `MemoriesManager` 使用
- 仅移除MCP暴露，不影响内部功能

## 后续建议

### P1建议 (高优先级)
1. **重命名JetBrains工具**: 简化为 `jb_*` 前缀
2. **重组AI工具模块**: 合并 `intelligent_tools` + `advanced_intelligent_tools` + `coding_standards_tools`

### P2建议 (中优先级)
1. **引入命名空间**: 考虑 `symbol:find`, `file:read` 等分层命名
2. **模块重组**: 按Epic分组 (epic001_constraints/, epic002_standards/, epic003_thinking/)

### 长期规划
1. **API版本化**: 支持工具演进而不破坏兼容性
2. **工具分类标记**: 增加更细粒度的工具分类和标记

## 技术细节

### 修改的文件
1. `src/serena/tools/__init__.py`
   - 移除 `from .legacy_memory_tools import *`
   - 添加说明注释

2. `src/serena/tools/advanced_intelligent_tools.py`
   - 添加 `get_name()` 方法覆盖
   - 修复AI命名问题

### 验证方法
```bash
# 验证MCP工具清单
python3 tools/verify_mcp_tools.py

# 检查命名冲突
python3 tools/check_naming_conflicts.py

# 测试get_name覆盖
uv run python -c "from serena.tools.advanced_intelligent_tools import OptimizeAIToolsTool; print(OptimizeAIToolsTool.get_name())"
```

## 影响评估

### 正面影响
- ✅ 清晰的工具定位和分类
- ✅ 消除命名冲突
- ✅ 符合EvolvAI产品定位
- ✅ 减少用户混淆

### 风险评估
- ⚠️ 外部代码直接调用memory工具会受影响 (低风险，memory工具本就标记为deprecated)
- ⚠️ 需要文档更新用户了解变化 (已通过本文档处理)

## 结论

本次MCP接口整理成功解决了关键的P0问题：
1. 消除了4个memory工具的命名冲突
2. 修复了optimize_ai_tools命名错误
3. 明确了Memory作为AI内部机制的定位
4. 减少了8个冗余工具，提升了接口清晰度

整理后的MCP接口更加清晰、规范，符合EvolvAI作为AI行为优化平台的定位。Memory工具不再暴露给用户，避免了误用风险，同时保持了内部功能的完整性。

---
**整理日期**: 2025-01-07
**整理范围**: P0问题修复
**状态**: ✅ 完成
**下次审查**: P1建议实施前