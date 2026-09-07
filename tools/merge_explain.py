# -*- coding: utf-8 -*-
"""Merge a batch file into data/explain.json, then rebuild the per-language packs.

    python tools/merge_explain.py batch.json

The batch has the same shape as the master. Existing ids are overwritten, so a
batch can also be used to correct earlier entries.
"""
import io
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(ROOT, "data", "explain.json")


def main():
    if len(sys.argv) < 2:
        print("usage: merge_explain.py batch.json")
        return 1
    batch = json.load(io.open(sys.argv[1], encoding="utf-8"))
    master = {}
    if os.path.exists(MASTER):
        master = json.load(io.open(MASTER, encoding="utf-8"))
    added = sum(1 for k in batch if k not in master)
    master.update(batch)
    with io.open(MASTER, "w", encoding="utf-8", newline="\n") as f:
        json.dump(master, f, ensure_ascii=False, indent=1, sort_keys=True)
    print("batch %d, new %d, master %d" % (len(batch), added, len(master)))

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import build_explain
    build_explain.main()
    return 0


if __name__ == "__main__":
    sys.exit(main())
