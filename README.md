# 西语词表练习站（拉美）

个人用的静态练习页生成器。词表来自 wordhoard（词频、词性、阴阳性、变位、估算 CEFR）和 doozan/spanish_data（英文释义、Tatoeba 例句）。

不是词典，也不是塞万提斯考纲。CEFR 是词频估算。变位是通用拉美教学：yo / tú / usted·él / nosotros / ustedes，没有 vosotros，没有智利口语 `estái`，没有河板 voseo。源数据没有单独标注的简单过去时。

## 生成

```bash
python3 build.py
```

只依赖 Python 3.9+ 标准库。首次会下载 wordhoard CSV 包和 doozan 释义，缓存在 `.cache/`。成功后得到：

- `dist/index.html`
- `dist/vocab.json`
- `dist/sentences.json`
- `dist/review.csv`：人工核对表，含排名、等级、释义、是否进默认队列、变位时态和例句。Excel 用 UTF-8 BOM。排名前 6000，等级到 B2。

本地预览：

```bash
python3 -m http.server -d dist 8765
```

Cloudflare Pages：把 `dist/` 作为根目录上传，或连到本仓库后把构建命令设为 `python3 build.py`、输出目录设为 `dist`。

## 练习

- 认词、听写、变位、浏览。顶栏可改等级范围（点一个等级是单级，再点另一个是区间）、每日新词和重音开关。界面中文 / English，手动优先，否则跟浏览器语言。
- 默认新词队列只要名词、动词（含 ser/estar/haber 这类 AUX）、形容词、副词，每天 15 个，等级 A2–B1。
- 进度和设置分开存在浏览器本地，设置页可分别导出 JSON。

## 许可

脚本和页面模板 MIT，见 `LICENSE`。生成的 `vocab.json` 和 `sentences.json` 是 CC-BY-SA 4.0 改编词表，例句另受 Tatoeba CC-BY 2.0 FR 约束。公开 `dist/` 时必须带上 `NOTICE.md` 和 `LICENSE-DATA`。署名、上游链接和改动说明都在 `NOTICE.md`。
