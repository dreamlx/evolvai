# 贡献指南 - Contributing to EvolvAI

感谢您对 EvolvAI 项目的关注！我们欢迎各种形式的贡献。

## 🤝 如何贡献

### 🐛 报告问题
- 使用 [Issues](https://github.com/dreamlx/evolvai/issues) 报告 bug
- 提供详细的重现步骤和环境信息
- 包含相关的错误日志和截图

### 💡 提出功能建议
- 在 Issues 中描述功能需求和使用场景
- 说明该功能如何改善开发体验
- 提供设计思路或参考实现

### 🔧 提交代码

#### 开发环境设置
```bash
# 克隆仓库
git clone https://github.com/dreamlx/evolvai.git
cd evolvai

# 安装依赖
pip install -e ".[dev]"

# 运行测试
uv run poe test

# 代码格式化
uv run poe format

# 类型检查
uv run poe type-check
```

#### 开发流程
1. Fork 仓库到您的 GitHub 账户
2. 创建功能分支：`git checkout -b feature/your-feature-name`
3. 提交更改：`git commit -m "feat: add your feature"`
4. 推送到您的 fork：`git push origin feature/your-feature-name`
5. 创建 Pull Request

#### 代码规范
- 遵循 PEP 8 Python 编码规范
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串
- 确保所有测试通过

#### MCP Tool Guidelines

**Docstring Rule**: Class docstring ≤ 10 lines

- **Reason**: MCP tool descriptions are transmitted on every connection (~1 token/word)
- **Example**: See `src/evolvai/tools/batch_edit_tool.py` (after cleanup)
- **Detailed guides**: Use `docs/guides/` for educational content instead

**Why this limit**: batch_edit had 160-line docstring = 1.5k wasted tokens per session

**What goes in tool docstring** (≤ 10 lines):
- Single-sentence capability statement
- 2-3 key constraints or features
- Reference to detailed guide

**What goes in docs/guides/** (unlimited):
- Tool selection frameworks (Level 1/2/3)
- Usage examples and case studies
- Common mistakes and solutions
- Design philosophy and rationale

## 🎯 贡献方向

### 🌍 环境支持扩展
- **Windows 环境**：PowerShell, CMD 检测和优化
- **Linux 桌面环境**：GNOME, KDE 等环境适配
- **容器化环境**：Docker, Podman, Kubernetes 支持
- **云开发环境**：GitHub Codespaces, Gitpod 集成

### 📝 编程语言支持
- **Rust**：Cargo, rustfmt, clippy 集成
- **Go**：go mod, golangci-lint 集成
- **TypeScript**：tsconfig, ESLint, Prettier 集成
- **Java/Kotlin**：Gradle, Maven, Ktlint 集成
- **C#**：.NET CLI, dotnet format 集成

### 🤖 AI 工具集成
- **GitHub Copilot**：深度集成和优化建议
- **Cursor**：环境感知和上下文提供
- **Tabnine**：代码补全优化
- **Amazon CodeWhisperer**：环境适配
- **本地 LLM**：Ollama, LM Studio 集成

### 📊 高级功能
- **可视化仪表板**：环境配置和学习进度展示
- **团队协作**：共享编码规范和环境配置
- **性能分析**：AI 工具使用效率统计
- **智能推荐**：基于使用模式的工具推荐
- **多项目管理**：跨项目环境配置同步

### 📚 文档改进
- **使用教程**：详细的功能使用指南
- **最佳实践**：不同开发场景的配置建议
- **故障排除**：常见问题和解决方案
- **API 文档**：接口说明和示例代码

## 🏗️ 项目结构

```
evolvai/
├── src/evolvai/              # 核心代码
│   ├── memory/              # 智能记忆系统
│   ├── tools/               # AI 工具集成
│   ├── cli/                 # 命令行接口
│   └── integration/         # 第三方集成
├── tests/                   # 测试套件
├── docs/                    # 文档
├── examples/                # 使用示例
└── scripts/                 # 开发脚本
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
uv run poe test

# 运行特定测试
uv run poe test tests/memory/

# 生成覆盖率报告
uv run poe test --cov=evolvai
```

### 添加测试
- 为新功能添加单元测试
- 确保测试覆盖率不低于 80%
- 使用清晰的测试描述和断言

## 📝 提交信息规范

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**类型说明：**
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建工具或辅助工具的变动

**示例：**
```
feat(memory): add Rust environment detection

- Implement Cargo.toml parsing for project type detection
- Add rustfmt and clippy command optimization
- Support Rust naming conventions (snake_case for functions)

Closes #123
```

## 🏆 贡献者认可

所有贡献者都会在项目中得到认可：

- 在 README 中添加贡献者列表
- 在 CHANGELOG 中记录重要贡献
- 在发布说明中特别感谢

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/dreamlx/evolvai/issues)
- **讨论区**: [GitHub Discussions](https://github.com/dreamlx/evolvai/discussions)
- **邮箱**: contributors@evolvai.dev

## 📄 许可证

通过贡献代码，您同意您的贡献将在 [MIT License](LICENSE) 下发布。

---

感谢您的贡献！🎉