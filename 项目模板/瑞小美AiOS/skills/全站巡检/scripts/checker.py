"""
页面检查器：对单个页面执行完整检查流程

检查项：
1. 页面加载与渲染（domcontentloaded + SPA 就绪检测，避免 networkidle 对 WebSocket/轮询页面的误超时）
2. 全页截图
3. 控制台错误（过滤环境噪音）
4. 网络请求错误（4xx/5xx，排除静态资源噪音）
5. 慢请求分析（区分首屏和后续请求）
6. 关键元素存在性统计
7. 空数据智能判断（区分合理空 vs 异常空）
8. 安全交互探索（Tab/分页/搜索/筛选/弹窗）
9. 交互后截图
"""
import asyncio
import time
from dataclasses import dataclass, field
from playwright.async_api import Page, BrowserContext

from config import (
    SETTLE_WAIT, SAFE_CLICK_SELECTORS, PAGE_TIMEOUT
)

NOISE_PATTERNS = [
    "Permissions-Policy",
    "CursorBrowser",
    "favicon.ico",
    "third-party cookie",
    "DevTools",
    "Download the Vue Devtools",
    "net::ERR_BLOCKED_BY_CLIENT",
    "ResizeObserver loop",
]

NOISE_URL_PATTERNS = [
    "favicon", "hot-update", ".map", "sockjs-node",
    "livereload", "__webpack_hmr", "browser-sync",
]

LEGITIMATE_EMPTY_PATHS = [
    "recycle-bin", "system-logs", "ai-logs", "ai-usage",
    "scheduled-jobs", "assistants",
    "risk/", "timeout/", "audit-logs",
    "analysis/", "group-stats", "lifecycle",
    "organization/", "customer/friends", "customer/duplicates",
    "customer/employee-analysis",
    "sessions/tracks", "sessions/voice-calls", "sessions/export",
    "outreach/", "blacklist",
    "statistics", "stats",
    "monitoring/config", "visit/config", "quality/config",
]


@dataclass
class PageIssue:
    level: str  # P0 / P1 / P2
    category: str
    message: str


@dataclass
class NetworkEntry:
    url: str
    method: str
    status: int
    duration_ms: float
    is_api: bool = False


@dataclass
class PageResult:
    module: str
    path: str
    title: str
    full_url: str
    screenshot_path: str = ""
    interaction_screenshots: list = field(default_factory=list)
    load_time_ms: float = 0
    console_errors: list = field(default_factory=list)
    console_warnings: list = field(default_factory=list)
    network_errors: list = field(default_factory=list)
    slow_requests: list = field(default_factory=list)
    issues: list = field(default_factory=list)
    is_blank: bool = False
    has_mock_data: bool = False
    element_counts: dict = field(default_factory=dict)
    status: str = "ok"  # ok / error / timeout / redirect_login


def _is_noise(msg: str) -> bool:
    return any(p.lower() in msg.lower() for p in NOISE_PATTERNS)


def _is_noise_url(url: str) -> bool:
    return any(p in url.lower() for p in NOISE_URL_PATTERNS)


def _is_api_url(url: str) -> bool:
    return "/api/" in url


def _is_legitimate_empty(path: str) -> bool:
    return any(p in path for p in LEGITIMATE_EMPTY_PATHS)


async def _wait_for_spa_ready(page: Page, timeout_ms: int = 10000):
    """等待 Vue SPA 渲染完成：检测 #app 下有实质子元素，或超时退出"""
    try:
        await page.wait_for_function("""
            () => {
                const app = document.querySelector('#app');
                if (!app) return false;
                return app.querySelectorAll('div, section, main, nav, table, form').length > 2;
            }
        """, timeout=timeout_ms)
    except Exception:
        pass


