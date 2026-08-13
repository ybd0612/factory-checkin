#!/usr/bin/env python3
"""New API 站点每日自动签到脚本（零依赖，Python 3.8+）

适用于所有开启「签到奖励」功能的 New API（https://github.com/QuantumNous/new-api）站点。

通过环境变量配置：
  NEWAPI_TOKEN     必填。站点后台「个人设置 -> 安全设置」生成的访问令牌
  NEWAPI_USER_ID   必填。数字用户 ID（浏览器 F12 -> Application -> Local Storage -> user -> id）
  NEWAPI_BASE_URL  可选。站点地址，默认 https://factory.pub

退出码：
  0 = 签到成功或今日已签到
  1 = 签到/查询失败
  2 = 配置缺失
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

# 避免 Windows 控制台（GBK）输出中文乱码
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

BASE_URL = (os.environ.get("NEWAPI_BASE_URL") or "https://factory.pub").rstrip("/")
TOKEN = os.environ.get("NEWAPI_TOKEN", "").strip()
USER_ID = os.environ.get("NEWAPI_USER_ID", "").strip()

MAX_RETRIES = 3
QUOTA_PER_DOLLAR = 500000  # New API 默认 500000 配额 = $1


def build_headers():
    return {
        "Authorization": f"Bearer {TOKEN}",
        "New-Api-User": USER_ID,
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 (newapi-checkin)",
    }


def request(method, path, payload=None):
    """发送请求并解析 JSON 响应。"""
    url = f"{BASE_URL}{path}"
    headers = build_headers()
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["X-Requested-With"] = "XMLHttpRequest"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def with_retries(name, fn):
    """失败自动重试；认证类错误（401/403）不重试直接抛出。"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn()
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:300]
            print(f"[{name}] HTTP {e.code}: {detail}")
            if e.code in (401, 403):
                raise
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] 请求失败: {e}")
        if attempt < MAX_RETRIES:
            wait = attempt * 5
            print(f"[{name}] {wait}s 后第 {attempt} 次重试...")
            time.sleep(wait)
    raise RuntimeError(f"{name}在 {MAX_RETRIES} 次尝试后仍然失败")


def quota_display(quota):
    return round((quota or 0) / QUOTA_PER_DOLLAR, 4)


def get_status():
    month = datetime.now().strftime("%Y-%m")
    return with_retries("查询签到状态", lambda: request("GET", f"/api/user/checkin?month={month}"))


def do_checkin():
    return with_retries("执行签到", lambda: request("POST", "/api/user/checkin", payload={}))


def main():
    print(f"站点: {BASE_URL}")
    print(f"用户: {USER_ID or '(未配置)'}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if not TOKEN or not USER_ID:
        print("错误: 请配置环境变量 NEWAPI_TOKEN 和 NEWAPI_USER_ID（详见 README）")
        return 2

    try:
        status = get_status()
    except Exception as e:  # noqa: BLE001
        print(f"查询签到状态失败: {e}")
        return 1

    if not status.get("success"):
        print(f"查询签到状态失败: {status.get('message', '未知错误')}")
        return 1

    data = status.get("data", {})
    stats = data.get("stats", {})

    if not data.get("enabled"):
        print("该站点未开启签到功能，无需操作")
        return 0

    if stats.get("checked_in_today"):
        print(
            f"今日已签到，无需重复。当前连签 {stats.get('checkin_count', 0)} 天，"
            f"累计获得 ${quota_display(stats.get('total_quota'))}"
        )
        return 0

    try:
        result = do_checkin()
    except Exception as e:  # noqa: BLE001
        print(f"签到失败: {e}")
        return 1

    if not result.get("success"):
        print(f"签到失败: {result.get('message', '未知错误')}")
        return 1

    awarded = result.get("data", {})
    print(
        f"签到成功！日期: {awarded.get('checkin_date', '今日')}，"
        f"获得 ${quota_display(awarded.get('quota_awarded'))} 额度，"
        f"当前连签 {stats.get('checkin_count', 0) + 1} 天"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
