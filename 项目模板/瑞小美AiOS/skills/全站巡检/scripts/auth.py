"""
认证模块：通过 portal-backend 容器生成 JWT Token

生成两类 Token：
  - 管理后台 Token（sub/is_super 格式）
  - 侧边栏 Token（type=sidebar_user 格式）
"""
import subprocess
import json
import sys

SUPER_USER = {
    "userid": "NongJun-dreamer",
    "name": "农君",
    "is_super": True,
}

_UID = json.dumps(SUPER_USER["userid"])
_NAME = json.dumps(SUPER_USER["name"])


def _run_in_container(python_code: str) -> str:
    """在 portal-backend 容器中执行 Python 代码并返回 stdout"""
    cmd = ["docker", "exec", "portal-backend", "python3", "-c", python_code]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        print(f"[auth] 容器执行失败: {result.stderr}", file=sys.stderr)
        raise RuntimeError("容器执行失败，请确认 portal-backend 正在运行")
    output = result.stdout.strip()
    if not output or output.count(".") != 2:
        raise RuntimeError(f"生成的 Token 格式异常: {output[:50]}")
    return output


def generate_token(hours: int = 2) -> str:
    """生成管理后台超管 JWT"""
    code = f"""
import os, json
from jose import jwt
from datetime import datetime, timedelta
key = os.environ['JWT_SECRET_KEY']
print(jwt.encode({{
    'sub': {_UID},
    'name': {_NAME},
    'userid': {_UID},
    'is_super': True,
    'exp': datetime.utcnow() + timedelta(hours={hours})
}}, key, algorithm='HS256'))
"""
    return _run_in_container(code)


def generate_sidebar_token(hours: int = 4) -> str:
    """生成侧边栏专用 JWT（type=sidebar_user）"""
    code = f"""
import os, json
from jose import jwt
from datetime import datetime, timedelta, timezone
key = os.environ['JWT_SECRET_KEY']
now = datetime.now(timezone.utc)
print(jwt.encode({{
    'userid': {_UID},
    'name': {_NAME},
    'type': 'sidebar_user',
    'iat': now,
    'exp': now + timedelta(hours={hours})
}}, key, algorithm='HS256'))
"""
    return _run_in_container(code)


def build_user_json() -> str:
    return json.dumps(SUPER_USER)
