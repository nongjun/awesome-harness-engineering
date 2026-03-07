# Awesome Harness Engineering

> 为 Vibe Coding 团队打造的 Cursor AI 编程辅助配置

[![GitHub Stars](https://img.shields.io/github/stars/nongjun/awesome-harness-engineering?style=flat)](https://github.com/nongjun/awesome-harness-engineering/stargazers)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 什么是 Harness Engineering？

当你的团队通过 **Vibe Coding**（自然语言指挥 AI 写代码）开发产品时，AI 就是你唯一的"程序员"。Harness Engineering 就是给这个程序员写的**工作手册**——告诉它遵循什么规范、怎么审查代码、怎么保障安全、怎么积累团队经验。

装上后，Cursor 就从"能写代码"升级为"懂规范、会审查、有安全意识、能自我验证"的专业搭档。

## 设计理念

1. **中文优先** — 命令名、技能名、文档全中文，非技术团队直接看懂
2. **简短信任** — 命令不写代码示例，充分信任大模型，随模型升级自动变强
3. **灵活组合** — 审查、测试、修复独立命令，按需串联
4. **跨项目通用** — 同一套命令适用于 Python/Go/小程序/Mac 应用等任何项目
5. **闭环验证** — 做完就验，验完就沉淀
6. **按需加载** — 仅 65 行固定上下文消耗，其余全部 globs 按需触发

## 包含内容

```
awesome-harness-engineering/
├── rules/              # 10 个规则（2 个 alwaysApply + 8 个 globs 按需）
├── agents/             # 5 个代理（AI 自动调度）
├── commands/           # 21 个命令（输入 /命令名 使用）
├── skills/             # 9 个通用技能（AI 按需参考）
├── hooks/              # 3 个自动化触发（编辑后/提交前/会话结束）
└── 项目模板/            # 特定项目的额外配置示例
```

## 安装

**把以下文字发给 Cursor AI，它会自动完成安装：**

> 请帮我从 GitHub 下载并安装 harness 配置到当前项目。
>
> 步骤：
> 1. `git clone https://github.com/nongjun/awesome-harness-engineering.git /tmp/harness-install`
> 2. 复制通用配置到 `.cursor/` 目录：
> ```bash
> PROJECT=".cursor"
> HARNESS="/tmp/harness-install"
> mkdir -p "$PROJECT/rules" "$PROJECT/agents" "$PROJECT/commands" "$PROJECT/skills"
> cp -r "$HARNESS/rules/"* "$PROJECT/rules/"
> cp -r "$HARNESS/agents/"* "$PROJECT/agents/"
> cp -r "$HARNESS/commands/"* "$PROJECT/commands/"
> cp -r "$HARNESS/skills/"* "$PROJECT/skills/"
> cp "$HARNESS/hooks/hooks.json" "$PROJECT/hooks.json" 2>/dev/null
> ```
> 3. `rm -rf /tmp/harness-install`
> 4. 告诉我安装了多少个文件。

安装完在 Cursor 中输入 `/` 就能看到全部中文命令。

## 命令速查

### 开发阶段

| 命令 | 什么时候用 |
|------|-----------|
| /规划实施方案 | 开始新功能前，先想清楚 |
| /代码审查专家 | 写完代码后，检查质量和安全 |
| /测试后端Api | 检查后端 API 是否正常 |
| /修复构建错误 | 项目跑不起来时 |
| /一键验证全部检查 | 提交前确认没破坏任何东西 |
| /审查刚才的文件与操作 | 做完一波操作后自检 |
| /全维度严格审查 | 发布前 6 个子 agent 并行全面体检 |
| /端到端测试 | 用无头浏览器测试关键用户流程 |

### 检查与维护

| 命令 | 什么时候用 |
|------|-----------|
| /检查系统的健康 | 看看整个系统是否正常运行 |
| /检查可复用的代码 | 找出可以提取的公共模块 |
| /架构师合并重复代码 | 清理重复代码 |
| /评估代码质量 | 给功能或代码打分 |
| /项目总监审视项目 | 以用户视角挑毛病 |

### 文档与沉淀

| 命令 | 什么时候用 |
|------|-----------|
| /更新项目文档 | 改完代码后同步文档 |
| /复盘并沉淀规则 | 踩完坑后总结经验写入规则 |
| /提取本次经验 | 会话结束时提炼收获 |
| /从Git提取团队习惯 | 分析 Git 历史，自动提取编码习惯 |

### 流程管理

| 命令 | 什么时候用 |
|------|-----------|
| /编排工作流 | 串联多个命令为自动流程 |
| /保存安全检查点 | 大改动前存一个安全回退点 |
| /会话摘要与交接 | 查看本次会话做了什么、交接给新会话 |
| /Git提交和推送 | 提交和推送代码 |

## 代理（AI 自动调度）

| 代理 | 自动触发场景 |
|------|-------------|
| 调试专家 | 遇到报错、异常时 |
| 测试专家 | 代码变更后 |
| 安全卫士 | 涉及用户输入、认证、API 时 |
| 构建修复师 | 构建失败时 |
| 端到端测试专家 | 需要验证完整用户流程时 |

## 规则（按需加载策略）

| 规则 | 加载方式 |
|------|---------|
| 基础规则（含 Agent 路由表） | 每次会话加载（37 行） |
| 安全红线 | 每次会话加载（28 行） |
| Python 编码风格 / 安全 | 编辑 `.py` 文件时 |
| Go 编码风格 / 安全 | 编辑 `.go` 文件时 |
| Swift 编码风格 | 编辑 `.swift` 文件时 |
| 通用编码风格 | 编辑任何代码文件时 |
| 技术栈标准 | 编辑 Docker/部署配置时 |
| 小助手注册规范 | 编辑 webhook 相关代码时 |

**每次会话固定消耗仅 65 行，其余按需加载。**

## 自动化 Hook

| 触发时机 | 做什么 |
|----------|--------|
| 编辑代码文件后 | 提醒检查文档是否需要同步 |
| 提交提示词前 | 自动扫描是否包含 API Key/密码等密钥 |
| 会话结束时 | 提醒沉淀经验 |

## 技能

**通用流程：** 闭环自验证、页面健康检查、文档园丁、文档库构建、技能创建器、移动端适配

**语言专属：** Go 开发模式、微信小程序、macOS 应用

## 闭环体系

```
开发闭环：规划 → 开发 → 审查 → 测试 → 修复 → 再验证
知识闭环：实践 → 沉淀规则 → 下次自动避免
文档闭环：改代码 → Hook 提醒 → 文档园丁巡检 → 更新文档
安全闭环：写代码 → 安全卫士 → 提交前密钥检测 → 验证时安全扫描
```

## 技术栈支持

Python / Go / Swift / TypeScript / Vue / 微信小程序 / Docker / Nginx / MySQL

## 项目模板

`项目模板/` 目录包含特定项目的额外配置示例。你可以为自己的项目创建类似的模板，将项目专属的规则、命令、技能放入，团队成员直接复制使用。

## 第一次使用建议

安装完毕后，推荐先用 `/文档库构建` 让 AI 为你的项目搭建文档体系（包括 Cursor 必读的 AGENTS.md），这样 AI 就能更好地理解你的项目。

## 致谢

设计灵感参考了 [Everything Claude Code](https://github.com/affaan-m/everything-claude-code)（Anthropic 黑客松获奖项目），在其自动化和安全体系基础上融入了实战经验：闭环验证、规则沉淀、文档园丁、先策略后执行。

## License

MIT
