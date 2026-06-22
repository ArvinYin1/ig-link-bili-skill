#!/bin/bash
# ig-link-bili: 一步到位——下载 IG 视频 + 截封面
# 用法: prepare_media.sh <shortcode> [media_dir]
#
# 前置: yt-dlp + ffmpeg 已装
# 输出:
#   <media_dir>/<shortcode>.mp4
#   <media_dir>/<shortcode>thumb.jpg
#   <media_dir>/<shortcode>.info.json   (元数据：uploader, like_count, description)

set -e

SHORTCODE="$1"
MEDIA_DIR="${2:-/tmp/ig_link_bili}"

if [ -z "$SHORTCODE" ]; then
  echo "用法: $0 <shortcode> [media_dir]"
  exit 1
fi

mkdir -p "$MEDIA_DIR"

# 1) 下载视频
if [ ! -f "$MEDIA_DIR/$SHORTCODE.mp4" ]; then
  echo "yt-dlp 下载 $SHORTCODE..."
  yt-dlp --no-check-certificates \
    -o "$MEDIA_DIR/$SHORTCODE.%(ext)s" \
    "https://www.instagram.com/reel/$SHORTCODE/" 2>&1 | tail -3
fi

# 2) 下载元数据（独立步骤，避免 yt-dlp 输出混淆 JSON）
if [ ! -f "$MEDIA_DIR/$SHORTCODE.info.json" ]; then
  echo "yt-dlp 拉元数据 $SHORTCODE..."
  yt-dlp --no-check-certificates \
    --skip-download --write-info-json \
    -o "$MEDIA_DIR/$SHORTCODE.%(ext)s" \
    "https://www.instagram.com/reel/$SHORTCODE/" 2>&1 | tail -2
fi

# 3) 拉封面（先 yt-dlp 抓 IG 官方封面，失败再 ffmpeg 截帧兜底）
#    Arvin 偏好 2026-06-07：优先原始封面，再截帧
if [ ! -f "$MEDIA_DIR/$SHORTCODE"thumb.jpg ]; then
  echo "yt-dlp 拉 IG 官方封面..."
  if yt-dlp --no-check-certificates \
      --skip-download --write-thumbnail --convert-thumbnails jpg \
      -o "$MEDIA_DIR/$SHORTCODE.%(ext)s" \
      "https://www.instagram.com/reel/$SHORTCODE/" 2>&1 | tail -2 \
      && [ -f "$MEDIA_DIR/$SHORTCODE.jpg" ]; then
    # yt-dlp 成功——把 .jpg 重命名为 .thumb.jpg 以匹配 upload_one.py 期望的路径
    mv "$MEDIA_DIR/$SHORTCODE.jpg" "$MEDIA_DIR/$SHORTCODE"thumb.jpg
    echo "封面来源：IG 官方"
  else
    # 兜底：ffmpeg 截第 1 秒
    echo "yt-dlp 拉封面失败，ffmpeg 截帧兜底..."
    ffmpeg -i "$MEDIA_DIR/$SHORTCODE.mp4" \
      -ss 00:00:01 -vframes 1 \
      "$MEDIA_DIR/$SHORTCODE"thumb.jpg -y 2>&1 | tail -1
    echo "封面来源：ffmpeg 第 1 秒截帧"
  fi
fi

# 4) 打印元数据关键字段
if [ -f "$MEDIA_DIR/$SHORTCODE.info.json" ]; then
  echo "---元数据---"
  python3 -c "
import json
d = json.load(open('$MEDIA_DIR/$SHORTCODE.info.json'))
for k in ['uploader', 'uploader_id', 'like_count', 'view_count', 'comment_count', 'duration', 'title', 'description']:
    v = d.get(k)
    if isinstance(v, str) and len(v) > 200:
        v = v[:200] + '...'
    print(f'  {k}: {v!r}')
"
fi

echo "完成: $MEDIA_DIR/$SHORTCODE.{mp4,info.json,thumb.jpg}"
