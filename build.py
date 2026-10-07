#!/usr/bin/env python3
"""Build a static LatAm Spanish vocab trainer from wordhoard + doozan.

Writes dist/index.html, dist/vocab.json, dist/sentences.json, dist/NOTICE.md.
No Node. Upload dist/ to Cloudflare Pages, or open index.html after serving
the folder (fetch needs http, not file://).
"""

from __future__ import annotations

import csv
import io
import json
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from urllib.request import urlopen, Request

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
CACHE = ROOT / ".cache"
WEB = ROOT / "web"

WORDHOARD_ZIP = "https://github.com/natema/wordhoard/releases/download/v0.1.0/wordhoard-csv-v0.1.0.zip"
DOOZAN_DICT = "https://raw.githubusercontent.com/doozan/spanish_data/master/es-en.data"
DOOZAN_SENT = "https://raw.githubusercontent.com/doozan/spanish_data/master/sentences.tsv"

MAX_RANK = 5000
MAX_SENTENCES = 2
SENT_MIN = 4
SENT_MAX = 16

CONTENT_POS = {"NOUN", "VERB", "AUX", "ADJ", "ADV"}

# wordhoard feature -> (tense id, person). 2pl dropped (vosotros).
PERSONS = ("1sg", "2sg", "3sg", "1pl", "3pl")
TENSE_LABELS = {
    "pres": "现在时",
    "impf": "未完成过去",
    "fut": "将来时",
    "cond": "条件式",
    "subj.pres": "虚拟现在",
    "subj.impf": "虚拟未完成",
    "subj.fut": "虚拟将来",
    "imp": "命令式",
    "ger": "副动词",
    "part": "过去分词",
}
PERSON_LABELS = {
    "1sg": "yo",
    "2sg": "tú",
    "3sg": "usted / él / ella",
    "1pl": "nosotros",
    "3pl": "ustedes",
    "ger": "副动词",
    "part": "过去分词",
}

POS_GLOSS = {
    "n": "NOUN",
    "noun": "NOUN",
    "v": "VERB",
    "verb": "VERB",
    "adj": "ADJ",
    "adv": "ADV",
    "aux": "AUX",
}


