# EvolvAI

<div align="center">
  <h3>🧠 智能开发环境学习助手</h3>
  <p>让 AI 编程助手理解你的开发环境和编码习惯</p>

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Tests](https://img.shields.io/badge/Tests-✅-brightgreen.svg)](tests/)
  [![GitHub stars](https://img.shields.io/github/stars/dreamlx/evolvai.svg?style=social&label=Star)](https://github.com/dreamlx/evolvai)
</div>

---

## 🎯 为什么需要 EvolvAI？

### 🤔 **当前痛点**
- AI 助手不了解你的开发环境（zsh vs bash, uv vs poetry）
- 生成的代码不符合项目编码规范（camelCase vs snake_case）
- 缺乏项目上下文，无法提供精准建议
- 每次都需要提醒 AI 你的环境配置

### ✨ **EvolvAI 解决方案**
- 🌍 **环境学习**：自动检测和学习你的 Shell、Python、Node.js 环境
- 📝 **编码规范**：分析项目代码，学习命名约定和风格偏好
- 🤖 **智能优化**：为 AI 工具提供环境适配的命令和代码建议
- 💾 **持续记忆**：跨会话保持学习成果，越用越懂你

---

## 🚀 核心功能

### 🌍 **环境偏好学习**
```bash
# 自动检测环境
evolvai detect

# 生成优化命令
evolvai optimize "run tests"  # → uv run poe test
```

### 📝 **编码标准分析**
```bash
# 分析项目编码规范
evolvai analyze-standards

# 应用编码规范到生成代码
evolvai apply-standards "create user service"
```

### 🤖 **AI 工具集成**
- 🔄 Claude Code 集成
- 🔄 Cursor 集成
- 🔄 GitHub Copilot 集成
- 🔄 其他 AI 编程助手支持

---

## 🛠️ 快速开始

### 安装
```bash
pip install evolvai
```

### 基础使用
```bash
# 1. 初始化项目环境学习
evolvai init

# 2. 检测当前环境
evolvai detect

# 3. 分析项目编码规范
evolvai analyze

# 4. 生成优化建议
evolvai optimize "format code"
```

### AI 助手集成
```bash
# Claude Code 集成
evolvai setup claude

# Cursor 集成
evolvai setup cursor

# 查看当前环境配置
evolvai status
```

---

## 📊 使用示例

### 环境优化示例
```bash
$ evolvai optimize "run tests"
→ uv run poe test

$ evolvai optimize "format code"
→ uv run poe format

$ evolvai optimize "type check"
→ uv run poe type-check
```

### 代码生成示例
```python
# 输入提示："create user validation function"
# EvolvAI 理解你的 Python snake_case 约定
def validate_user_data(user_input: dict) -> bool:
    """Validate user input data according to project standards."""
    # 生成的代码符合项目命名约定
```

---

## 🏗️ 架构设计

```
EvolvAI/
├── 🧠 Core Intelligence
│   ├── Environment Learning    # 环境学习引擎
│   ├── Coding Standards Analysis # 编码标准分析
│   └── AI Tool Optimization     # AI 工具优化
├── 🤖 Integration Layer
│   ├── Claude Code Integration
│   ├── Cursor Integration
│   └── MCP Protocol Support
└── 📚 Learning Memory
    ├── Environment Preferences
    ├── Coding Patterns
    └── Usage Analytics
```

---

## 🎨 特色功能

### 🔄 **持续学习**
- 每次交互都在学习你的偏好
- 跨项目环境配置迁移
- 智能模式识别和适应

### 🎯 **精准适配**
- 基于真实项目环境的建议
- 考虑团队协作的编码约定
- 支持多语言、多框架

### 🔧 **工具无关**
- 不绑定特定 AI 工具
- 支持多种开发环境
- 灵活的配置和扩展

---

## 📈 对比优势

| 特性 | 传统 AI 助手 | EvolvAI |
|------|------------|--------|
| 环境感知 | ❌ | ✅ |
| 编码规范学习 | ❌ | ✅ |
| 持续记忆 | ❌ | ✅ |
| 命令优化 | ❌ | ✅ |
| 多工具支持 | ❌ | ✅ |

---

## 🤝 贡献

我们欢迎社区贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 贡献方向
- 🌍 更多环境支持（Windows, Linux 桌面环境）
- 📝 更多编程语言支持（Rust, Go, TypeScript）
- 🤖 更多 AI 工具集成
- 📊 高级分析和可视化

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

基于 Serena 的 LSP 分析能力，感谢所有贡献者和用户反馈

---

<div align="center">
  <p>🌟 如果 EvolvAI 提升了你的开发体验，请给我们一个 Star！</p>
</div>