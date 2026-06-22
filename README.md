# ig-link-bili

> 把你给的 Instagram Reel 链接，自动下载、翻译、转载到 B 站。

一个 **agent skill**（任何支持 skill 的 AI agent 都能用，不绑定特定平台）。你只管把 IG 链接丢给 agent、说一句"转到 B 站"——**装依赖、刷 cookie、下载、翻译、上传、验真，全部由 agent 自动完成**。

**系统支持：macOS / Windows / Linux 均可。**

> [!IMPORTANT]
> ## 🧑 你只需亲自做这 1-2 件事
> agent 替你包办其余一切，但下面这些**它做不了，必须你来**：
>
> 1. **在浏览器登录你的 B 站账号** —— agent 没有你的账号密码，登不进去。（所有系统都需要）
> 2. **（仅 macOS + 用 Chrome 等 Chromium 浏览器时）首次刷 cookie，在弹出的钥匙串密码框点「允许」** —— 原生安全弹窗，agent 点不了。**Windows / Linux 通常不弹；任何系统改用 Firefox 也不弹。**
>
> 其余（装依赖、刷 cookie、下载、翻译、上传、验真）你都不用管。

**它做什么**

- 解析单条（或一批）IG Reel/Post 链接
- 公开下载视频 + 封面 + 元数据（`yt-dlp`，**无需 Instagram 账号**）
- 把外文标题/简介翻成中文
- 上传到 B 站，填好原作者归属
- 上传后调 B 站 API **验真**（接口异步，返 success ≠ 真成功）

**它不做什么**（核心设计取舍）

- ❌ 不自动抓 IG feed / hashtag —— 链接都是你主动给的
- ❌ 不做点赞阈值筛选、不做去重、不做作者黑名单

---

## 快速开始

你只需要做几件 agent 替不了的小事，其余全部交给它。

### ① 让 agent 拿到这个 skill

把本仓库放进你 agent 的 skills 目录，或者直接对 agent 说：

```
把这个 skill 装好：https://github.com/ArvinYin1/ig-link-bili-skill
```

agent 会克隆代码、**自动装好所有依赖**（Python 包 / `yt-dlp` / `ffmpeg`），并通过 `SKILL.md` 识别这个 skill。

### ② 在浏览器登录 bilibili.com

agent **不能替你登录账号**——请自己在某个浏览器（Chrome / Edge / Brave / Arc / Firefox / Safari 都行）登录好你的 B 站。

### ③ 直接对 agent 说话

```
把这条转到 B 站：https://www.instagram.com/reel/DYyvKNpEdoo/
```

**首次运行**时，agent 会自动跑 `setup_cookies.py` 从你浏览器把 B 站登录态读出来，之后你就等结果。

> [!WARNING]
> 🧑 **可能需要你动手的瞬间（仅 macOS）**：用 Chrome 等 Chromium 系浏览器时，系统会弹一次**钥匙串密码框**——点「允许」即可。这是原生安全弹窗，agent 替你点不了。**Windows / Linux 一般不弹（静默读取）；改用 Firefox 任何系统都不弹。**

---

## 谁做什么

| 事项 | 谁来做 |
|---|---|
| 装 Python 依赖 / `yt-dlp` / `ffmpeg` | 🤖 agent |
| 刷 B 站 cookie（跑 `setup_cookies.py`） | 🤖 agent |
| 下载视频、翻译文案、上传、验真 | 🤖 agent |
| cookie 过期后重刷（你说一句"cookie 过期了重刷下"） | 🤖 agent |
| **在浏览器登录 B 站账号** | 🧑 **你**（agent 没有你的账号密码） |
| **批准 macOS 钥匙串弹窗**（仅 Chromium 系 + 首次） | 🧑 **你**（原生安全弹窗，agent 点不了） |

---

## 怎么跟 agent 说（触发）

单条：

```
把这条转载到 B 站：https://www.instagram.com/reel/DYyvKNpEdoo/
```

多条（会串行处理、彼此间隔，一条失败不影响其他）：

```
这几条 IG Reel 都搬到 B 站：
https://www.instagram.com/reel/DYyvKNpEdoo/
https://www.instagram.com/reel/Cabc123dEfg/
```

**触发条件**：消息里 ① 含 `instagram.com` 链接（`/reel/`、`/p/`、`/tv/`），**且** ② 表达"转载 / 搬运 / 上传 / 转到 B 站"的意图。只是分享链接、问内容是什么，**不会**触发。

