# 瑞小美团队 Harness Engineering

> 为瑞小美轻医美集团高管团队打造的 AI 编程辅助配置

## 团队背景

我们是一群不懂代码的高管，通过 vibe coding（自然语言指挥 AI 写代码）方式开发产品。AI 是我们唯一的"程序员"，这套配置就是 AI 的"工作手册"。

## 设计理念

1. **中文优先** — 命令名、技能名、文档全中文，团队成员直接看懂
2. **简短信任** — 命令不写代码示例，充分信任大模型，随模型升级自动变强
3. **灵活组合** — 审查、测试、修复独立命令，按需串联
4. **跨项目通用** — 同一套命令适用于 Python/Go/小程序/Mac 应用等任何项目
5. **闭环验证** — 做完就验，验完就沉淀
6. **自动化兜底** — Hook 防止人为遗忘

## 目录结构

```
瑞小美-harness/
├── rules/              # 通用规则（所有项目自动生效）
├── agents/             # 通用代理（AI 自动调度）
├── commands/           # 通用命令（输入 /命令名 使用）
├── skills/             # 通用技能（AI 按需参考）
├── hooks/              # 自动化触发
└── 项目模板/            # 特定项目的额外配置（按需复制）
    └── 瑞小美AiOS/    # AiOS 项目专属规则、命令、技能
```

## 通用组件

### 规则（自动生效，无需操作）

| 规则 | 作用 |
|------|------|
| 基础规则 | 中文回复、子 agent 并行、先策略后执行 |
| 安全红线 | 禁止硬编码密钥、安全检查清单 |

### 代理（AI 自动调度，无需手动调用）

| 代理 | 自动触发场景 |
|------|-------------|
| 调试专家 | 遇到报错、异常时 |
| 测试专家 | 代码变更后 |
| 安全卫士 | 涉及用户输入、认证、API 时 |
| 构建修复师 | 构建失败时 |
| 端到端测试专家 | 需要验证完整用户流程时 |

### 命令速查（输入 /命令名 使用）

| 命令 | 什么时候用 |
|------|-----------|
| /规划实施方案 | 开始新功能前，先想清楚 |
| /代码审查专家 | 写完代码后，检查质量和安全 |
| /测试后端Api | 检查后端 API 是否正常 |
| /修复构建错误 | 项目跑不起来时 |
| /一键验证全部检查 | 提交前确认没破坏任何东西 |
| /审查刚才的文件与操作 | 做完一波操作后自检 |
| /检查系统的健康 | 看看整个系统是否正常运行 |
| /检查可复用的代码 | 找出可以提取的公共模块 |
| /架构师合并重复代码 | 清理重复代码 |
| /更新项目文档 | 改完代码后同步文档 |
| /复盘并沉淀规则 | 踩完坑后总结经验写入规则 |
| /提取本次经验 | 会话结束时提炼收获 |
| /评估代码质量 | 给功能或代码打分 |
| /项目总监审视项目 | 以用户视角挑毛病 |
| /编排工作流 | 串联多个命令为自动流程 |
| /保存安全检查点 | 大改动前存一个安全回退点 |
| /会话摘要与交接 | 查看本次会话做了什么、交接给新会话 |
| /从Git提取团队习惯 | 分析 Git 历史，提取团队编码习惯 |
| /全维度严格审查 | 6 个子 agent 并行做全面代码体检（发布前/外部代码接入） |
| /端到端测试 | 用无头浏览器测试关键用户流程 |
| /Git提交和推送 | 提交和推送代码 |

### 技能（AI 自动参考，无需手动调用）

**通用流程技能：**

| 技能 | 作用 |
|------|------|
| 闭环自验证 | 写代码→构建→检查→验证→修复→再验证 |
| 页面健康检查 | 截屏→交互→数据/视觉/性能检查→修复 |
| 文档园丁 | 巡检、整理、审计项目文档 |
| 文档库构建 | 新项目首次搭建文档体系 |
| 技能创建器 | 交互式创建新的 Skill |
| 移动端适配 | Vue 管理后台的移动端适配 |

**语言专属技能：**

