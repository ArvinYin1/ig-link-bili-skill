#!/usr/bin/env python3
"""
ig-link-bili: 单条 IG Reel → B 站上传 wrapper

用法：
  python3 upload_one.py <shortcode> <title> <description> [选项]

位置参数：
  shortcode    Instagram Reel 短码（如 DYyvKNpEdoo）
  title        中文标题（agent 生成；不含任何写死前缀）
  description  中文描述（保留 "—— 原简介 ——" 段落；不要写原视频链接）

选项（编辑风格——按你的频道/内容定，不写死）：
  --category TID   B 站分区 TID（必填：命令行或 config.json 二选一提供）
  --tags  a,b,c    标签，逗号分隔（默认读 config.json，再不行用 B 站默认）
  --source URL     转载来源（默认自动用该 Reel 的 IG 链接）

可选配置文件 config.json（放在 skill 根目录，见 config.example.json）：
  { "title_prefix": "", "category": "", "tags": [] }
  解析优先级：命令行参数 > config.json > 兜底。
  title_prefix 非空且标题没带它时，自动加在标题前（给固定频道用）。

前置：
  - <media_dir>/<shortcode>.mp4         (prepare_media.py 下载好的视频)
  - <media_dir>/<shortcode>thumb.jpg    (封面；缺失则 B 站自动生成)
    media_dir 默认 = 系统临时目录/ig_link_bili，可用环境变量 IG_MEDIA_DIR 改
  - bilibili_uploader/credentials.json  (B 站 cookie，由 setup_cookies.py 生成)

返回：
  stdout JSON: {success, bvid, aid, message, ...}；非 0 退出码 = 上传失败

实现说明：内部生成一个临时 .py 脚本调用 bilibili_uploader.publisher，然后删除。
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
SKILL_DIR = SCRIPT_DIR.parent
UPLOADER_DIR = SKILL_DIR / "bilibili_uploader"
CONFIG_PATH = SKILL_DIR / "config.json"

# 视频/封面路径（跨平台：默认放系统临时目录，不写死 /tmp）
DEFAULT_MEDIA_DIR = Path(tempfile.gettempdir()) / "ig_link_bili"
MEDIA_DIR = Path(os.environ.get("IG_MEDIA_DIR") or DEFAULT_MEDIA_DIR)


def load_config():
    """读取可选的 config.json（用户固定偏好）；不存在就返回空 dict。"""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(json.dumps({"success": False, "error": f"config.json 解析失败: {e}"}, ensure_ascii=False))
            sys.exit(2)
    return {}


def fail(msg, code=2):
    print(json.dumps({"success": False, "error": msg}, ensure_ascii=False))
    sys.exit(code)


def main():
    ap = argparse.ArgumentParser(add_help=True, description="单条 IG Reel 上传到 B 站")
    ap.add_argument("shortcode")
    ap.add_argument("title")
    ap.add_argument("description")
    ap.add_argument("--category", help="B 站分区 TID（命令行或 config.json 必须提供其一）")
    ap.add_argument("--tags", help="标签，逗号分隔")
    ap.add_argument("--source", help="转载来源 URL（默认用该 Reel 的 IG 链接）")
    args = ap.parse_args()

    cfg = load_config()
    shortcode = args.shortcode

    # --- 标题：可选前缀（仅 config.json 提供时生效，给固定频道用）---
    title = args.title
    prefix = cfg.get("title_prefix", "")
    if prefix and not title.startswith(prefix):
        title = prefix + title

    # --- 分区：命令行 > config > 报错（绝不默默猜，避免进错区）---
    category = args.category or cfg.get("category")
    if not category:
        fail("未指定 B 站分区。请用 --category <TID>，或在 config.json 设置 category。"
             "（按视频内容选分区；创意/动画类内容不要用游戏默认区。）")
    category = str(category)

    # --- 标签：命令行 > config > 空（交给 B 站默认）---
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
    elif cfg.get("tags"):
        tags = list(cfg["tags"])
    else:
        tags = []

    # --- 来源：命令行 > 默认用 IG 链接 ---
    source = args.source or f"https://www.instagram.com/reel/{shortcode}/"

    description = args.description
    video_path = MEDIA_DIR / f"{shortcode}.mp4"
    cover_path = MEDIA_DIR / f"{shortcode}thumb.jpg"
    if not video_path.exists():
        fail(f"video not found: {video_path}（先跑 prepare_media.sh）")

    # 把参数落到临时 .py 脚本
    cred_file = str(UPLOADER_DIR / "credentials.json")
    helper_code = f'''#!/usr/bin/env python3
import sys, json, asyncio
sys.path.insert(0, {str(UPLOADER_DIR)!r})
from main import BilibiliAllInOne

bilibili = BilibiliAllInOne(credential_file={cred_file!r})
publisher = bilibili.publisher

async def main():
    try:
        result = await publisher.upload(
            file_path={str(video_path)!r},
            title={title!r},
            description={description!r},
            tags={tags!r},
            category={category!r},
            cover_path={str(cover_path)!r},
            no_reprint=0,
            source={source!r},
        )
        print("IGLINK_RESULT=" + json.dumps(result, ensure_ascii=False))
    except Exception as e:
        print("IGLINK_RESULT=" + json.dumps({{"success": False, "error": str(e)}}, ensure_ascii=False))

asyncio.run(main())
'''

    # 写到临时 .py 文件
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".py", prefix="iglink_upload_",
        delete=False,
    ) as f:
        f.write(helper_code)
        helper_path = f.name

    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{UPLOADER_DIR}:" + env.get("PYTHONPATH", "")

        proc = subprocess.run(
            [sys.executable, helper_path],
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )

        out_line = None
        for line in proc.stdout.splitlines():
            if line.startswith("IGLINK_RESULT="):
                out_line = line[len("IGLINK_RESULT="):]
                break

        if out_line:
            try:
                result = json.loads(out_line)
                print(json.dumps(result, ensure_ascii=False, indent=2))
                sys.exit(0 if (result.get("success") or result.get("bvid")) else 1)
            except json.JSONDecodeError as e:
                print(json.dumps({
                    "success": False,
                    "error": f"JSON parse: {e}",
                    "raw": out_line[:500],
                }, ensure_ascii=False, indent=2))
                sys.exit(1)
        else:
            print(json.dumps({
                "success": False,
                "error": "publisher 未返回 IGLINK_RESULT",
                "stdout_tail": proc.stdout[-500:],
                "stderr_tail": proc.stderr[-500:],
            }, ensure_ascii=False, indent=2))
            sys.exit(1)
    finally:
        try:
            os.unlink(helper_path)
        except OSError:
            pass


if __name__ == "__main__":
    main()