**agent 收到后自动做的事**（你只需等结果）：下载 → 翻译标题简介 → 上传（填好原作者归属）→ 等 1-2 分钟验真 → 回给你 B 站视频地址 `https://www.bilibili.com/video/<bvid>`。

---

## 自定义编辑风格（不写死，适配不同场景）

标题、描述、**B 站分区（category）**、**标签（tags）** 都**不固定**：

- **默认**：由 agent 按视频内容 + 你当下的话临时决定（零配置）。比如你说"发到动画区、带上 #定格动画 标签"，它就照做。
- **想给固定频道设默认**：把 [`config.example.json`](./config.example.json) 复制成 `config.json`，填好 `title_prefix` / `category` / `tags`，agent 会自动沿用（命令行临时指定仍可覆盖）。

> 解析优先级：命令行参数 > `config.json` > 兜底。分区**不会**默默用一个写死值——没指定时脚本会要求你/agent 明确给出，避免投错区。默认也**不会**把视频加入任何合集。

---

## 文件结构

```
ig-link-bili-skill/
├── SKILL.md                       # agent 视角的完整工作流与规则
├── README.md                      # 本文件
├── config.example.json            # 可选配置模板（复制为 config.json 设固定分区/标签/标题前缀）
├── scripts/
│   ├── setup_cookies.py           # 从本机浏览器抓 B 站 cookie（多浏览器，自动验真）
│   ├── prepare_media.py           # 下载 mp4 + 截/拉封面 + 拉元数据
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

绝大多数失败是 **B 站 cookie 失效**（agent 会看到 `Expecting value: line 1 column 1`）。这时对 agent 说一句即可：

```
B 站 cookie 好像过期了，帮我重刷一下
```

agent 会重跑 `setup_cookies.py`（你可能要再点一次钥匙串）。技术细节、cookie 三件套必须同源、preupload 403 决策树等，见 [`references/pitfalls.md`](./references/pitfalls.md)。

<details>
<summary>手动安装 / 运行（不通过 agent，开发调试用）</summary>

支持 macOS / Windows / Linux。下面命令里的 `python3`，**Windows 上换成 `python`**（或 `py`）。

```bash
# 安装
git clone https://github.com/ArvinYin1/ig-link-bili-skill.git && cd ig-link-bili-skill
pip install -r bilibili_uploader/requirements.txt browser_cookie3 yt-dlp
# yt-dlp + ffmpeg 系统工具：
#   macOS:   brew install yt-dlp ffmpeg
#   Linux:   apt install ffmpeg   （yt-dlp 已由上面的 pip 装）
#   Windows: winget install Gyan.FFmpeg  （或 scoop install ffmpeg；yt-dlp 已由 pip 装）
#   Windows 还需： pip install pywin32   （browser_cookie3 解 Chromium cookie 用）
python3 scripts/setup_cookies.py                 # 先在浏览器登录 bilibili.com；或 --browser firefox

# 跑一条（shortcode 取自 instagram.com/reel/DYyvKNpEdoo/）
python3 scripts/prepare_media.py DYyvKNpEdoo                              # 下载 + 封面 + 元数据
python3 scripts/upload_one.py DYyvKNpEdoo "<中文标题>" "<中文描述>" --category <TID> --tags 标签1,标签2   # 上传
python3 scripts/verify_upload.py <bvid>                                  # 等 1-2 分钟后验真
```

完整工作流见 [SKILL.md](./SKILL.md)。
</details>

---

## ⚠️ 使用须知 / 免责声明

- **版权与合规自负**：本工具会把**他人的** Instagram 内容转到 B 站。是否有权转载、B 站转载规则、原作者授权，**由使用者自行负责**。脚本会自动填 `source` 原作者归属，但这不替代取得授权。
- **用你自己的 B 站账号，风险自担**：短时间大量转载可能触发 B 站风控/处罚。脚本已串行 + 间隔上传，但账号后果由你承担。
- **cookie 是你本机 / 本账号专属**：`setup_cookies.py` 读取你本机浏览器的 B 站登录态。**绝不要**把生成的 `credentials.json` 拷给别人——B 站按设备指纹绑会话，拷出去既无效也泄露你的账号。
- **依赖外部站点**：`yt-dlp` 下载依赖 Instagram 页面结构，IG 改版时可能需要更新（`pip install -U yt-dlp`，也可让 agent 代劳）。

---

## 致谢

B 站上传能力来自 [`wscats/bilibili-all-in-one`](https://github.com/wscats/bilibili-all-in-one)（MIT），已 vendored 进 `bilibili_uploader/`，许可证见该目录下的 `LICENSE`。