async def check_page(
    context: BrowserContext,
    module_name: str,
    route: dict,
    base_url: str,
    screenshot_dir: str,
) -> PageResult:
    """对单个页面执行完整检查"""
    full_url = base_url.rstrip("/") + route["path"]
    result = PageResult(
        module=module_name,
        path=route["path"],
        title=route.get("title", ""),
        full_url=full_url,
    )

    page = await context.new_page()
    console_messages = []
    network_entries = []

    page.on("console", lambda msg: console_messages.append({
        "type": msg.type, "text": msg.text
    }))

    request_timings = {}

    def on_request(req):
        request_timings[req] = time.time()

    def on_response(resp):
        start = request_timings.pop(resp.request, time.time())
        duration = (time.time() - start) * 1000
        network_entries.append(NetworkEntry(
            url=resp.url, method=resp.request.method,
            status=resp.status, duration_ms=round(duration, 1),
            is_api=_is_api_url(resp.url),
        ))

    page.on("request", on_request)
    page.on("response", on_response)

    try:
        t0 = time.time()
        # 用 domcontentloaded 代替 networkidle，避免 WebSocket/轮询页面永不 idle
        await page.goto(full_url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT)
        # 等待 SPA 组件渲染
        await _wait_for_spa_ready(page, timeout_ms=8000)
        # 额外等待异步数据加载
        await asyncio.sleep(SETTLE_WAIT)
        result.load_time_ms = round((time.time() - t0) * 1000, 1)

        current_url = page.url
        if "/login" in current_url and not route.get("skip_auth_check"):
            result.status = "redirect_login"
            result.issues.append(PageIssue("P0", "认证", f"页面被重定向到登录页: {current_url}"))
            await page.close()
            return result

        safe_name = f"{module_name}_{route['path'].strip('/').replace('/', '_') or 'index'}"
        screenshot_path = f"{screenshot_dir}/{safe_name}.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        result.screenshot_path = screenshot_path

        # 白屏检测
        body_text = await page.evaluate("document.body?.innerText?.trim() || ''")
        visible_elements = await page.evaluate("""
            () => {
                const els = document.querySelectorAll('div, table, form, ul, ol, section, article, main, nav');
                let visible = 0;
                els.forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) visible++;
                });
                return visible;
            }
        """)
        if not body_text and visible_elements < 3:
            result.is_blank = True
            result.issues.append(PageIssue("P0", "白屏", "页面内容为空或仅有极少可见元素"))

        # 元素统计
        result.element_counts = await page.evaluate("""
            () => ({
                buttons: document.querySelectorAll('button, .el-button').length,
                inputs: document.querySelectorAll('input, textarea, .el-input').length,
                tables: document.querySelectorAll('table, .el-table').length,
                forms: document.querySelectorAll('form, .el-form').length,
                tabs: document.querySelectorAll('.el-tabs__item, [role="tab"]').length,
                links: document.querySelectorAll('a[href]').length,
                dialogs: document.querySelectorAll('.el-dialog, .el-drawer').length,
                cards: document.querySelectorAll('.el-card').length,
                emptyTexts: document.querySelectorAll('.el-empty, .el-table__empty-text').length,
            })
        """)

        # 模拟数据检测
        mock_indicators = await page.evaluate("""
            () => {
                const text = document.body?.innerText || '';
                const patterns = ['张三', '李四', '王五', '13800138000', 'Lorem ipsum',
                                  'test@test.com', 'placeholder', 'mock'];
                return patterns.filter(p => text.toLowerCase().includes(p.toLowerCase()));
            }
        """)
        if mock_indicators:
            result.has_mock_data = True
            result.issues.append(PageIssue(
                "P0", "模拟数据", f"检测到疑似模拟数据: {', '.join(mock_indicators)}"
            ))

        # 空数据智能判断
        empty_count = result.element_counts.get("emptyTexts", 0)
        if empty_count > 0:
            has_table = result.element_counts.get("tables", 0) > 0
            has_failed_api = any(
                e.is_api and e.status >= 400 for e in network_entries
            )
            is_expected_empty = _is_legitimate_empty(route["path"])

            if has_failed_api:
                result.issues.append(PageIssue(
                    "P0", "空数据（API失败）",
                    f"{empty_count} 个空状态 + API 请求失败，大概率是后端异常"
                ))
            elif has_table and not is_expected_empty:
                result.issues.append(PageIssue(
                    "P2", "空数据（待确认）",
                    f"表格显示空状态，可能是数据确实为空，也可能是加载异常"
                ))
            # 合理空（如回收站）不报问题

        # 控制台消息分类
        for msg in console_messages:
            if _is_noise(msg["text"]):
                continue
            if msg["type"] == "error":
                result.console_errors.append(msg["text"][:300])
            elif msg["type"] == "warning":
                result.console_warnings.append(msg["text"][:300])

        if result.console_errors:
            result.issues.append(PageIssue(
                "P0", "控制台错误",
                f"{len(result.console_errors)} 个 JS 错误"
            ))

        # 网络请求分析
        for entry in network_entries:
            if _is_noise_url(entry.url):
                continue
            if entry.status >= 400:
                result.network_errors.append(entry)
            if entry.is_api and entry.duration_ms > 3000:
                result.slow_requests.append(entry)

        if result.network_errors:
            api_errors = [e for e in result.network_errors if e.is_api]
            static_errors = [e for e in result.network_errors if not e.is_api]
            if api_errors:
                result.issues.append(PageIssue(
                    "P0", "API请求失败",
                    f"{len(api_errors)} 个 API 请求返回错误"
                ))
            if static_errors:
                result.issues.append(PageIssue(
                    "P2", "静态资源加载失败",
                    f"{len(static_errors)} 个静态资源加载失败"
                ))
        if result.slow_requests:
            result.issues.append(PageIssue(
                "P1", "慢请求",
                f"{len(result.slow_requests)} 个 API 请求超过 3s"
            ))

        # 安全交互探索
        result.interaction_screenshots = await _explore_interactions(
            page, safe_name, screenshot_dir
        )

    except Exception as e:
        error_msg = str(e)
        if "timeout" in error_msg.lower():
            result.status = "timeout"
            result.issues.append(PageIssue("P0", "超时", f"页面加载超时 ({PAGE_TIMEOUT}ms)"))
        else:
            result.status = "error"
            result.issues.append(PageIssue("P0", "异常", error_msg[:300]))
    finally:
        try:
            await page.close()
        except Exception:
            pass

    return result


