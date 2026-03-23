#!/usr/bin/env python3
"""
瑞小美 AiOS 全站巡检工具

使用 Playwright 多浏览器上下文并行检查所有页面。
每次运行前自动扫描前端 router 文件获取最新路由表。

用法:
    python run.py                     # 检查所有模块
    python run.py --module 门户系统     # 只检查指定模块
    python run.py --workers 6          # 使用 6 个并行 worker
    python run.py --module 门户系统 --module 联系人  # 检查多个模块
"""
import argparse
import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import PARALLEL_WORKERS
from route_scanner import scan_all_routes
from engine import run_inspection


def main():
    parser = argparse.ArgumentParser(description="瑞小美 AiOS 全站巡检工具")
    parser.add_argument(
        "--module", "-m",
        action="append",
        help="指定要检查的模块名称（可多次使用），不指定则检查全部",
    )
    parser.add_argument(
        "--workers", "-w",
        type=int,
        default=PARALLEL_WORKERS,
        help=f"并行 worker 数量（默认 {PARALLEL_WORKERS}）",
    )
    parser.add_argument(
        "--output", "-o",
        help="输出目录路径（默认自动按时间生成）",
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="列出所有可用模块",
    )
    args = parser.parse_args()

    print("[run] 扫描前端路由文件...")
    modules = scan_all_routes()

    if args.list_modules:
        print("\n可用模块:")
        for m in modules:
            print(f"  {m['name']:12s} — {len(m['routes']):3d} 个页面 ({m['base_url']})")
        return

    if args.module:
        module_names = set(args.module)
        filtered = [m for m in modules if m["name"] in module_names]
        not_found = module_names - {m["name"] for m in filtered}
        if not_found:
            print(f"未找到模块: {', '.join(not_found)}", file=sys.stderr)
            print(f"可用模块: {', '.join(m['name'] for m in modules)}", file=sys.stderr)
            sys.exit(1)
        modules = filtered

    t0 = time.time()
    results, report_path = asyncio.run(
        run_inspection(
            modules=modules,
            workers=args.workers,
            output_dir=args.output,
        )
    )
    elapsed = time.time() - t0
    print(f"\n总耗时: {elapsed:.1f}s")
    print(f"报告位置: {os.path.abspath(report_path)}")


if __name__ == "__main__":
    main()
