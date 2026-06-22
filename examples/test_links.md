# 测试链接（2026-06-05 验证用）

下面这些是已经验证过、可正常下载 + 上传 + 在 B 站可见的 Reel 链接。

可以拿来做 smoke test：

```
https://www.instagram.com/reel/DVT6MCWgroY/    # Higgsfield AI 85k 赞
https://www.instagram.com/reel/DYyvKNpEdoo/    # Nothing 10k 赞
https://www.instagram.com/reel/DSC8VLEjWDM/    # xk.studio 14.4 万赞
https://www.instagram.com/reel/DZKVEbStlD2/    # rocketpanda 4.7k
https://www.instagram.com/reel/DX36S_8ByRb/    # nazmul.motion 4.1k
```

## Smoke test 流程

```bash
# 1) 准备视频
./scripts/prepare_media.sh DVT6MCWgroY

# 2) 上传（标题/分区/标签按内容定——下面的标题前缀、分区、标签都只是示例值）
python3 ./scripts/upload_one.py "DVT6MCWgroY" \
"Higgsfield AI 脚下发电——日本把脚步转化为电力的创新设计" \
"转载来源：Instagram - 原作者：@higgsfield.ai

Higgsfield AI 介绍日本一项把脚步转化为电力的设计，以及自家的 Soul Hex 工具。

—— 原简介 ——
#🇯🇵 Japan is turning footsteps into electricity! AI Color Matching has never been this easy 🧩 Meet Higgsfield Soul Hex

Upload your reference and transfer color palette to your visuals in a single click. Save once, generate forever." \
--category 207 --tags "AI,创意设计,黑科技"

# 3) 等 60s 验真
sleep 60
python3 ./scripts/verify_upload.py <上一步返回的 bvid>
```

> `--category 207` 仅为示例（请按内容选你账号合适的分区 TID）。想固定前缀/分区/标签的，
> 用 `config.json`（见 [`config.example.json`](../config.example.json)）。

期望输出：
- `success: true`
- `bvid: BV1xxxxxxx`
- verify: `OK BV1xxxxxxx | <你的标题>...`
