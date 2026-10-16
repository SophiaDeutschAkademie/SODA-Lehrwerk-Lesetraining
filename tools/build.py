#!/usr/bin/env python3
"""SODA LESETRAINING – erzeugt data/index.js und data/a1.js … data/c1.js aus src/texts/*.json.

Aufruf:  python3 tools/build.py
Vor dem Bauen wird tools/validate.py ausgeführt; bei Fehlern bricht das Skript ab.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "texts"
OUT = ROOT / "data"
ORDER = ["A1", "A2", "B1", "B2", "C1"]
WORD_RE = re.compile(r"[0-9A-Za-zÄÖÜäöüßÀ-ÿ]+(?:[-’'][0-9A-Za-zÄÖÜäöüßÀ-ÿ]+)*")


def main():
    if "--no-check" not in sys.argv:
        res = subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")], capture_output=True, text=True)
        if res.returncode != 0:
            print(res.stdout)
            print("Bauen abgebrochen: zuerst die Fehler beheben.")
            return 1
    texts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(SRC.glob("*.json"))]
    by_level = {lv: [] for lv in ORDER}
    for t in texts:
        t["words"] = len(WORD_RE.findall("\n".join(p["de"] for p in t["paragraphs"])))
        by_level[t["level"]].append(t)
    OUT.mkdir(exist_ok=True)
    index = {}
    digest = hashlib.sha1()
    for lv in ORDER:
        items = sorted(by_level[lv], key=lambda t: t["no"])
        index[lv] = [
            {k: t[k] for k in ("id", "no", "title", "titleKo", "type", "typeKo", "intro", "focus", "words")}
            | {"questions": len(t["questions"])}
            for t in items
        ]
        payload = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
        digest.update(payload.encode("utf-8"))
        (OUT / f"{lv.lower()}.js").write_text(
            f'(window.LESE_DATA=window.LESE_DATA||{{}})["{lv}"]={payload};\n', encoding="utf-8")
    (OUT / "index.js").write_text(
        'window.LESE_VERSION="' + digest.hexdigest()[:10] + '";\n' +
        "window.LESE_INDEX=" + json.dumps(index, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8")
    total = sum(len(v) for v in index.values())
    print("gebaut:", ", ".join(f"{lv} {len(index[lv])}" for lv in ORDER), f"(insgesamt {total})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
