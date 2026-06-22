# ig-link-bili

> 把你给的 Instagram Reel 链接，自动下载、翻译标题简介、转载到 B 站。

一个 Claude / agent **skill**（同时也是一套可独立运行的脚本）。你扔一条 `instagram.com/reel/<code>/` 链接并说"转到 B 站"，它就完成 **下载 → 翻译文案 → 上传 → 验真** 全流程。

**它做什么**

- 解析单条（或一批）IG Reel/Post 链接
- 用 `yt-dlp` 公开下载视频 + 封面 + 元数据（**无需 Instagram 账号**）
- 把外文标题/简介翻成中文（由 agent 完成）
- 上传到 B 站，并在视频里填好原作者归属
- 上传后调 B 站 API **验真**（接口异步，返 success ≠ 真成功）

**它不做什么**（核心设计取舍）

- ❌ 不自动抓 IG feed / hashtag —— 链接都是你主动给的
- ❌ 不做点赞阈值筛选、不做去重、不做作者黑名单

链接是你给的，过滤掉反而是 surprise。需要自动抓取请用别的工具。

---

## 环境要求

| 依赖 | 用途 | 安装 |
|---|---|---|
| Python 3.8+ | 跑脚本 | 系统自带 |
| `yt-dlp` | 公开下载 IG Reel | `brew install yt-dlp` / `pip install yt-dlp` |
| `ffmpeg` | 截帧兜底封面 | `brew install ffmpeg` / `apt install ffmpeg` |
| pip 依赖 | B 站上传库 | `pip install -r bilibili_uploader/requirements.txt` |
| `browser_cookie3` | 从浏览器抓 B 站 cookie | `pip install browser_cookie3` |
| 一个 B 站账号 | 上传用（你自己的） | 在浏览器登录 bilibili.com |

---

## 安装

```bash
# 1) 获取代码
git clone https://github.com/ArvinYin1/ig-link-bili-skill.git
cd ig-link-bili-skill

# 2) 装依赖
pip install -r bilibili_uploader/requirements.txt browser_cookie3 yt-dlp
brew install yt-dlp ffmpeg          # macOS（Linux 用 apt/yum 装 yt-dlp + ffmpeg）

# 3) 刷 B 站 cookie（首次必做）—— 仓库里不含真 cookie，只有占位模板
#    先在任意浏览器登录 bilibili.com（chrome/edge/brave/arc/vivaldi/firefox/safari 都行），再跑：
python3 scripts/setup_cookies.py            # 自动探测已登录 B 站的浏览器
# 或指定：python3 scripts/setup_cookies.py --browser firefox
# 看到 "✓ 成功！...isLogin=True, @你的用户名" 即配置完成。cookie 过期了重跑同一条命令。
```

> **作为 Claude / agent skill 使用**：把整个目录放进你 agent 的 skills 目录，agent 会通过 `SKILL.md` 的
> 描述自动识别——当你发来 IG 链接并表达"转载到 B 站"时触发。仍需先完成上面第 2、3 步（装依赖 + 刷 cookie）。

---

## 使用

装好依赖、刷过 cookie 之后，**你不用记任何命令**——直接把 IG 链接发给 agent，并说一句"转到 B 站"即可。

**怎么跟 agent 说**（举例）：

```
把这条转载到 B 站：https://www.instagram.com/reel/DYyvKNpEdoo/
```

```
这几条 IG Reel 都搬到 B 站：
https://www.instagram.com/reel/DYyvKNpEdoo/
https://www.instagram.com/reel/Cabc123dEfg/
```

**触发条件**：消息里 ① 含 `instagram.com` 链接（`/reel/`、`/p/`、`/tv/`），**且** ② 表达了"转载 / 搬运 / 上传 / 转到 B 站"的意图。只是分享链接、问内容是什么，**不会**触发。

**agent 收到后自动做的事**（你只需等结果）：

1. 下载视频 + 封面 + 元数据（`yt-dlp`，公开下载，无需 IG 账号）
2. 把外文标题/简介翻成中文
3. 上传到 B 站，填好原作者归属
4. 等 1-2 分钟调 API 验真（接口异步，确保真成功）
5. 回给你 B 站视频地址：`https://www.bilibili.com/video/<bvid>`

