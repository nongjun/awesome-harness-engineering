---
name: site-inspector
description: 通过 Playwright 多浏览器并行巡检 AiOS 全站页面。每次运行前自动扫描 Vue Router 文件获取最新路由表，无需手工维护。截图、控制台与网络错误检测、白屏与模拟数据识别、安全交互探索，生成 JSON 报告供 AI agent 消费。当用户提到"全站巡检""检查所有页面""系统体检""全面检查""巡检报告"时使用。
---

# 全站巡检

用 Playwright 无头浏览器并行检查 AiOS 所有前端页面（含侧边栏），生成 JSON 报告供 AI agent 消费。

路由表在每次运行前自动从各前端模块的 `router/index.js|ts` 扫描生成，新增或删除页面无需手工维护。

## 何时使用

- 大版本发布前的全面体检
- 定期质量巡检
- 新模块上线后验证全站没有被影响

## 运行方式

```bash
cd ~/.cursor/skills/全站巡检/scripts

# 全站检查（自动扫描路由）
PYTHONUNBUFFERED=1 python3 run.py

# 只查指定模块
python3 run.py -m 门户系统 -m 联系人

# 调整并行数（默认 4）
python3 run.py -w 6

# 列出自动扫描到的所有模块和页面数
python3 run.py --list-modules
```

报告输出到 `reports/` 子目录，每次运行自动清理旧报告只保留最新一份。

## 路由自动扫描

`route_scanner.py` 在每次巡检前解析 `/root/瑞小美AiOS/*/前端*/src/router/index.{js,ts}`：

- 提取 `createWebHistory(base)` 作为 URL 前缀
- 递归解析 `children` 嵌套路由，自动拼接父路径
- 自动过滤：动态参数 (`:id`) / 创建编辑页 / 登录 OAuth / 404 通配
- 侧边栏模块无 vue-router，在 `route_scanner.py` 中静态配置

新增前端模块时，在 `route_scanner.py` 的 `MODULE_SOURCES` 中加一行映射即可。

## 检查项（每个页面）

| 检查项 | 级别 | 说明 |
|--------|------|------|
| 白屏 | P0 | 页面无内容或极少可见元素 |
| 控制台 JS 错误 | P0 | 过滤了 Permissions-Policy、ResizeObserver 等环境噪音 |
| API 请求失败 | P0 | /api/ 路径的 4xx/5xx 响应 |
| 模拟数据残留 | P0 | 检测张三/李四/13800138000/placeholder/mock 等 |
| 空数据 + API 失败 | P0 | 空状态组件 + 后端返回错误 = 大概率 bug |
| 页面加载超时 | P0 | 超过 30s |
| 慢 API 请求 | P1 | API 响应超过 3s |
| 空数据（待确认） | P2 | 有表格但数据为空，非已知合理空页面 |
| 静态资源加载失败 | P2 | 非 API 的 4xx/5xx |

## 安全交互探索

自动对每个页面执行安全交互，暴露更多子视图：

- **Tab/分段器切换** — 点击所有 Tab
- **分页** — 翻到第 2 页再翻回来
- **折叠面板** — 展开折叠项
- **只读弹窗** — 点击「查看」「详情」按钮，截图后关闭，不提交

**绝不点击**：删除、禁用、确认、提交、审批、开关。

## 认证机制

生成两类 JWT Token 覆盖全站：

- **管理后台 Token**：`is_super` 超管权限，注入 `scrm_token` + `scrm_user`
- **侧边栏 Token**：`type: sidebar_user` 格式，注入 `scrm_sidebar_token` + `scrm_userid` + `scrm_username`

两类 Token 同时注入所有域名的 localStorage，无需按模块区分。

## 目录结构

```
全站巡检/
├── SKILL.md               # 本文件
├── scripts/
│   ├── run.py             # CLI 入口
│   ├── route_scanner.py   # 路由自动扫描（解析 Vue Router 文件）
│   ├── config.py          # 运行时常量（并行数、超时、选择器）
│   ├── auth.py            # 生成管理后台 + 侧边栏两种 JWT
│   ├── engine.py          # asyncio + 多 BrowserContext 并行
│   ├── checker.py         # 单页面检查逻辑
│   ├── reporter.py        # JSON 报告生成
│   └── requirements.txt   # playwright
└── reports/               # 只保留最新一份
    └── inspection_YYYYMMDD_HHMMSS/
        ├── report.json    # 仅含有问题的页面，按 P0→P2 排序
        └── screenshots/   # 截图 PNG
```

## 前置条件

- Docker 可用且 `portal-backend` 容器正在运行（生成 JWT 需要）
- 执行环境能访问各模块域名

## 依赖

- Python 3.11+
- playwright（含 Chromium）
- 系统库：atk, cups-libs, libdrm, mesa-libgbm, nss, pango, gtk3 等

首次安装：

```bash
pip3 install playwright
playwright install chromium
dnf install -y atk at-spi2-atk cups-libs libdrm mesa-libgbm libxkbcommon pango alsa-lib nss nspr libXcomposite libXdamage libXrandr libXtst libXfixes libXcursor libXScrnSaver libXi gtk3
```

## 已知限制

- 动态参数路由（`:id`）和写入页面（create/edit）自动跳过
- 侧边栏在非企微环境下可渲染 UI 但 JS-SDK 功能不可用
- 只检测 1920×1080 桌面视口
- 新增前端**模块**（非页面）需在 `route_scanner.py` 的 `MODULE_SOURCES` 加一行
