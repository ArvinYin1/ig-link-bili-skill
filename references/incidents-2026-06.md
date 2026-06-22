# ig-link-bili 事故时间线（2026-06）

按时间倒序记录实测撞墙点 + 复现步骤 + 根因 + 修复。**主 SKILL.md 只放规则**，session-specific 留这里。

---

## 2026-06-13 · cookie 失效导致 upload 假失败（`Expecting value: line 1 column 1`）

**场景**：连跑多条 IG Reel 转载，第一条就失败。

**症状**：`upload_one.py` 返：
```json
{"success": false, "error": "Expecting value: line 1 column 1 (char 0)"}
```
（preupload 返了 HTML 错误页，不是 JSON。）

**根因诊断**（30 秒）：
```bash
SESSDATA=$(python3 -c "import json,pathlib; print(json.loads(pathlib.Path('bilibili_uploader/credentials.json').read_text())['sessdata'])")
curl -sS -m 10 "https://api.bilibili.com/x/web-interface/nav" -b "SESSDATA=$SESSDATA"
# → isLogin: false  ⇒ 本机 cookie 失效（不是 B 站上游）
```

**修复**：
```bash
python3 scripts/setup_cookies.py   # 重刷本份 cookie，自动验真
```
重刷后重跑 `upload_one.py`，多条全部上传 + 验真 OK。

**教训**：
1. 任何 `Expecting value: line 1 column 1` 错误 **先**跑 nav API 验 `isLogin`，**再**归因上游
2. `isLogin: false` 几乎一定是本机 cookie 失效——`setup_cookies.py` 重刷即可
3. 长期方案：让 `upload_one.py` 启动时自检 SESSDATA 占位/失效并提示重刷（见 pitfalls §9 预防）

> （作者本机原始事故还涉及"多个搬运 skill 各维护一份 cookie 互不同步"，已在 pitfalls §10 归档；
> 独立安装者不涉及。）

---

## 历史事故
（更早的事故记录在更早版本的 incidents 文件中，按需往这里追加）
