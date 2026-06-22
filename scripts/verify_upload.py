#!/usr/bin/env python3
"""
ig-link-bili: 验真 B 站上传是否真成功

用法：
  python3 verify_upload.py <bvid>
  python3 verify_upload.py <bvid> --retries 5 --interval 30

返回：
  exit 0 + stdout "OK <title>" = 视频可查，转载成功
  exit 1 + stdout "FAIL ..." = 视频不存在
  exit 2 + stdout "PENDING ..." = 重试 N 次仍 PENDING

B 站上传接口是异步的：返 success + bvid 后，aid/bvid 真可查
可能要等 30s-2min。立即 verify 通常会拿到 -404。
"""
import argparse
import json
import sys
import time
import urllib.request


API_URL = "https://api.bilibili.com/x/web-interface/view"


def check(bvid: str) -> dict:
    """调 B 站 view API，返回完整 JSON。"""
    url = f"{API_URL}?bvid={bvid}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bvid", help="B 站视频 BV 号")
    ap.add_argument("--retries", type=int, default=3, help="重试次数（默认 3）")
    ap.add_argument("--interval", type=int, default=30, help="重试间隔秒（默认 30）")
    args = ap.parse_args()

    for attempt in range(1, args.retries + 1):
        result = check(args.bvid)
        code = result.get("code", -1)
        msg = result.get("message", "")

        if code == 0:
            data = result.get("data", {})
            title = data.get("title", "(no title)")
            print(f"OK {args.bvid} | {title}")
            sys.exit(0)
        elif code == -404:
            print(f"PENDING attempt {attempt}/{args.retries}: {msg}")
            if attempt < args.retries:
                time.sleep(args.interval)
        else:
            # 其他错误码（如 -101 未登录等）
            print(f"FAIL {args.bvid}: code={code} {msg}")
            sys.exit(1)

    print(f"FAIL {args.bvid}: 重试 {args.retries} 次后仍 404")
    sys.exit(2)


if __name__ == "__main__":
    main()