多条链接会串行处理、彼此间隔，一条失败不影响其他，最后汇总。

**自定义编辑风格**：标题前缀（默认 `【动态参考】`）、tags、分区（`category`）、描述模板都在
[`scripts/upload_one.py`](./scripts/upload_one.py) 里改。默认**不会**把视频加入任何合集。

<details>
<summary>手动运行（不通过 agent，调试用）</summary>

以 shortcode `DYyvKNpEdoo`（取自 `instagram.com/reel/DYyvKNpEdoo/`）为例：

```bash
# 1) 下载视频 + 封面 + 元数据
./scripts/prepare_media.sh DYyvKNpEdoo
#    产出 /tmp/ig_link_bili/DYyvKNpEdoo.{mp4,info.json,thumb.jpg}

# 2) 读元数据里的 description，自己翻成中文标题 + 描述
cat /tmp/ig_link_bili/DYyvKNpEdoo.info.json

# 3) 上传到 B 站
python3 ./scripts/upload_one.py DYyvKNpEdoo "<中文标题>" "<中文描述>" "<原作者用户名>"

# 4) 等 1-2 分钟验真
sleep 60 && python3 ./scripts/verify_upload.py <上一步的 bvid>
```
</details>

完整工作流、多链接处理、边界情况见 [SKILL.md](./SKILL.md)。

---

## 文件结构

```
ig-link-bili-skill/
├── SKILL.md                       # agent 视角的完整工作流与规则
├── README.md                      # 本文件
├── scripts/
│   ├── setup_cookies.py           # 首次必跑：从本机浏览器抓 B 站 cookie（多浏览器，自动验真）
│   ├── prepare_media.sh           # 下载 mp4 + 截/拉封面 + 拉元数据
│   ├── upload_one.py              # 单条上传 B 站
│   └── verify_upload.py           # B 站 API 验真（带重试）
├── bilibili_uploader/             # 自包含 B 站上传库
│   ├── credentials.json.template  # cookie 模板（真 credentials.json 由 setup_cookies.py 生成，已 .gitignore）
│   ├── main.py / src/ / ...
│   └── requirements.txt
├── examples/test_links.md         # 测试链接
└── references/                    # 排错：踩坑记录 + 诊断方法论
    ├── pitfalls.md
    ├── diagnosis-methodology.md
    └── ...
```

---

## 排错

最常见问题：`upload_one.py` 抛 `Expecting value: line 1 column 1` —— **几乎一定是本机 cookie 失效**（不是 B 站挂了）。先重刷：

```bash
python3 scripts/setup_cookies.py
```

30 秒判定登录态：

```bash
SESSDATA=$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('bilibili_uploader/credentials.json').read_text())['sessdata'])")
curl -sS "https://api.bilibili.com/x/web-interface/nav" -b "SESSDATA=$SESSDATA" | python3 -c "import json,sys; print('isLogin:', json.load(sys.stdin)['data']['isLogin'])"
```

更多坑（cookie 三件套必须同源、preupload 403 决策树等）见 [`references/pitfalls.md`](./references/pitfalls.md)。

---

## ⚠️ 使用须知 / 免责声明

- **版权与合规自负**：本工具会把**他人的** Instagram 内容转到 B 站。是否有权转载、B 站转载规则、原作者授权，**由使用者自行负责**。脚本会自动填 `source` 原作者归属，但这不替代取得授权。
- **用你自己的 B 站账号，风险自担**：短时间大量转载可能触发 B 站风控/处罚。脚本已串行 + 间隔上传，但账号后果由你承担。
- **cookie 是你本机 / 本账号专属**：`setup_cookies.py` 读取你本机浏览器的 B 站登录态（macOS 上 Chromium 系会弹一次钥匙串）。**绝不要**把生成的 `credentials.json` 拷给别人——B 站按设备指纹绑会话，拷出去既无效也泄露你的账号。
- **依赖外部站点**：`yt-dlp` 下载依赖 Instagram 页面结构，IG 改版时可能需要 `pip install -U yt-dlp`。

---

## 致谢

B 站上传能力来自 [`wscats/bilibili-all-in-one`](https://github.com/wscats/bilibili-all-in-one)（MIT），已 vendored 进 `bilibili_uploader/`，许可证见该目录下的 `LICENSE`。
