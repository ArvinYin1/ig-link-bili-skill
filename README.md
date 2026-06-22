# ig-link-bili

把 Instagram Reel 链接（用户提供）下载、翻译、转载到 B 站。

不做 IG feed/hashtag 自动抓取、不做点赞阈值筛选、不做去重、不做作者黑名单——链接都是用户主动给的。

---

## ⚠️ 使用须知（分享版必读）

- **版权与合规自负**：本工具会把**他人的** Instagram 内容转到 B 站。是否有权转载、B 站转载规则、原作者授权，**由使用者自行负责**。脚本会自动在视频里填 `source` 原作者归属，但这不替代你取得授权。
- **用你自己的 B 站账号，风险自担**：短时间大量转载可能触发 B 站风控/处罚。脚本已串行 + 间隔上传，但账号后果由你承担。
- **cookie 是你本机/本账号专属**：`setup_cookies.py` 会读取你本机浏览器的 B 站登录态（macOS 上 Chromium 系会弹一次钥匙串）。**绝不要**把刷出来的 `credentials.json` 拷给别人——B 站按设备指纹绑会话，拷出去既无效也泄露你的账号。
- **依赖外部站点**：`yt-dlp` 下载 IG 依赖 Instagram 页面结构，IG 改版时可能需要 `pip install -U yt-dlp`。

---

## 给其他 Agent 的 30 秒上手

收到用户给的 Instagram 链接 + "转载到 B 站"意图：

```bash
# 1) 准备视频
./scripts/prepare_media.sh <shortcode> [/tmp/ig_link_bili]

# 2) 看元数据，自己脑内翻译 caption → 中文标题 + 中文描述
cat /tmp/ig_link_bili/<shortcode>.info.json

# 3) 上传
python3 ./scripts/upload_one.py <shortcode> "<中文标题>" "<中文描述>" "<uploader>"

# 4) 等 1-2 分钟验真
sleep 60
python3 ./scripts/verify_upload.py <上一步返回的 bvid>
```

完事。把 B 站视频 URL 汇报给用户：`https://www.bilibili.com/video/<bvid>`。

详细流程 + 边界情况见 [SKILL.md](./SKILL.md)。

---

## 安装（如果在新机器上跑）

```bash
# 1) Python 依赖
pip install -r bilibili_uploader/requirements.txt
pip install yt-dlp

# 2) 系统工具
brew install yt-dlp ffmpeg  # macOS
# 或: apt install yt-dlp ffmpeg  # Linux

# 3) B 站 cookie（首次必跑）——分发包里 credentials.json 是占位模板，没有真 cookie
pip install browser_cookie3
# 先在任意浏览器登录 bilibili.com（chrome/edge/brave/arc/vivaldi/firefox/safari 等都行），再跑：
python3 scripts/setup_cookies.py            # 自动探测已登录 B 站的浏览器
# 或指定：python3 scripts/setup_cookies.py --browser firefox
# 返回 "✓ 成功！...isLogin=True, @你的用户名" 即可。过期了重跑同一条命令。
```

---

## 文件结构

```
ig-link-bili/
├── SKILL.md
├── README.md
├── scripts/
│   ├── setup_cookies.py        # 首次必跑：从本机浏览器抓 B 站 cookie（多浏览器，自动验真）
│   ├── prepare_media.sh        # 一键下载 + 截封面 + 拉元数据
│   ├── upload_one.py           # 单条上传 B 站
│   └── verify_upload.py        # B 站 API 验真
├── bilibili_uploader/          # 自包含 B 站上传库（wscats/bilibili-all-in-one 拷贝）
│   ├── main.py
│   ├── src/
│   ├── credentials.json        # 你的 B 站 cookie（自带）
│   ├── credentials.json.template
│   ├── requirements.txt
│   └── ...
├── examples/
│   └── test_links.md
└── references/
    └── pitfalls.md
```
