# -*- coding: utf-8 -*-
"""data/explain.json -> data/explain.<lang>.js

Master format:
  { "<question id>": { "law": "art. 26 ust. 3 pkt 3 PoRD",
                       "text": { "pl": "...", "en": "...", "de": "...", "ua": "..." } } }

The law reference is shared across languages. A language may be missing; the site
falls back to the Polish text.
"""
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "data", "explain.json")
LANGS = ["pl", "en", "de", "ua"]


def main():
    master = json.load(io.open(SRC, encoding="utf-8"))
    for lang in LANGS:
        pack = {}
        for qid, rec in master.items():
            text = rec.get("text", {}).get(lang)
            if not text:
                continue
            entry = {"text": text}
            if rec.get("law"):
                entry["law"] = rec["law"]
            pack[qid] = entry
        out = os.path.join(ROOT, "data", "explain.%s.js" % lang)
        body = json.dumps(pack, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        with io.open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write("window.EXPLAIN=window.EXPLAIN||{};window.EXPLAIN.%s=%s;\n" % (lang, body))
        print("%s  %5d entries  %7.1f KB" % (lang, len(pack), os.path.getsize(out) / 1024.0))


if __name__ == "__main__":
    main()