async def _explore_interactions(
    page: Page, safe_name: str, screenshot_dir: str
) -> list:
    """安全交互探索：Tab/分页/搜索/筛选/弹窗"""
    screenshots = []

    for idx, selector in enumerate(SAFE_CLICK_SELECTORS):
        try:
            elements = await page.query_selector_all(selector)
            if not elements:
                continue

            clicked = set()
            for i, el in enumerate(elements[:5]):
                text = (await el.text_content() or "").strip()[:20]
                if text in clicked:
                    continue
                clicked.add(text)

                if not await el.is_visible():
                    continue

                try:
                    await el.click(timeout=3000)
                    await asyncio.sleep(1)

                    shot_path = f"{screenshot_dir}/{safe_name}_interact_{idx}_{i}.png"
                    await page.screenshot(path=shot_path, full_page=True)
                    screenshots.append({
                        "path": shot_path,
                        "action": f"点击 {selector} - '{text}'",
                    })
                except Exception:
                    pass
        except Exception:
            pass

    # 分页探索：如果有分页器且不止一页，点第二页
    try:
        pager_btn = page.locator('.el-pager .number').nth(1)
        if await pager_btn.count() > 0 and await pager_btn.is_visible():
            await pager_btn.click(timeout=3000)
            await asyncio.sleep(1.5)
            shot_path = f"{screenshot_dir}/{safe_name}_page2.png"
            await page.screenshot(path=shot_path, full_page=True)
            screenshots.append({"path": shot_path, "action": "翻到第 2 页"})
            first_page = page.locator('.el-pager .number').first
            if await first_page.count() > 0:
                await first_page.click(timeout=2000)
                await asyncio.sleep(0.5)
    except Exception:
        pass

    # 弹窗探索：只看不提交
    for btn_text in ["查看", "详情"]:
        try:
            btn = page.locator(f'button:has-text("{btn_text}")').first
            if await btn.count() > 0 and await btn.is_visible():
                await btn.click(timeout=3000)
                await asyncio.sleep(1.5)

                shot_path = f"{screenshot_dir}/{safe_name}_dialog_{btn_text}.png"
                await page.screenshot(path=shot_path, full_page=True)
                screenshots.append({
                    "path": shot_path,
                    "action": f"打开 {btn_text} 弹窗",
                })

                close_btn = page.locator('.el-dialog__headerbtn, .el-drawer__close-btn').first
                if await close_btn.count() > 0:
                    await close_btn.click(timeout=2000)
                    await asyncio.sleep(0.5)
        except Exception:
            pass

    return screenshots