| 技能 | 适用场景 |
|------|----------|
| Go开发模式 | Go 后端服务、微服务、CLI 工具 |
| 微信小程序 | 微信小程序、Uni-app 跨平台 |
| macOS应用 | Swift/SwiftUI 桌面应用 |

### 自动化 Hook

| 触发时机 | 自动做什么 |
|----------|-----------|
| 编辑代码文件后 | 提醒检查文档是否需要同步（调用文档园丁） |
| 提交代码前 | 检测是否包含 API Key/密码等敏感信息 |
| 会话结束时 | 提醒：有没有值得沉淀的经验？ |

## 部署与使用

### 前置知识

- **Cursor** 是我们团队使用的 AI 编程工具
- Cursor 会自动读取项目中 `.cursor/` 目录下的配置文件来增强 AI 能力
- 本 harness 就是一套放入 `.cursor/` 目录的配置文件

### GitHub 仓库

```
https://github.com/nongjun/awesome-harness-engineering
```

### 安装到你的项目（让 AI 帮你做）

**直接复制以下文字发给 Cursor AI，它会自动完成安装：**

---

请帮我从 GitHub 下载并安装团队 harness 配置到当前项目。

**操作步骤：**

1. 克隆 harness 仓库到临时目录：

```bash
git clone https://github.com/nongjun/awesome-harness-engineering.git /tmp/harness-install
```

2. 在当前项目根目录下创建 `.cursor/` 目录并复制通用配置：

```bash
PROJECT=".cursor"
HARNESS="/tmp/harness-install"

mkdir -p "$PROJECT/rules" "$PROJECT/agents" "$PROJECT/commands" "$PROJECT/skills"

cp -r "$HARNESS/rules/"* "$PROJECT/rules/"
cp -r "$HARNESS/agents/"* "$PROJECT/agents/"
cp -r "$HARNESS/commands/"* "$PROJECT/commands/"
cp -r "$HARNESS/skills/"* "$PROJECT/skills/"
cp "$HARNESS/hooks/hooks.json" "$PROJECT/hooks.json" 2>/dev/null
```

3. 清理临时目录：

```bash
rm -rf /tmp/harness-install
```

4. 完成后告诉我安装了多少个规则、代理、命令、技能。

---

### 额外加载瑞小美 AiOS 专属配置（仅 AiOS 项目需要）

如果你的项目是瑞小美 AiOS，安装通用配置后再额外执行：

```bash
git clone https://github.com/nongjun/awesome-harness-engineering.git /tmp/harness-install
PROJECT=".cursor"
HARNESS="/tmp/harness-install"

cp -r "$HARNESS/项目模板/瑞小美AiOS/rules/"* "$PROJECT/rules/"
cp -r "$HARNESS/项目模板/瑞小美AiOS/commands/"* "$PROJECT/commands/"
cp -r "$HARNESS/项目模板/瑞小美AiOS/skills/"* "$PROJECT/skills/"
rm -rf /tmp/harness-install
```

### 安装后验证

安装完成后，在 Cursor 中输入 `/` 应该能看到所有中文命令列表。如果看不到，重启 Cursor 即可。

### 更新 harness

当 harness 有更新时，重新执行上面的安装命令即可（会自动覆盖旧文件）。

### 为新项目创建专属配置

当你的项目积累了独特的规则和技能时：
1. Fork 本仓库
2. 在 `项目模板/` 下创建一个以你的项目命名的目录
3. 将项目专属的规则、命令、技能放入
4. 提交 PR，团队其他成员可以直接使用

### 第一次使用建议

安装完毕后，推荐先用 `/文档库构建` 命令让 AI 为你的项目搭建文档体系（包括 Cursor 必读的 AGENTS.md），这样 AI 就能更好地理解你的项目。

## 技术栈支持

- Python 3.11 / FastAPI / SQLAlchemy
- Go
- 微信小程序 / Uni-app
- macOS 应用 / Swift / SwiftUI
- Vue 3 / TypeScript / Element Plus
- Docker / Nginx / MySQL

## 致谢

设计灵感参考了 [Everything Claude Code](https://github.com/affaan-m/everything-claude-code)（Anthropic 黑客松获奖项目），在其自动化和安全体系基础上融入了瑞小美团队的实战经验：闭环验证、规则沉淀、文档园丁、先策略后执行。
