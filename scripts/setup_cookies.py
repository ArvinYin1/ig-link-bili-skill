#!/usr/bin/env python3
"""
ig-link-bili: 一键提取本机浏览器的 B 站 cookie 写入 credentials.json

用法：
  python3 scripts/setup_cookies.py                 # 自动探测已登录 B 站的浏览器
  python3 scripts/setup_cookies.py --browser chrome # 指定浏览器
  python3 scripts/setup_cookies.py --list          # 列出支持的浏览器
  python3 scripts/setup_cookies.py --no-verify     # 跳过 isLogin 验真（默认验）

做什么：
  从本机浏览器的当前会话里抓 SESSDATA + bili_jct + buvid3 三件套（必须同一浏览器、
  同一会话——B 站按设备指纹绑定，混着取必返 -101），写入
  ../bilibili_uploader/credentials.json，然后调 nav API 验 isLogin。

前提（人来做的两件事，脚本替不了）：
  1. 先在该浏览器里登录 bilibili.com（不要隐身/无痕模式）
  2. macOS 上 Chromium 系（chrome/edge/brave/arc/vivaldi/opera）解密 cookie 会弹
     钥匙串密码框，需要批准一次；Firefox/LibreWolf 不走钥匙串、不弹框。

铁律：cookie 是「你自己账号 + 这台设备」专属的，不能拷给别人用。
"""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

CRED_PATH = Path(__file__).resolve().parent.parent / "bilibili_uploader" / "credentials.json"
NAV_API = "https://api.bilibili.com/x/web-interface/nav"

# 自动探测时的尝试顺序（常见在前）
AUTO_ORDER = [
    "chrome", "arc", "edge", "brave", "vivaldi", "chromium",
    "opera", "opera_gx", "firefox", "librewolf", "safari",
]


def available_browsers(bc):
    """该 browser_cookie3 版本实际提供的浏览器函数。"""
    return [n for n in AUTO_ORDER if hasattr(bc, n) and callable(getattr(bc, n))]


def extract_from(bc, browser):
    """从单个浏览器抓三件套（同一会话）。返回 dict 或抛异常。"""
    jar = getattr(bc, browser)(domain_name="bilibili.com")
    found = {"sessdata": "", "bili_jct": "", "buvid3": ""}
    for c in jar:
        if c.name == "SESSDATA":
            found["sessdata"] = c.value
        elif c.name == "bili_jct":
            found["bili_jct"] = c.value
        elif c.name == "buvid3":
            found["buvid3"] = c.value
    return found


def verify(creds, timeout=10):
    """调 nav API 验登录态。返回 (is_login, uname, raw_code)。网络失败抛异常。"""
    cookie = f"SESSDATA={creds['sessdata']}; bili_jct={creds['bili_jct']}; buvid3={creds['buvid3']}"
    req = urllib.request.Request(
        NAV_API,
        headers={
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.bilibili.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    d = data.get("data", {}) or {}
    return bool(d.get("isLogin")), d.get("uname", ""), data.get("code")


def write_creds(creds):
    payload = {
        "sessdata": creds["sessdata"],
        "bili_jct": creds["bili_jct"],
        "buvid3": creds["buvid3"],
        "comment": "由 setup_cookies.py 从本机浏览器自动写入；切勿拷给他人（设备指纹绑定）",
    }
    CRED_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="提取浏览器 B 站 cookie 写入 credentials.json")
    ap.add_argument("--browser", default="auto",
                    help="浏览器名（chrome/edge/brave/arc/vivaldi/chromium/opera/opera_gx/firefox/librewolf/safari），默认 auto 自动探测")
    ap.add_argument("--list", action="store_true", help="列出本机支持的浏览器后退出")
    ap.add_argument("--no-verify", action="store_true", help="跳过 isLogin 验真")
    args = ap.parse_args()

    try:
        import browser_cookie3 as bc
    except ImportError:
        print("✗ 未安装 browser_cookie3。先跑：pip install browser_cookie3", file=sys.stderr)
        sys.exit(3)

    avail = available_browsers(bc)
    if args.list:
        print("本机支持的浏览器：", ", ".join(avail))
        return

    # 确定要尝试的浏览器列表
    if args.browser == "auto":
        candidates = avail
        print(f"自动探测中（按顺序尝试）：{', '.join(candidates)}")
    else:
        if not hasattr(bc, args.browser):
            print(f"✗ 不支持的浏览器 '{args.browser}'。支持：{', '.join(avail)}", file=sys.stderr)
            sys.exit(2)
        candidates = [args.browser]

    last_err = None
    for browser in candidates:
        try:
            creds = extract_from(bc, browser)
        except Exception as e:  # noqa: BLE001 — 不同浏览器抛各种异常（没装/库锁/钥匙串拒绝）
            last_err = f"{browser}: {e}"
            if args.browser != "auto":
                print(f"✗ 从 {browser} 提取失败：{e}", file=sys.stderr)
                print("  常见原因：① 没在该浏览器登录 B 站 ② 钥匙串没解锁/被拒 ③ 浏览器没装", file=sys.stderr)
                sys.exit(4)
            continue

        if not creds["sessdata"]:
            last_err = f"{browser}: 没找到 SESSDATA（该浏览器没登录 B 站？）"
            if args.browser != "auto":
                print(f"✗ {browser} 里没有 SESSDATA——请先在该浏览器登录 bilibili.com", file=sys.stderr)
                sys.exit(5)
            continue

        # 抓到了 SESSDATA。验真（除非 --no-verify）
        if args.no_verify:
            write_creds(creds)
            print(f"✓ 已从 {browser} 写入 credentials.json（未验真）")
            print(f"  路径：{CRED_PATH}")
            return

        try:
            is_login, uname, code = verify(creds)
        except Exception as e:  # noqa: BLE001 — 网络问题不该吞掉已抓到的 cookie
            write_creds(creds)
            print(f"⚠ 已从 {browser} 写入 credentials.json，但验真请求失败：{e}")
            print(f"  路径：{CRED_PATH}")
            print("  请手动验：curl -s 'https://api.bilibili.com/x/web-interface/nav' -b \"SESSDATA=...\" 看 isLogin")
            return

        if is_login:
            write_creds(creds)
            print(f"✓ 成功！从 {browser} 提取并验真：isLogin=True，@{uname}")
            print(f"  已写入：{CRED_PATH}")
            return

        # 抓到 SESSDATA 但 isLogin=False（字段不配套/过期）
        last_err = f"{browser}: isLogin=False (code={code})——三件套可能不配套或已过期"
        if args.browser != "auto":
            print(f"✗ {browser} 的 cookie 验真失败：isLogin=False, code={code}", file=sys.stderr)
            print("  可能：SESSDATA 已过期，或三件套来自不同会话。重新登录 B 站后再跑。", file=sys.stderr)
            sys.exit(6)
        # auto 模式继续试下一个
        print(f"  · {browser}：抓到 cookie 但 isLogin=False，试下一个…")

    # 全部失败
    print("✗ 没有任何浏览器拿到有效的 B 站登录态。", file=sys.stderr)
    print(f"  最后错误：{last_err}", file=sys.stderr)
    print("  请确认：已在某个浏览器登录 bilibili.com（非无痕），且批准了钥匙串解锁。", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
