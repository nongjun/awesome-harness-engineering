"""
路由自动扫描器

从各前端模块的 Vue Router 配置文件中自动提取路由表。
每次巡检前执行，确保路由覆盖与代码实时同步。

解析策略：
  1. 找到 routes 数组 → 用括号计数拆分顶层路由对象
  2. 递归处理 children 嵌套，拼接父路径
  3. 提取 createWebHistory(base) 作为 URL 前缀
  4. 过滤：动态参数 / create|edit / login|oauth / pathMatch 通配
"""
import os
import re

AIOS_ROOT = "/root/瑞小美AiOS"

MODULE_SOURCES = [
    {"name": "门户系统", "base_url": "https://scrm.ireborn.com.cn",
     "router_path": "门户系统/前端/src/router/index.js"},
    {"name": "联系人", "base_url": "https://scrm.ireborn.com.cn",
     "router_path": "联系人/前端-管理后台/src/router/index.js"},
    {"name": "内容中心", "base_url": "https://scrm.ireborn.com.cn",
     "router_path": "内容中心/前端-管理后台/src/router/index.js"},
    {"name": "企微托管", "base_url": "https://scrm.ireborn.com.cn",
     "router_path": "企微托管/前端-管理后台/src/router/index.ts"},
    {"name": "朋友圈", "base_url": "https://moment.ireborn.com.cn",
     "router_path": "朋友圈/前端-管理后台/src/router/index.js"},
    {"name": "会话存档", "base_url": "https://archive.ireborn.com.cn",
     "router_path": "会话存档/前端应用/src/router/index.ts"},
    {"name": "对话质检", "base_url": "https://quality.ireborn.com.cn",
     "router_path": "对话质检/前端应用/src/router/index.ts"},
]

SIDEBAR_MODULES = [
    {
        "name": "联系人侧边栏",
        "base_url": "https://contact.ireborn.com.cn",
        "auth_type": "sidebar",
        "routes": [{"path": "/sidebar/contact/", "title": "客户概况"}],
    },
    {
        "name": "内容中心侧边栏",
        "base_url": "https://scrm.ireborn.com.cn",
        "auth_type": "sidebar",
        "routes": [{"path": "/sidebar/content/", "title": "话术素材侧边栏"}],
    },
    {
        "name": "企微托管侧边栏",
        "base_url": "https://scrm.ireborn.com.cn",
        "auth_type": "none",
        "routes": [{"path": "/sidebar", "title": "智能回复侧边栏"}],
    },
]

_SKIP_DYNAMIC = re.compile(r":[\w]+")
_SKIP_REGEX = re.compile(r"\(.*\)")
_SKIP_KEYWORDS = {"create", "edit", "wizard", "login", "oauth"}


def _should_skip(path: str) -> bool:
    if "pathMatch" in path:
        return True
    if _SKIP_DYNAMIC.search(path) or _SKIP_REGEX.search(path):
        return True
    parts = set(path.lower().strip("/").split("/"))
    return bool(parts & _SKIP_KEYWORDS)


def _extract_objects(text: str) -> list[str]:
    """从 JS 数组中按大括号计数提取顶层对象"""
    objects = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objects.append(text[start : i + 1])
                start = None
    return objects


def _find_bracket_end(text: str, open_pos: int, open_char: str = "[", close_char: str = "]") -> int:
    """从 open_pos 开始找匹配的闭合括号位置"""
    depth = 0
    for i in range(open_pos, len(text)):
        if text[i] == open_char:
            depth += 1
        elif text[i] == close_char:
            depth -= 1
            if depth == 0:
                return i + 1
    return len(text)


def _strip_children(text: str) -> str:
    """移除路由对象中的 children: [...] 部分，只保留自身属性"""
    match = re.search(r"children:\s*\[", text)
    if not match:
        return text
    end = _find_bracket_end(text, match.end() - 1)
    return text[: match.start()] + text[end:]


def _parse_route(text: str, parent_path: str = "") -> list[dict]:
    """递归解析单个路由对象，返回有效路由列表"""
    routes = []

    path_match = re.search(r"path:\s*['\"]([^'\"]*)['\"]", text)
    if not path_match:
        return routes
    raw = path_match.group(1)

    if raw.startswith("/"):
        full = raw
    elif raw == "":
        full = parent_path or "/"
    else:
        full = parent_path.rstrip("/") + "/" + raw
    full = re.sub(r"/+", "/", full) or "/"

    children_match = re.search(r"children:\s*\[", text)
    if children_match:
        arr_start = children_match.end() - 1
        arr_end = _find_bracket_end(text, arr_start)
        for child in _extract_objects(text[arr_start:arr_end]):
            routes.extend(_parse_route(child, full))

    own = _strip_children(text)
    has_component = bool(re.search(r"component\s*:", own))
    has_redirect = bool(re.search(r"redirect\s*:", own))
    skip_auth = bool(re.search(r"(skipAuth|noAuth|public)\s*:\s*true", own))
    title_m = re.search(r"title:\s*['\"]([^'\"]*)['\"]", own)
    title = title_m.group(1) if title_m else ""

    if has_component and not has_redirect and title and not skip_auth and not _should_skip(full):
        routes.append({"path": full, "title": title})

    return routes


def _scan_file(filepath: str) -> tuple[str, list[dict]]:
    """解析单个 Vue Router 文件"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    base_match = re.search(r"createWebHistory\(\s*['\"]([^'\"]+)['\"]", content)
    base_path = base_match.group(1).rstrip("/") if base_match else ""

    routes_match = re.search(r"(?:const\s+)?routes\s*(?::\s*\w+(?:\[\])?)?\s*=\s*\[", content)
    if not routes_match:
        return base_path, []

    arr_start = routes_match.end() - 1
    arr_end = _find_bracket_end(content, arr_start)

    all_routes = []
    for obj in _extract_objects(content[arr_start:arr_end]):
        all_routes.extend(_parse_route(obj))

    if base_path:
        for r in all_routes:
            if not r["path"].startswith(base_path):
                r["path"] = base_path + r["path"]

    seen = set()
    unique = []
    for r in all_routes:
        if r["path"] not in seen:
            seen.add(r["path"])
            unique.append(r)

    return base_path, unique


def scan_all_routes() -> list[dict]:
    """扫描所有前端模块的 router 文件，返回完整的 MODULES 列表"""
    modules = []

    for src in MODULE_SOURCES:
        filepath = os.path.join(AIOS_ROOT, src["router_path"])
        if not os.path.exists(filepath):
            print(f"[scanner] 路由文件不存在: {src['name']} ({filepath})")
            modules.append({"name": src["name"], "base_url": src["base_url"], "auth_type": "admin", "routes": []})
            continue

        try:
            base_path, routes = _scan_file(filepath)
            print(f"[scanner] {src['name']}: {len(routes)} 个页面 (base={base_path or '/'})")
            modules.append({
                "name": src["name"],
                "base_url": src["base_url"],
                "auth_type": src.get("auth_type", "admin"),
                "routes": routes,
            })
        except Exception as e:
            print(f"[scanner] 解析失败: {src['name']} - {e}")
            modules.append({"name": src["name"], "base_url": src["base_url"], "auth_type": "admin", "routes": []})

    modules.extend(SIDEBAR_MODULES)

    total = sum(len(m["routes"]) for m in modules)
    print(f"[scanner] 侧边栏: {sum(len(m['routes']) for m in SIDEBAR_MODULES)} 个页面（静态配置）")
    print(f"[scanner] 总计: {total} 个页面")

    return modules
