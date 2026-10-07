# 词表出处与许可

`vocab.json` 和 `sentences.json` 是改编数据库，不是 MIT。公开这些文件时，本说明必须一起提供。

改编词表的许可证是 Creative Commons Attribution-ShareAlike 4.0 International。

https://creativecommons.org/licenses/by-sa/4.0/

CC 许可证按原样提供，不作担保。完整免责声明见上面的许可证文本。

例句同时受 CC-BY 2.0 FR 约束：

https://creativecommons.org/licenses/by/2.0/fr/deed.en

## 署名

- 词元、词频排名、词性、阴阳性、变位、CEFR 估算：wordhoard 0.1.0，Emanuele Natale。https://github.com/natema/wordhoard 。数据集 CC-BY-SA 4.0。
- 阴阳性与变位来自维基词典贡献者，经 kaikki.org / wiktextract（Tatu Ylönen），CC-BY-SA 4.0。https://kaikki.org
- 词频来自 OpenSubtitles，经 hermitdave/FrequencyWords，MIT。https://github.com/hermitdave/FrequencyWords
- 词元化与词性：spaCy，MIT。https://spacy.io
- 英文释义：doozan/spanish_data，来自英语维基词典贡献者，CC-BY-SA。https://github.com/doozan/spanish_data
- 例句：Tatoeba 贡献者，CC-BY 2.0 FR。https://tatoeba.org

未获上述项目背书。CEFR 不是塞万提斯学院考纲。

## 改动

相对上游，本包做了这些改编：

- 只保留词频排名前 5000 中的名词、动词、AUX、形容词、副词。
- 去掉 vosotros / 第二人称复数。ustedes 使用原表第三人称复数。
- 命令式 ustedes 取虚拟现在第三人称复数。tú 命令式因源标签不可靠而未收入。
- 没有单独标注的简单过去时。不是智利口语变位，也不是河板 voseo。
- 每词最多两条 4–16 词的 Tatoeba 例句。释义取维基词典首条短释义。
