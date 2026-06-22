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

# 2) 上传
python3 ./scripts/upload_one.py "DVT6MCWgroY" \
"【动态参考】Higgsfield AI 脚下发电——日本把脚步转化为电力的创新设计" \
"转载来源：Instagram - 原作者：@higgsfield.ai

Higgsfield AI 介绍日本一项把脚步转化为电力的设计，以及自家的 Soul Hex 工具。

—— 原简介 ——
#🇯🇵 Japan is turning footsteps into electricity! AI Color Matching has never been this easy 🧩 Meet Higgsfield Soul Hex

Upload your reference and transfer color palette to your visuals in a single click. Save once, generate forever." \
"higgsfield.ai"

# 3) 等 60s 验真
sleep 60
python3 ./scripts/verify_upload.py <上一步返回的 bvid>
```

期望输出：
- `success: true`
- `bvid: BV1xxxxxxx`
- verify: `OK BV1xxxxxxx | 【动态参考】Higgsfield AI...`
