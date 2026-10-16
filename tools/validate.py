#!/usr/bin/env python3
"""SODA LESETRAINING – Prüfskript für die Textdateien in src/texts/.

Aufruf:
    python3 tools/validate.py            # alle Texte prüfen
    python3 tools/validate.py a1-01 b2-03 # nur bestimmte Texte

Fehler (ERROR) müssen behoben werden, Hinweise (WARN) bitte prüfen.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "texts"

LEVELS = {
    "A1": dict(words=(90, 140), questions=6, grammar=3, vocab=12, phrases=3, mc=3, ngram=5),
    "A2": dict(words=(160, 240), questions=7, grammar=3, vocab=14, phrases=4, mc=3, ngram=5),
    "B1": dict(words=(260, 360), questions=8, grammar=4, vocab=16, phrases=5, mc=3, ngram=4),
    "B2": dict(words=(380, 500), questions=9, grammar=4, vocab=18, phrases=6, mc=3, ngram=4),
    "C1": dict(words=(520, 700), questions=10, grammar=4, vocab=20, phrases=8, mc=4, ngram=4),
}
KINDS = {"detail", "gist", "match", "paraphrase", "meaning", "intent", "inference"}
ROLES = {
    "주어", "동사", "동사(끝)", "4격 목적어", "3격 목적어", "2격 목적어", "전치사 목적어", "보어",
    "부사어", "부사어(시간)", "부사어(장소)", "부사어(방법)", "부사어(이유)", "부사어(빈도)",
    "부정어", "재귀대명사", "접속사", "접속부사", "의문사", "관계대명사", "종속절", "관계절",
    "zu 부정사구", "기타",
}
WORD_RE = re.compile(r"[0-9A-Za-zÄÖÜäöüßÀ-ÿ]+(?:[-’'][0-9A-Za-zÄÖÜäöüßÀ-ÿ]+)*")
HANGUL = re.compile(r"[가-힣]")


def words(text):
    return WORD_RE.findall(text)


def ngrams(tokens, n):
    return {" ".join(tokens[i:i + n]) for i in range(len(tokens) - n + 1)}


class Report:
    def __init__(self, tid):
        self.tid = tid
        self.errors = []
        self.warns = []

    def err(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


# ---------------------------------------------------------------- Korean style
def has_double_past(text):
    """'-었었-' 찾기: 받침 ㅆ인 음절 바로 뒤에 '었'이 오는 경우 (있었다의 '있었'은 제외)."""
    for i in range(len(text) - 1):
        a, b = text[i], text[i + 1]
        if b != "었" or not ("가" <= a <= "힣"):
            continue
        if (ord(a) - 0xAC00) % 28 == 20 and a != "있":
            return True
    return False


def option_length_problem(opts, ans):
    """Antwortoptionen sollen gleich lang wirken (die längste Option darf nicht die richtige verraten).

    Erlaubt: Unterschied höchstens 6 Zeichen oder höchstens 20 % (längste ÷ kürzeste ≤ 1,2).
    Die richtige Option darf die längste falsche nicht um mehr als 8 % (und mehr als 4 Zeichen) übertreffen.
    """
    lens = [len(o) for o in opts]
    lo, hi = min(lens), max(lens)
    if hi - lo > 6 and hi / lo > 1.2:
        return f"Optionslängen {lens} zu unterschiedlich (längste ÷ kürzeste = {hi / lo:.2f}, erlaubt ≤ 1,20 oder ≤ 6 Zeichen)"
    wrong = [n for k, n in enumerate(lens) if k != ans]
    if lens[ans] - max(wrong) > 4 and lens[ans] > 1.08 * max(wrong):
        return f"richtige Option ist mit {lens[ans]} Zeichen deutlich länger als jede falsche (max. {max(wrong)})"
    return None


SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+|\n+")


def check_korean(rep, where, text, allow_dict=False, para_style=None):
    if not isinstance(text, str):
        return
    if has_double_past(text):
        rep.err(f"{where}: '-었었-' (doppelte Vergangenheit) gefunden: {text[:60]}")
    if re.search(r"(?<!화법)조동사", text):
        rep.err(f"{where}: '조동사' außerhalb von '화법조동사': {text[:60]}")
    if allow_dict:
        return
    for sent in SENT_SPLIT.split(text.strip()):
        s = sent.strip()
        if not s or not HANGUL.search(s):
            continue
        core = re.sub(r"[\s.!?…\"'”’)\]」』]+$", "", s)
        if not core:
            continue
        if core.endswith("다") and not core.endswith(("니다", "습니다")):
            rep.err(f"{where}: Satz endet auf '-다' (반말/평서체): …{s[-30:]}")
            continue
        if para_style in ("h", "meta"):
            continue
        if core.endswith("까") and not core.endswith("니까"):
            rep.warn(f"{where}: Frage endet auf '-까' (반말?): '{core[-8:]}'")
            continue
        if core.endswith(("요", "니다", "니까")):
            continue
        m = re.search(r"(어|아|야|지|게|래|냐|자|네|군|해|돼|봐|줘|걸|니|데)$", core)
        if m and len(core) >= 2:
            rep.warn(f"{where}: Satzende klingt nach 반말 ('{core[-8:]}')")


# ---------------------------------------------------------------- German style
def check_german(rep, where, text, style=None):
    if '"' in text:
        rep.err(f"{where}: gerade Anführungszeichen \" – bitte „…“ verwenden")
    if re.search(r"\w[*:]innen|\wInnen\b", text):
        rep.err(f"{where}: Genderzeichen gefunden")
    if re.search(r"\s-\s", text):
        rep.warn(f"{where}: ' - ' als Gedankenstrich? Bitte ' – ' verwenden")
    if "  " in text:
        rep.warn(f"{where}: doppeltes Leerzeichen")
    if "..." in text:
        rep.warn(f"{where}: '...' – bitte '…' verwenden")
    if style not in ("h", "meta") and text and text.strip()[-1] not in ".!?…“:)–":
        rep.warn(f"{where}: Absatz endet ohne Satzzeichen")
    if re.search(r"[A-Za-zäöüß][.!?,;:][A-Za-zÄÖÜäöü]", text) and not re.search(r"(z\.B|d\.h|u\.a|bzw|ca|Nr|Dr|S\.|www\.|\.de|\.com|\d\.\d)", text):
        rep.warn(f"{where}: fehlendes Leerzeichen nach Satzzeichen?")


def occurrences(haystacks, needle):
    return sum(h.count(needle) for h in haystacks)


def validate_file(path):
    tid = path.stem
    rep = Report(tid)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa
        rep.err(f"JSON nicht lesbar: {e}")
        return rep

    # --- Kopf
    for key in ("id", "level", "no", "title", "titleKo", "type", "typeKo", "intro", "focus",
                "paragraphs", "questions", "grammar", "vocab", "phrases"):
        if key not in data:
            rep.err(f"Feld fehlt: {key}")
    if rep.errors:
        return rep
    if "_" in path.name:
        rep.err("Dateiname enthält '_'")
    level = data["level"]
    if level not in LEVELS:
        rep.err(f"unbekanntes Level {level}")
        return rep
    cfg = LEVELS[level]
    if data["id"] != tid:
        rep.err(f"id '{data['id']}' passt nicht zum Dateinamen '{tid}'")
    if not tid.startswith(level.lower() + "-"):
        rep.err("id passt nicht zum Level")
    try:
        if int(tid.split("-")[1]) != data["no"]:
            rep.err("no passt nicht zur id")
    except Exception:  # noqa
        rep.err("id-Format a1-01 erwartet")
    if not (2 <= len(data["focus"]) <= 4):
        rep.err("focus: 2–4 Einträge erwartet")
    if len(data["intro"]) > 80:
        rep.warn(f"intro ist lang ({len(data['intro'])} Zeichen)")
    check_korean(rep, "intro", data["intro"])
    check_korean(rep, "titleKo", data["titleKo"], para_style="h")
    for f in data["focus"]:
        check_korean(rep, "focus", f, allow_dict=True)
    check_german(rep, "title", data["title"], style="h")

    # --- Absätze
    paras = data["paragraphs"]
    if not paras:
        rep.err("keine Absätze")
        return rep
    des = []
    for i, p in enumerate(paras, 1):
        where = f"Absatz {i}"
        if "de" not in p or "ko" not in p or not p["de"].strip() or not p["ko"].strip():
            rep.err(f"{where}: de/ko fehlt")
            continue
        style = p.get("style")
        if style not in (None, "h", "q", "meta"):
            rep.err(f"{where}: unbekannter style {style}")
        for k in p:
            if k not in ("de", "ko", "label", "style"):
                rep.err(f"{where}: unbekanntes Feld {k}")
        check_german(rep, where, p["de"], style)
        check_korean(rep, where + " (ko)", p["ko"], para_style=style)
        des.append(p["de"])
    full = "\n".join(des)
    wc = len(words(full))
    lo, hi = cfg["words"]
    if not (lo <= wc <= hi):
        rep.err(f"Wortzahl {wc} außerhalb {lo}–{hi}")

    # --- Fragen
    qs = data["questions"]
    if len(qs) != cfg["questions"]:
        rep.err(f"{len(qs)} Fragen, erwartet {cfg['questions']}")
    tf_answers, mc_answers, longest_hits = [], [], []
    mc_total = sum(1 for q in qs if q.get("type") == "mc")
    for i, q in enumerate(qs, 1):
        where = f"Frage {i}"
        t = q.get("type")
        kind = q.get("kind", "detail")
        if t not in ("rf", "rfn", "mc"):
            rep.err(f"{where}: type {t}")
            continue
        if kind not in KINDS:
            rep.err(f"{where}: kind {kind}")
        if level in ("A1", "A2", "B1") and t == "rfn":
            rep.warn(f"{where}: rfn erst ab B2 vorgesehen")
        if level in ("B2", "C1") and t == "rf":
            rep.warn(f"{where}: ab B2 bitte rfn statt rf")
        if not q.get("q", "").strip():
            rep.err(f"{where}: q fehlt")
        check_german(rep, where + " q", q.get("q", ""), style="meta")
        ans = q.get("answer")
        if t == "mc":
            opts = q.get("options") or []
            if kind == "match":
                if not (3 <= len(opts) <= 6):
                    rep.err(f"{where}: match braucht 3–6 Optionen")
            elif len(opts) != cfg["mc"]:
                rep.err(f"{where}: {len(opts)} Optionen, erwartet {cfg['mc']}")
            if len(set(opts)) != len(opts):
                rep.err(f"{where}: doppelte Optionen")
            for o in opts:
                check_german(rep, where + " Option", o, style="meta")
            if not isinstance(ans, int) or not (0 <= ans < len(opts)):
                rep.err(f"{where}: answer außerhalb des Bereichs")
                continue
            if kind != "match":
                mc_answers.append(ans)
            problem = option_length_problem(opts, ans)
            if problem:
                rep.err(f"{where}: {problem}")
            lens = [len(o) for o in opts]
            if lens.count(max(lens)) == 1 and lens[ans] == max(lens):
                longest_hits.append(i)
            correct_text = opts[ans]
        else:
            if q.get("options"):
                rep.err(f"{where}: rf/rfn ohne options")
            n = 2 if t == "rf" else 3
            if not isinstance(ans, int) or not (0 <= ans < n):
                rep.err(f"{where}: answer außerhalb des Bereichs")
                continue
            tf_answers.append(ans)
            correct_text = q["q"] if ans == 0 else None
        ev = q.get("evidence")
        if ev is None:
            if not (t == "rfn" and ans == 2):
                rep.err(f"{where}: evidence fehlt (nur bei 'Text sagt dazu nichts' erlaubt)")
        else:
            c = occurrences(des, ev)
            if c == 0:
                rep.err(f"{where}: evidence nicht wörtlich im Text: „{ev[:70]}“")
            elif c > 1:
                rep.err(f"{where}: evidence kommt {c}× vor – bitte eindeutiger")
        if kind in ("paraphrase", "meaning"):
            quotes = re.findall(r"„([^“]+)“", q.get("q", ""))
            if not quotes:
                rep.err(f"{where}: {kind}-Frage braucht ein Zitat „…“ im Fragetext")
            for qu in quotes:
                if occurrences(des, qu) == 0:
                    rep.err(f"{where}: Zitat nicht wörtlich im Text: „{qu[:70]}“")
        pairs = q.get("pairs")
        if not isinstance(pairs, list):
            rep.err(f"{where}: pairs fehlt (Liste)")
        else:
            for pr in pairs:
                if not (isinstance(pr, list) and len(pr) == 2 and all(isinstance(x, str) and x.strip() for x in pr)):
                    rep.err(f"{where}: pairs-Eintrag muss [Text, Frage] sein")
                    continue
                if pr[0] not in full:
                    rep.warn(f"{where}: pairs-Textausdruck nicht wörtlich im Text: „{pr[0][:50]}“")
                hay = q.get("q", "") + " " + " ".join(q.get("options") or [])
                if pr[1] not in hay:
                    rep.warn(f"{where}: pairs-Frageausdruck nicht in Frage/Optionen: „{pr[1][:50]}“")
            if not pairs and kind in ("detail", "match", "paraphrase"):
                rep.warn(f"{where}: pairs leer")
        if not q.get("explain", "").strip():
            rep.err(f"{where}: explain fehlt")
        check_korean(rep, where + " explain", q.get("explain", ""))
        # Paraphrase-Kontrolle: richtige Aussage darf den Text nicht abschreiben
        if correct_text and kind not in ("meaning",):
            ct = [w.lower() for w in words(correct_text)]
            tt = [w.lower() for w in words(full)]
            n = cfg["ngram"]
            common = ngrams(ct, n) & ngrams(tt, n)
            if kind == "paraphrase":
                pass
            elif common:
                rep.warn(f"{where}: richtige Antwort übernimmt Textwortlaut: „{sorted(common)[0]}“")
    if tf_answers and len(set(tf_answers)) == 1 and len(tf_answers) > 2:
        rep.warn("alle R/F-Antworten gleich")
    if mc_answers and len(set(mc_answers)) == 1 and len(mc_answers) > 2:
        rep.warn("alle MC-Antworten an derselben Position")
    if mc_total >= 4 and len(longest_hits) * 2 > mc_total:
        rep.warn(f"richtige Option ist in {len(longest_hits)} von {mc_total} MC-Fragen die längste")

    # --- Grammatik
    gs = data["grammar"]
    if len(gs) != cfg["grammar"]:
        rep.err(f"{len(gs)} Grammatikpunkte, erwartet {cfg['grammar']}")
    with_parts = 0
    for i, g in enumerate(gs, 1):
        where = f"Grammatik {i}"
        for key in ("title", "term", "explain", "examples"):
            if not g.get(key):
                rep.err(f"{where}: {key} fehlt")
        check_korean(rep, where + " title", g.get("title", ""), para_style="h")
        check_korean(rep, where + " explain", g.get("explain", ""))
        if g.get("tip"):
            check_korean(rep, where + " tip", g["tip"])
        if g.get("pattern"):
            check_korean(rep, where + " pattern", g["pattern"], allow_dict=True)
        has_parts = False
        for j, ex in enumerate(g.get("examples", []), 1):
            w = f"{where} Bsp {j}"
            de = ex.get("de", "")
            if occurrences(des, de) == 0:
                rep.err(f"{w}: Beispiel nicht wörtlich im Text: „{de[:70]}“")
            if not ex.get("ko"):
                rep.err(f"{w}: ko fehlt")
            check_korean(rep, w + " ko", ex.get("ko", ""))
            for mk in ex.get("mark", []):
                if mk not in de:
                    rep.err(f"{w}: mark „{mk}“ nicht im Beispiel")
            parts = ex.get("parts")
            if parts:
                has_parts = True
                try:
                    joined = " ".join(p[0] for p in parts)
                except Exception:  # noqa
                    rep.err(f"{w}: parts-Format [[Teil, Rolle], …]")
                    continue
                if joined != de:
                    rep.err(f"{w}: parts ergeben nicht den Satz:\n      parts: {joined}\n      de:    {de}")
                for p in parts:
                    if len(p) != 2 or p[1] not in ROLES:
                        rep.err(f"{w}: unbekannte Rolle {p[1:] if len(p) > 1 else p}")
        if has_parts:
            with_parts += 1
        elif level in ("A1", "A2", "B1"):
            rep.err(f"{where}: A1–B1 braucht mindestens ein Beispiel mit parts")
    if level in ("B2", "C1") and with_parts < 2:
        rep.err("B2/C1: mindestens zwei Grammatikpunkte mit parts")

    # --- Wortschatz
    vs = data["vocab"]
    if len(vs) != cfg["vocab"]:
        rep.err(f"{len(vs)} Vokabeln, erwartet {cfg['vocab']}")
    seen = set()
    for i, v in enumerate(vs, 1):
        de, ko = v.get("de", ""), v.get("ko", "")
        if not de or not ko:
            rep.err(f"Vokabel {i}: de/ko fehlt")
            continue
        if de in seen:
            rep.err(f"Vokabel doppelt: {de}")
        seen.add(de)
        if re.match(r"^(der|die|das) ", de) and not re.search(r",|\((Pl|Sg)\.\)", de):
            rep.warn(f"Vokabel „{de}“: Pluralangabe fehlt")
        check_korean(rep, f"Vokabel {i}", ko, allow_dict=True)
        check_german(rep, f"Vokabel {i}", de, style="meta")
    ps = data["phrases"]
    if len(ps) != cfg["phrases"]:
        rep.err(f"{len(ps)} Ausdrücke, erwartet {cfg['phrases']}")
    for i, p in enumerate(ps, 1):
        w = f"Ausdruck {i}"
        for key in ("de", "ko", "ex", "exko"):
            if not p.get(key):
                rep.err(f"{w}: {key} fehlt")
        if p.get("ex") and occurrences(des, p["ex"]) == 0:
            rep.err(f"{w}: ex nicht wörtlich im Text: „{p['ex'][:70]}“")
        check_korean(rep, w + " ko", p.get("ko", ""), allow_dict=True)
        check_korean(rep, w + " exko", p.get("exko", ""))
        check_german(rep, w, p.get("de", ""), style="meta")
    return rep, wc


def main(argv):
    ids = argv[1:]
    files = sorted(SRC.glob("*.json"))
    if ids:
        files = [SRC / f"{i}.json" for i in ids]
    total_err = 0
    for f in files:
        if not f.exists():
            print(f"✗ {f.stem}: Datei fehlt")
            total_err += 1
            continue
        res = validate_file(f)
        if isinstance(res, tuple):
            rep, wc = res
        else:
            rep, wc = res, 0
        status = "✓" if not rep.errors else "✗"
        print(f"{status} {rep.tid}  ({wc} Wörter)  Fehler {len(rep.errors)} · Hinweise {len(rep.warns)}")
        for e in rep.errors:
            print(f"   ERROR {e}")
        for w in rep.warns:
            print(f"   WARN  {w}")
        total_err += len(rep.errors)
    print(f"\n{len(files)} Datei(en), {total_err} Fehler")
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
