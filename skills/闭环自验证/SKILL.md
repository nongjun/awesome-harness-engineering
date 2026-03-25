---
name: 闭环自验证
description: Agent 闭环自验证工作流，在完成代码修改后自动执行"构建→静态检查→UI验证→日志检查→结果判定"的完整循环。当 Agent 完成功能开发、Bug 修复、UI 修改、API 变更或任何代码改动后，应主动触发此验证流程。适用于 Web 前后端项目的闭环验证。
---

# 闭环自验证 SOP

## 验证循环

```
写代码 → 构建/部署 → 静态检查 → UI 验证 → 系统验证 → 判定
                                                       ↓
                                              失败 → 修复 → 回到构建（最多 3 轮）
```

## Step 1: 构建与部署

```bash
docker compose build <service-name>
docker compose up -d <service-name>
docker logs <container-name> --tail 30
docker ps --filter "name=<container-name>" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

**通过标准**：容器 `Up`，无 `Restarting`，日志无 Error/Exception。

## Step 2: 静态检查

使用 ReadLints 工具检查已编辑文件。TypeScript 项目额外执行 `npx tsc --noEmit`。

**通过标准**：无新增 linter/类型错误。

## Step 3: UI 验证

对前端变更，使用浏览器 MCP 工具：

1. `browser_navigate` → 目标 URL，等待渲染
2. `browser_snapshot` → 检查 DOM 结构和交互元素
3. `browser_click` / `browser_fill` → 模拟用户操作，`snapshot(includeDiff: true)` 对比变化
4. `browser_console_messages` → 检查 JS 错误
5. `browser_network_requests` → 检查 API 请求（无 4xx/5xx）
6. `browser_take_screenshot(fullPage: true)` → 视觉确认

**通过标准**：目标元素存在可见、控制台无 error、网络请求全部成功、交互行为符合预期。

## Step 4: 系统验证

```bash
# API 可达性 + 响应时间
curl -s -o /dev/null -w "%{http_code} %{time_total}s" https://<domain>/api/health

# 容器资源
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" <container-name>
```

**通过标准**：无 error/exception 日志、API 返回 2xx、响应时间 <2s、资源无异常飙升。

## Step 5: 结果判定

- **全部通过** → 列出已验证检查点，附关键截图（如有 UI 变更），标记完成
- **发现问题** → 定位修复 → 从 Step 1 重新验证，最多 3 轮后向用户报告

## 验证深度选择

| 变更类型 | 构建 | 静态检查 | UI 验证 | 系统验证 |
|---------|------|---------|--------|---------|
| 前端 UI | ✅ | ✅ | ✅ 完整 | ⚡ 轻量 |
| 后端 API | ✅ | ✅ | ⚡ 轻量 | ✅ 完整 |
| 全栈变更 | ✅ | ✅ | ✅ 完整 | ✅ 完整 |
| 配置变更 | ✅ | — | ⚡ 轻量 | ✅ 完整 |
| 样式微调 | ✅ | ✅ | ✅ 截图 | — |

⚡ 轻量 = 健康检查 + 控制台无错误
