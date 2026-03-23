"""
巡检报告生成器

输出 report.json 供 AI agent 消费：
  - 仅含有问题的页面，按 P0→P2 排序
  - 控制台错误、网络请求 URL 不截断
  - 不含截图（agent 无法消费图片）
"""
import json
import os
import time

from checker import PageResult


def generate_report(results: list[PageResult], output_dir: str) -> str:
    """生成 JSON 报告，返回报告文件路径。"""
    LEVEL_PRIORITY = {"P0": 0, "P1": 1, "P2": 2}

    all_issues_flat = []
    for r in results:
        if not r.issues and r.status == "ok":
            continue

        page_issues = []
        for issue in r.issues:
            page_issues.append({
                "level": issue.level,
                "category": issue.category,
                "message": issue.message,
            })

        entry = {
            "module": r.module,
            "title": r.title,
            "path": r.path,
            "full_url": r.full_url,
            "status": r.status,
            "load_time_ms": r.load_time_ms,
            "issues": page_issues,
            "console_errors": r.console_errors,
            "network_errors": [
                {"url": e.url, "method": e.method, "status": e.status, "duration_ms": e.duration_ms}
                for e in r.network_errors
            ],
            "slow_requests": [
                {"url": e.url, "method": e.method, "status": e.status, "duration_ms": e.duration_ms}
                for e in r.slow_requests
            ],
        }

        max_level = min(
            (LEVEL_PRIORITY.get(i.level, 99) for i in r.issues),
            default=99,
        )
        all_issues_flat.append((max_level, entry))

    all_issues_flat.sort(key=lambda x: x[0])

    total = len(results)
    all_issue_objs = [i for r in results for i in r.issues]

    report = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": {
            "total_pages": total,
            "ok": sum(1 for r in results if r.status == "ok" and not r.issues),
            "with_issues": sum(1 for r in results if r.issues or r.status != "ok"),
            "p0": sum(1 for i in all_issue_objs if i.level == "P0"),
            "p1": sum(1 for i in all_issue_objs if i.level == "P1"),
            "p2": sum(1 for i in all_issue_objs if i.level == "P2"),
            "auth_fail": sum(1 for r in results if r.status == "redirect_login"),
        },
        "pages_with_issues": [entry for _, entry in all_issues_flat],
    }

    json_path = os.path.join(output_dir, "report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    return json_path
