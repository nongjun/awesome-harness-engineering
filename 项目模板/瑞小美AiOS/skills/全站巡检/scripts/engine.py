"""
并行检查引擎

使用 asyncio + Playwright 多浏览器上下文并行检查所有页面。
每个 worker 拥有独立的 BrowserContext（独立的 localStorage、Cookie），
互不干扰。
"""
import asyncio
import os
import shutil
import time
from urllib.parse import urlparse

from playwright.async_api import async_playwright

from config import PARALLEL_WORKERS, VIEWPORT, PAGE_TIMEOUT
from auth import generate_token, generate_sidebar_token, build_user_json
from checker import check_page, PageResult, PageIssue
from reporter import generate_report


async def run_inspection(
    modules: list = None,
    workers: int = PARALLEL_WORKERS,
    output_dir: str = None,
):
    """执行全站巡检"""
    if modules is None:
        from route_scanner import scan_all_routes
        modules = scan_all_routes()
    skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    default_reports = os.path.join(skill_dir, "reports")

    if not output_dir:
        _cleanup_old_reports(default_reports)
        output_dir = os.path.join(default_reports, f"inspection_{time.strftime('%Y%m%d_%H%M%S')}")

    screenshot_dir = os.path.join(output_dir, "screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)

    print("[engine] 生成认证 Token...")
    token = generate_token(hours=4)
    sidebar_token = generate_sidebar_token(hours=4)
    user_json = build_user_json()
    print(f"[engine] 管理后台 Token (长度: {len(token)}), 侧边栏 Token (长度: {len(sidebar_token)})")

    # 构建任务队列
    tasks = []
    for module in modules:
        for route in module["routes"]:
            if route.get("skip_auth_check"):
                continue
            tasks.append({
                "module_name": module["name"],
                "base_url": module["base_url"],
                "route": route,
            })

    total = len(tasks)
    print(f"[engine] 共 {total} 个页面待检查，启动 {workers} 个并行 worker")

    queue = asyncio.Queue()
    for t in tasks:
        await queue.put(t)

    results: list[PageResult] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )

        done_count = 0

        async def worker(worker_id: int):
            nonlocal done_count
            context = await browser.new_context(
                viewport=VIEWPORT,
                ignore_https_errors=True,
                locale="zh-CN",
            )
            context.set_default_timeout(PAGE_TIMEOUT)

            domains_injected = set()
            domains_failed = set()

            while True:
                try:
                    task = queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

                base_url = task["base_url"]
                domain = urlparse(base_url).netloc

                if domain not in domains_injected and domain not in domains_failed:
                    try:
                        inject_page = await context.new_page()
                        await inject_page.goto(base_url, wait_until="commit", timeout=15000)
                        await inject_page.evaluate(
                            """([adminToken, sidebarToken, userJson]) => {
                                localStorage.setItem('scrm_token', adminToken);
                                localStorage.setItem('scrm_user', userJson);
                                localStorage.setItem('scrm_sidebar_token', sidebarToken);
                                var user = JSON.parse(userJson);
                                localStorage.setItem('scrm_userid', user.userid || '');
                                localStorage.setItem('scrm_username', user.name || '');
                            }""",
                            [token, sidebar_token, user_json],
                        )
                        await inject_page.close()
                        domains_injected.add(domain)
                    except Exception as e:
                        print(f"  [worker-{worker_id}] 注入 Token 到 {domain} 失败: {e}")
                        domains_failed.add(domain)

                done_count += 1
                print(
                    f"  [worker-{worker_id}] [{done_count}/{total}] "
                    f"{task['module_name']} - {task['route']['title']} "
                    f"({task['route']['path']})"
                )

                if domain in domains_failed:
                    page_result = PageResult(
                        module=task["module_name"],
                        path=task["route"]["path"],
                        title=task["route"].get("title", ""),
                        full_url=base_url.rstrip("/") + task["route"]["path"],
                        status="error",
                        issues=[],
                    )
                    page_result.issues.append(PageIssue("P0", "Token注入失败", f"域名 {domain} 的 Token 注入失败，跳过检查"))
                else:
                    page_result = await check_page(
                        context=context,
                        module_name=task["module_name"],
                        route=task["route"],
                        base_url=base_url,
                        screenshot_dir=screenshot_dir,
                    )

                results.append(page_result)

                queue.task_done()

            await context.close()

        # 启动所有 worker 并行执行
        worker_tasks = [
            asyncio.create_task(worker(i)) for i in range(workers)
        ]
        await asyncio.gather(*worker_tasks)
        await browser.close()

    print(f"\n[engine] 检查完成，共 {len(results)} 个页面")

    # 按模块排序
    module_order = {m["name"]: i for i, m in enumerate(modules)}
    results.sort(key=lambda r: (module_order.get(r.module, 99), r.path))

    report_path = generate_report(results, output_dir)
    print(f"[engine] 报告已生成: {report_path}")

    # 打印摘要
    _print_summary(results)

    return results, report_path


def _print_summary(results: list[PageResult]):
    """打印检查摘要"""
    total = len(results)
    ok = sum(1 for r in results if r.status == "ok" and not r.issues)
    has_issues = sum(1 for r in results if r.issues)
    errors = sum(1 for r in results if r.status in ("error", "timeout"))
    auth_fail = sum(1 for r in results if r.status == "redirect_login")

    all_issues = []
    for r in results:
        for issue in r.issues:
            all_issues.append(issue)

    p0 = sum(1 for i in all_issues if i.level == "P0")
    p1 = sum(1 for i in all_issues if i.level == "P1")
    p2 = sum(1 for i in all_issues if i.level == "P2")

    print(f"""
{'='*60}
  全站巡检摘要
{'='*60}
  总页面数:     {total}
  正常:         {ok}
  有问题:       {has_issues}
  加载失败:     {errors}
  认证失败:     {auth_fail}

  问题分布:
    P0 (严重):  {p0}
    P1 (重要):  {p1}
    P2 (优化):  {p2}
{'='*60}
""")

    if auth_fail > 0:
        print("  ⚠ 认证失败的页面:")
        for r in results:
            if r.status == "redirect_login":
                print(f"    - {r.module} / {r.title} ({r.path})")
        print()

    if p0 > 0:
        print("  ⚠ P0 严重问题:")
        for r in results:
            for issue in r.issues:
                if issue.level == "P0":
                    print(f"    - [{r.module}] {r.title}: {issue.category} - {issue.message}")
        print()


def _cleanup_old_reports(reports_dir: str):
    """删除所有旧报告目录，只保留即将生成的最新一份"""
    if not os.path.exists(reports_dir):
        return
    for name in os.listdir(reports_dir):
        path = os.path.join(reports_dir, name)
        if os.path.isdir(path) and name.startswith("inspection_"):
            shutil.rmtree(path, ignore_errors=True)
            print(f"[engine] 已清理旧报告: {name}")
