"""
全站巡检运行时配置

路由表由 route_scanner.py 在每次巡检前从前端 router 文件自动扫描生成，
此文件只保留与扫描无关的运行时常量。
"""

PARALLEL_WORKERS = 4

PAGE_TIMEOUT = 30000

SETTLE_WAIT = 3

VIEWPORT = {"width": 1920, "height": 1080}

SAFE_CLICK_SELECTORS = [
    ".el-tabs__item",
    ".el-radio-button",
    ".el-segmented-item",
    '[role="tab"]',
    ".el-collapse-item__header",
    ".el-table__expand-icon",
]