def fetch(url: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        print(f"cache {dest.name}")
        return dest
    print(f"get {url}")
    req = Request(url, headers={"User-Agent": "es-vocab-latam/1.0"})
    with urlopen(req, timeout=180) as resp:
        dest.write_bytes(resp.read())
    return dest


def strip_wiki(text: str) -> str:
    text = re.sub(r"\{\{[^}]*\}\}", " ", text)
    text = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = text.replace("'''", "").replace("''", "")
    text = re.sub(r"\s+", " ", text).strip(" ;,")
    return text


def load_glosses(path: Path) -> dict[tuple[str, str], str]:
    """lemma+UPOS -> first short English gloss."""
    glosses: dict[tuple[str, str], str] = {}
    lemma = ""
    pos = ""
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line == "_____":
                lemma = ""
                pos = ""
                continue
            if not lemma and line and not line.startswith(" "):
                lemma = line.strip().lower()
                continue
            if line.startswith("pos:"):
                raw = line.split(":", 1)[1].strip().lower()
                pos = POS_GLOSS.get(raw, "")
                continue
            if line.startswith("  gloss:") and lemma and pos:
                key = (lemma, pos)
                if key in glosses:
                    continue
                gloss = strip_wiki(line.split(":", 1)[1])
                if not gloss or gloss.startswith("inflection of") or gloss.startswith("form of"):
                    continue
                if len(gloss) > 140:
                    gloss = gloss[:137] + "..."
                glosses[key] = gloss
    return glosses


def load_sentences(path: Path) -> dict[str, list[dict]]:
    """lemma -> up to MAX_SENTENCES short es/en pairs.

    doozan sentences.tsv has no header. Columns are English, Spanish,
    attribution, then a tag field like ':n,amor :v,ser'.
    """
    buckets: dict[str, list[dict]] = defaultdict(list)
    if not path.exists() or path.stat().st_size == 0:
        return buckets
    with path.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 2:
                continue
            en, es = cols[0].strip(), cols[1].strip()
            n = len(es.split())
            if n < SENT_MIN or n > SENT_MAX:
                continue
            tag = cols[-1]
            lemmas = re.findall(r":(?:n|v|adj|adv),([a-záéíóúüñ]+)", tag.lower())
            if not lemmas:
                continue
            seen = set()
            for lem in lemmas:
                if lem in seen or len(buckets[lem]) >= MAX_SENTENCES:
                    continue
                seen.add(lem)
                buckets[lem].append({"es": es, "en": en})
    return buckets


CLITICS = ("melos", "melas", "selos", "selas", "nos", "les", "los", "las", "me", "te", "se", "le", "lo", "la")


def without_clitic(form: str) -> bool:
    return not any(form.endswith(c) and len(form) > len(c) + 2 for c in CLITICS)


def keep_forms(forms: list[str], imperative: bool) -> list[str]:
    if not imperative:
        return forms
    bare = [f for f in forms if without_clitic(f)]
    chosen = bare or sorted(forms, key=len)[:1]
    return chosen[:4]


def parse_forms(raw: str) -> dict:
    """Return {tense: {person: [forms]}} plus plural for nouns."""
    paradigms: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    plural = []
    if not raw:
        return {"paradigms": {}, "plural": []}
    for chunk in raw.split(";"):
        if ":" not in chunk:
            continue
        form, feat = chunk.split(":", 1)
        form = form.strip()
        feat = feat.strip()
        if not form or feat == "surface":
            continue
        if feat == "pl":
            plural.append(form)
            continue
        if feat.endswith(".2pl") or feat == "imp.pl":
            continue
        tense = None
        person = None
        for prefix in ("subj.pres", "subj.impf", "subj.fut", "pres", "impf", "fut", "cond"):
            if feat.startswith(prefix + "."):
                tense = prefix
                person = feat[len(prefix) + 1 :]
                break
        if feat == "ger":
            tense, person = "ger", "ger"
        elif feat == "part.perf":
            tense, person = "part", "part"
        elif feat == "imp.sg":
            # wordhoard imp.sg mixes clitics and subjunctive; skip tú imperative
            continue
        if not tense or person not in PERSONS and person not in ("ger", "part"):
            continue
        bucket = paradigms[tense][person]
        if form not in bucket:
            bucket.append(form)
    for tense, persons in paradigms.items():
        for person, forms in list(persons.items()):
            persons[person] = keep_forms(forms, tense == "imp")
    # ustedes affirmative imperative = subjunctive present 3pl when present
    if "subj.pres" in paradigms and "3pl" in paradigms["subj.pres"]:
        paradigms["imp"].setdefault("3pl", [])
        for form in paradigms["subj.pres"]["3pl"]:
            if form not in paradigms["imp"]["3pl"]:
                paradigms["imp"]["3pl"].append(form)
    clean = {t: dict(persons) for t, persons in paradigms.items() if persons}
    return {"paradigms": clean, "plural": plural}


def load_wordhoard(zip_path: Path) -> list[dict]:
    with zipfile.ZipFile(zip_path) as zf:
        name = next(n for n in zf.namelist() if n.endswith("es.csv"))
        text = io.TextIOWrapper(zf.open(name), encoding="utf-8")
        rows = list(csv.DictReader(text))
    rows.sort(key=lambda r: int(r["frequency_rank"]))
    return rows


def build() -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    zpath = fetch(WORDHOARD_ZIP, CACHE / "wordhoard-csv.zip")
    dpath = fetch(DOOZAN_DICT, CACHE / "es-en.data")
    try:
        spath = fetch(DOOZAN_SENT, CACHE / "sentences.tsv")
    except Exception as exc:
        print("sentences skipped:", exc)
        spath = CACHE / "sentences.tsv"

    print("parse glosses")
    glosses = load_glosses(dpath)
    print(f"glosses {len(glosses)}")
    print("parse sentences")
    sentences = load_sentences(spath)
    print(f"sentence lemmas {len(sentences)}")

    vocab = []
    sent_out = {}
    for row in load_wordhoard(zpath):
        rank = int(row["frequency_rank"])
        if rank > MAX_RANK:
            break
        pos = row["pos"]
        if pos not in CONTENT_POS:
            continue
        lemma = row["lemma"]
        parsed = parse_forms(row.get("forms") or "")
        gloss = glosses.get((lemma, pos)) or glosses.get((lemma, "VERB" if pos == "AUX" else pos)) or ""
        item = {
            "id": f"{lemma}|{pos}|{rank}",
            "lemma": lemma,
            "pos": pos,
            "gender": row.get("gender") or "",
            "rank": rank,
            "cefr": row.get("cefr_estimate") or "",
            "gloss": gloss,
            "plural": parsed["plural"][:2],
            "paradigms": parsed["paradigms"],
        }
        vocab.append(item)
        if lemma in sentences:
            sent_out[item["id"]] = sentences[lemma][:MAX_SENTENCES]

    DIST.mkdir(parents=True, exist_ok=True)
    (DIST / "vocab.json").write_text(
        json.dumps({"version": 1, "items": vocab}, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    (DIST / "sentences.json").write_text(
        json.dumps(sent_out, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    html = (WEB / "index.html").read_text(encoding="utf-8")
    (DIST / "index.html").write_text(html, encoding="utf-8")
    (DIST / "NOTICE.md").write_text((ROOT / "NOTICE.md").read_text(encoding="utf-8"), encoding="utf-8")
    (DIST / "LICENSE-DATA").write_text((ROOT / "LICENSE-DATA").read_text(encoding="utf-8"), encoding="utf-8")
    verbs = sum(1 for v in vocab if v["paradigms"])
    gloss_n = sum(1 for v in vocab if v["gloss"])
    print(f"vocab {len(vocab)} with gloss {gloss_n} with paradigm {verbs} sentences {len(sent_out)}")
    print(f"wrote {DIST}")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:
        print("build failed:", exc, file=sys.stderr)
        sys.exit(1)
