#!/usr/bin/env python3
"""
ig-link-bili: 一步到位——下载 IG 视频 + 封面 + 元数据（跨平台：mac / Windows / Linux）

用法：
  python3 prepare_media.py <shortcode> [media_dir]

参数：
  shortcode   Instagram Reel 短码（如 DYyvKNpEdoo）
  media_dir   输出目录（默认 = 系统临时目录/ig_link_bili）

前置：PATH 上有 yt-dlp（必需）和 ffmpeg（可选，仅截帧兜底封面用）

输出：
  <media_dir>/<shortcode>.mp4
  <media_dir>/<shortcode>.info.json   (元数据：uploader / like_count / description ...)
  <media_dir>/<shortcode>thumb.jpg     (封面：优先 IG 官方图，失败用 ffmpeg 截第 1 秒帧)

封面缺失（如极短视频 + 无 ffmpeg）时不报错——upload 时 B 站会自动生成默认封面。
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd):
    """跑外部命令，返回 (returncode, stdout+stderr)。list 形式，不经过 shell，跨平台安全。"""
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) >= 2 else 1)

    shortcode = sys.argv[1]
    media_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(tempfile.gettempdir()) / "ig_link_bili"
    media_dir.mkdir(parents=True, exist_ok=True)

    ytdlp = shutil.which("yt-dlp")
    if not ytdlp:
        print("✗ 找不到 yt-dlp。安装：pip install -U yt-dlp（或 brew/winget/scoop/apt）", file=sys.stderr)
        sys.exit(3)
    ffmpeg = shutil.which("ffmpeg")  # 可选

    url = f"https://www.instagram.com/reel/{shortcode}/"
    out_tmpl = str(media_dir / f"{shortcode}.%(ext)s")
    mp4 = media_dir / f"{shortcode}.mp4"
    info = media_dir / f"{shortcode}.info.json"
    thumb = media_dir / f"{shortcode}thumb.jpg"

    # 1) 下载视频
    if not mp4.exists():
        print(f"yt-dlp 下载 {shortcode} ...")
        rc, out = run([ytdlp, "--no-check-certificates", "-o", out_tmpl, url])
        if rc != 0 and not mp4.exists():
            print(f"✗ 下载失败：\n{out[-500:]}", file=sys.stderr)
            sys.exit(4)

    # 2) 元数据（独立步骤，避免输出混淆）
    if not info.exists():
        print(f"yt-dlp 拉元数据 {shortcode} ...")
        run([ytdlp, "--no-check-certificates", "--skip-download", "--write-info-json", "-o", out_tmpl, url])

    # 3) 封面：先试 IG 官方封面，失败再 ffmpeg 截帧
    if not thumb.exists():
        print("yt-dlp 拉 IG 官方封面 ...")
        run([ytdlp, "--no-check-certificates", "--skip-download",
             "--write-thumbnail", "--convert-thumbnails", "jpg", "-o", out_tmpl, url])
        official = media_dir / f"{shortcode}.jpg"
        if official.exists():
            official.replace(thumb)  # 跨平台改名/移动（覆盖已存在）
            print("封面来源：IG 官方")
        elif ffmpeg and mp4.exists():
            print("官方封面失败，ffmpeg 截第 1 秒帧 ...")
            rc, out = run([ffmpeg, "-i", str(mp4), "-ss", "00:00:01", "-vframes", "1", str(thumb), "-y"])
            print("封面来源：ffmpeg 截帧" if thumb.exists() else "封面：跳过（B 站将自动生成）")
        else:
            print("封面：跳过（无 ffmpeg 或极短视频，B 站将自动生成默认封面）")

    # 4) 打印元数据关键字段
    if info.exists():
        try:
            d = json.loads(info.read_text(encoding="utf-8"))
            print("--- 元数据 ---")
            for k in ["uploader", "uploader_id", "like_count", "view_count",
                      "comment_count", "duration", "title", "description"]:
                v = d.get(k)
                if isinstance(v, str) and len(v) > 200:
                    v = v[:200] + "..."
                print(f"  {k}: {v!r}")
        except (json.JSONDecodeError, OSError) as e:
            print(f"（元数据解析失败：{e}）", file=sys.stderr)

    print(f"完成: {media_dir}/{shortcode}.{{mp4,info.json,thumb.jpg}}")


if __name__ == "__main__":
    main()
