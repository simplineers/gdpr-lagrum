"""
statements.py — Genererar självständiga lagrum ur GDPR:s artikeltext.

Designbeslut (samtliga medvetna och dokumenterade i METOD.md):
  * Normtext återges ordagrant och obrutet. Infogade referenser läggs i
    avgränsade block EFTER normtexten, aldrig inne i den.
  * Rekursionsdjup 1. Referenser i infogad text redovisas i referenskedjan
    men infogas inte.
  * Referens till hel artikel/kapitel infogas inte, endast pekare med rubrik.
  * Externa instrument (direktiv, fördrag, stadgan m.m.) infogas aldrig.
  * Termer: artikel 4-definitioner för de termer som faktiskt förekommer.
"""
import re, json, csv, os
from collections import OrderedDict
import parse as P

OJ = "EUT L 119, 4.5.2016, s. 1"
RATT = "rättelse EUT L 127, 23.5.2018, s. 16"
KONS = "konsoliderad text CELEX 02016R0679-20160504 (SV)"

FORBEHALL = (
    "Utdraget avser ett enskilt lagrum i förordning (EU) 2016/679. Normtexten "
    "återges ordagrant. Förordningen ska tolkas som en helhet och mot bakgrund "
    "av sina skäl; utdraget ersätter inte en fullständig rättslig bedömning. "
    "Nationell rätt kan komplettera eller precisera tillämpningen."
)

# ----------------------------------------------------------------- index

class Reg:
    def __init__(self, arts):
        self.arts = {a["artikel"]: a for a in arts}
        self.punkt = {}
        self.led = {}
        self.artled = {}
        self.defs = {}
        for a in arts:
            n = a["artikel"]
            for p in a["punkter"]:
                self.punkt[(n, p["nr"])] = p
                for l in p["led"]:
                    if l["key"]:
                        self.led[(n, p["nr"], l["key"])] = l
            for it in a.get("listposter", []):
                if it["kind"] == "siffra":
                    self.defs[(n, it["key"])] = it
                elif it["kind"] == "bokstav":
                    self.artled[(n, it["key"])] = it

    def rubrik(self, n):
        a = self.arts.get(n)
        return a["rubrik"] if a else ""


# ----------------------------------------------------------------- referenser

TOKEN = r"\d+(?:\.\d+)*(?:\s+[a-zåäö](?![a-zåäö]))?"
# Bokstaven "i" är i svensk lagtext antingen ett led ("punkt 2 h, i eller j")
# eller prepositionen "i" ("punkt 1 i denna artikel"). Den räknas som led
# endast när nästa token inte är ett ord.
I_LED_OK = re.compile(r"^\s*(?:och|eller|samt|[,.;:)\]–—]|$)")


def strip_prep_i(expr, tail_after):
    """Tar bort ett avslutande ' i' som i själva verket är preposition."""
    m = re.search(r"\s+i$", expr)
    if m and not I_LED_OK.match(tail_after):
        return expr[:m.start()], True
    return expr, False
SEP = r"och|eller|samt|till|,|–|—|-"
ENUM = re.compile(rf"(?:\s*(?:{TOKEN}|{SEP}))+")
KW = re.compile(r"\b(artiklarna|artiklar|artikel|punkterna|punkter|punkt|leden|led)\b", re.I)
INTERNT_EFTER = re.compile(
    r"^\s+i\s+(?:denna förordning|den här förordningen|denna artikel|"
    r"den här artikeln|detta kapitel|det här kapitlet|denna punkt|"
    r"den här punkten|detta avsnitt|första stycket|andra stycket)", re.I)
EXT_CAP = re.compile(r"^\s+i\s+[A-ZÅÄÖ]")
EXT_WORD = re.compile(
    r"^\s+i\s+(?:direktiv|förordning|fördraget|fördragen|rådets|kommissionens|"
    r"stadgan|konvention|beslut|rekommendation|avtal|protokoll)\b", re.I)


def is_external(after):
    if INTERNT_EFTER.match(after):
        return False
    return bool(EXT_CAP.match(after) or EXT_WORD.match(after))
KAP = re.compile(r"\bkapitel\s+([IVX]+)\b", re.I)
INSTR_AKT = re.compile(
    r"^\s+i\s+((?:Europaparlamentets och rådets\s+|rådets\s+|kommissionens\s+)?"
    r"(?:direktiv|förordning|beslut|rekommendation)\s*"
    r"(?:\((?:EU|EG|EEG|Euratom)\)\s*)?(?:nr\s*)?\d+/\d+(?:/[A-Za-z]+)?)", re.I)
INSTR_TRAKTAT = re.compile(
    r"^\s+i\s+(EUF-fördraget|fördraget om Europeiska unionens funktionssätt|"
    r"fördraget om Europeiska unionen|Europeiska unionens stadga[^,.;]{0,40}|"
    r"stadgan|Europarådets konvention[^,.;]{0,60})", re.I)


def instrument_of(after):
    for rx in (INSTR_AKT, INSTR_TRAKTAT):
        m = rx.match(after)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
    m = re.match(r"^\s+i\s+([^,;.]{0,70})", after)
    t = (m.group(1) if m else "").strip()
    t = re.sub(r"\(\s*\d+\s*\)\s*$", "", t).strip()
    return t
VAG = [
    ("denna förordning", "hänvisar till förordningen som helhet"),
    ("den här förordningen", "hänvisar till förordningen som helhet"),
    ("unionsrätten", "hänvisar till unionsrätten utan angivet instrument"),
    ("medlemsstaternas nationella rätt", "hänvisar till nationell rätt utan angivet instrument"),
    ("nationell rätt", "hänvisar till nationell rätt utan angivet instrument"),
    ("denna artikel", "hänvisar till artikeln som helhet"),
    ("detta kapitel", "hänvisar till kapitlet som helhet"),
]

ROMAN_MAP = {}


def parse_refs(text, ctx_art, ctx_punkt):
    """Returnerar lista av referensobjekt i textordning."""
    refs = []
    for m in KW.finditer(text):
        kw = m.group(1).lower()
        tail = text[m.end():]
        em = ENUM.match(tail)
        if not em or not re.search(r"\d|[a-zåäö]", em.group(0)):
            continue
        expr = em.group(0)
        after = tail[em.end():]
        expr, dropped = strip_prep_i(expr, after)
        if dropped:
            after = " i" + after
        if not re.search(r"\d", expr):
            continue
        external = is_external(after)
        raw = (m.group(1) + expr).strip().rstrip(",").strip()
        raw = re.sub(r"\s+(och|eller|samt|till)$", "", raw).strip()
        if external:
            refs.append({"raw": raw, "typ": "externt",
                         "instrument": instrument_of(after), "mal": None})
            continue
        for tgt in expand(kw, expr, ctx_art, ctx_punkt):
            if tgt not in [r["mal"] for r in refs]:
                refs.append({"raw": raw, "typ": None, "mal": tgt})
    for km in KAP.finditer(text):
        refs.append({"raw": km.group(0), "typ": "pekare-kapitel",
                     "mal": ("kap", km.group(1).upper())})
    return refs


def expand(kw, expr, ctx_art, ctx_punkt):
    """Tolkar uppräkningen till konkreta mål."""
    items = re.findall(rf"{TOKEN}|–|—|till|-", expr)
    out = []
    last = None
    prev_num = None
    range_pending = False
    for it in items:
        it = it.strip()
        if it in ("–", "—", "till", "-"):
            range_pending = True
            continue
        mm = re.match(r"^(\d+(?:\.\d+)*)(?:\s+([a-zåäö]))?$", it)
        if not mm:
            continue
        num, letter = mm.group(1), mm.group(2)
        parts = num.split(".")
        if kw.startswith("artik"):
            art = int(parts[0])
            punkt = parts[1] if len(parts) > 1 else None
        elif kw.startswith("punkt"):
            art = ctx_art
            punkt = parts[0]
        else:  # led
            art, punkt = ctx_art, ctx_punkt
            letter = letter or num
            punkt = ctx_punkt
        if range_pending and prev_num is not None and kw.startswith("artik") and punkt is None:
            for k in range(prev_num + 1, art):
                out.append(("art", k, None, None))
        range_pending = False
        if kw.startswith("artik") and punkt is None:
            out.append(("art", art, None, None))
            prev_num = art
        else:
            out.append(("norm", art, punkt, letter))
            last = (art, punkt)
        if letter and not punkt and last:
            pass
    # bara-bokstav-fall: "artikel 6.1 a och e" -> andra token saknar siffra
    masked = re.sub(TOKEN, lambda m: " " * len(m.group(0)), expr)
    lone = [x for x in re.findall(r"(?<![\wåäö.])([a-zåäö])(?![a-zåäö])", masked)
            if x != "i"]
    if lone and out:
        base = [o for o in out if o[0] == "norm"]
        if base:
            _, a0, p0, _ = base[0]
            for L in lone:
                t = ("norm", a0, p0, L)
                if t not in out:
                    out.append(t)
    return out


# ----------------------------------------------------------------- termer

SUF = (r"(?:ernas|arnas|ornas|erna|arna|orna|ens|ets|nas|ans|as|es|ns|ts|"
       r"en|et|ar|er|or|na|s|n|t|e|a)?")
ALIAS = {
    "11": ["samtycke av den registrerade", "samtycke"],
    "6": ["register", "registret", "registren", "registrets"],
}


def build_terms(reg):
    terms = []
    for (art, key), it in sorted(reg.defs.items(), key=lambda x: int(x[0][1])):
        if art != 4:
            continue
        t = it["term"]
        if not t:
            continue
        forms = ALIAS.get(key, [t])
        pats = []
        for f in forms:
            words = [re.escape(w) for w in f.split()]
            words[-1] = words[-1] + SUF
            pats.append(r"\s+".join(words))
        rx = re.compile(r"(?<![\wåäöÅÄÖ-])(?:" + "|".join(pats) + r")(?![a-zåäöA-ZÅÄÖ-])",
                        re.IGNORECASE)
        terms.append({"ref": f"4.{key}", "term": t, "text": it["text"],
                      "text_md": it["text_md"], "rx": rx, "len": len(t)})
    terms.sort(key=lambda x: -x["len"])
    return terms


def find_terms(blocks, terms, self_ref):
    hay = " ".join(b["text"] for b in blocks)
    mask = [False] * len(hay)
    hits = []
    for t in terms:
        if t["ref"] == self_ref:
            continue
        for m in t["rx"].finditer(hay):
            if any(mask[m.start():m.end()]):
                continue
            for i in range(m.start(), m.end()):
                mask[i] = True
            hits.append(t)
            break
    hits.sort(key=lambda x: (int(x["ref"].split(".")[1])))
    return hits


# ----------------------------------------------------------------- uttalanden

def niva_label(art, punkt, led, kind):
    s = f"artikel {art}"
    if punkt:
        s += f".{punkt}"
    if led:
        s += f" led {led}"
    if kind == "definition":
        s = f"artikel 4.{punkt} (definition)"
    return s


def blocks_for_target(reg, tgt):
    """Textblock för en infogad referens."""
    kind = tgt[0]
    if kind == "art":
        return None
    _, art, punkt, led = tgt
    if art == 4 and punkt and not led and (4, punkt) in reg.defs:
        d = reg.defs[(4, punkt)]
        return [{"label": f"artikel 4.{punkt}", "text": d["text"], "text_md": d["text_md"]}]
    if punkt and led:
        p = reg.punkt.get((art, punkt))
        l = reg.led.get((art, punkt, led))
        if not l:
            return None
        out = []
        if p and p["chapeau"]:
            out.append({"label": f"artikel {art}.{punkt} inledning",
                        "text": p["chapeau"], "text_md": p["chapeau_md"]})
        out.append({"label": f"artikel {art}.{punkt} led {led}",
                    "text": l["text"], "text_md": l["text_md"]})
        return out
    if punkt:
        p = reg.punkt.get((art, punkt))
        if not p:
            return None
        out = []
        if p["text"]:
            out.append({"label": f"artikel {art}.{punkt}",
                        "text": p["text"], "text_md": p["text_md"]})
        else:
            if p["chapeau"]:
                out.append({"label": f"artikel {art}.{punkt} inledning",
                            "text": p["chapeau"], "text_md": p["chapeau_md"]})
            for l in p["led"]:
                out.append({"label": f"led {l['marker']}" if l["key"] else l["marker"],
                            "text": l["text"], "text_md": l["text_md"]})
        for s in p["avslut"]:
            out.append({"label": f"artikel {art}.{punkt} avslutande stycke",
                        "text": s["text"], "text_md": s["text_md"]})
        return out
    return None


def scope_of(st):
    return (st["artikel"], st.get("punkt"), st.get("led"))


def resolve(reg, st, terms, chapters):
    blocks = st["normtext"]
    hay = " ".join(b["text"] for b in blocks)
    raw = parse_refs(hay, st["artikel"], st.get("punkt"))
    seen, refs, chain = set(), [], []
    a, p, l = scope_of(st)
    for r in raw:
        if r["typ"] == "externt":
            k = ("ext", r["raw"], r["instrument"])
            if k in seen:
                continue
            seen.add(k)
            refs.append({"referens": r["raw"], "typ": "externt",
                         "instrument": r["instrument"],
                         "not": "Externt instrument – återges inte här."})
            continue
        tgt = r["mal"]
        if tgt[0] == "kap":
            k = ("kap", tgt[1])
            if k in seen:
                continue
            seen.add(k)
            refs.append({"referens": r["raw"], "typ": "pekare",
                         "mal": f"kapitel {tgt[1]}",
                         "rubrik": chapters.get(tgt[1], ""),
                         "not": "Hänvisning till helt kapitel – återges inte i sin helhet."})
            continue
        if tgt[0] == "art":
            n = tgt[1]
            if n == a:
                continue
            k = ("art", n)
            if k in seen:
                continue
            seen.add(k)
            refs.append({"referens": r["raw"], "typ": "pekare",
                         "mal": f"artikel {n}", "rubrik": reg.rubrik(n),
                         "not": "Hänvisning till hel artikel – återges inte i sin helhet."})
            continue
        _, ta, tp, tl = tgt
        if (ta, tp, tl) == (a, p, l):
            continue
        if ta == a and tp == p and tl is None:
            continue  # samma punkt: redan i normtexten
        k = ("norm", ta, tp, tl)
        if k in seen:
            continue
        seen.add(k)
        bl = blocks_for_target(reg, tgt)
        if bl is None:
            refs.append({"referens": r["raw"], "typ": "pekare",
                         "mal": niva_label(ta, tp, tl, ""),
                         "rubrik": reg.rubrik(ta),
                         "not": "Målet kunde inte upplösas till en enskild bestämmelse."})
            continue
        refs.append({"referens": r["raw"], "typ": "infogad",
                     "mal": niva_label(ta, tp, tl, ""),
                     "artikelrubrik": reg.rubrik(ta), "block": bl})
        subhay = " ".join(b["text"] for b in bl)
        for phrase, note in VAG:
            if re.search(r"(?<![\wåäö])" + re.escape(phrase), subhay, re.I):
                chain.append(f"{niva_label(ta,tp,tl,'')} → ”{phrase}” (vag hänvisning)")
        sub = parse_refs(subhay, ta, tp)
        for s in sub:
            if s["typ"] == "externt":
                chain.append(f"{niva_label(ta,tp,tl,'')} → {s['raw']} (externt)")
            elif s["mal"][0] == "art":
                chain.append(f"{niva_label(ta,tp,tl,'')} → artikel {s['mal'][1]}")
            elif s["mal"][0] == "kap":
                chain.append(f"{niva_label(ta,tp,tl,'')} → kapitel {s['mal'][1]}")
            else:
                _, sa, sp, sl = s["mal"]
                chain.append(f"{niva_label(ta,tp,tl,'')} → {niva_label(sa,sp,sl,'')}")
    helpunkt = {(r["mal"],) for r in refs
                if r["typ"] == "infogad" and " led " not in r["mal"]}
    refs = [r for r in refs
            if not (r["typ"] == "infogad" and " led " in r["mal"]
                    and (r["mal"].split(" led ")[0],) in helpunkt)]

    merged, byraw = [], {}
    for r in refs:
        if r["typ"] != "pekare":
            merged.append(r); continue
        k = r["referens"]
        if k in byraw:
            byraw[k]["mal_lista"].append({"mal": r.get("mal"), "rubrik": r.get("rubrik", "")})
        else:
            nr = {"referens": k, "typ": "pekare", "not": r.get("not", ""),
                  "mal_lista": [{"mal": r.get("mal"), "rubrik": r.get("rubrik", "")}]}
            byraw[k] = nr
            merged.append(nr)
    refs = merged

    vag = []
    for phrase, note in VAG:
        if re.search(r"(?<![\wåäö])" + re.escape(phrase), hay, re.I):
            vag.append({"uttryck": phrase, "not": note})
    st["referenser"] = refs
    st["vaga_hanvisningar"] = vag
    egen = niva_label(a, p, l, "")
    chain = [c for c in chain if not c.endswith("→ " + egen)]
    st["referenskedja"] = list(OrderedDict.fromkeys(chain))
    allb = list(blocks) + [b for r in refs if r["typ"] == "infogad" for b in r["block"]]
    st["termer"] = [{"ref": t["ref"], "term": t["term"], "text": t["text"],
                     "text_md": t["text_md"]}
                    for t in find_terms(allb, terms, st.get("self_term_ref"))]
    return st


def generate():
    arts = P.parse()
    reg = Reg(arts)
    terms = build_terms(reg)
    chapters = {}
    for a in arts:
        if a["kapitel"]:
            m = re.match(r"KAPITEL\s+([IVX]+)\s+–\s+(.*)", a["kapitel"])
            if m:
                chapters[m.group(1)] = m.group(2)

    sts = []
    for a in arts:
        n = a["artikel"]
        base = {"kapitel": a["kapitel"], "avsnitt": a["avsnitt"],
                "artikel": n, "artikelrubrik": a["rubrik"]}

        for d in a.get("listposter", []):
            if d["kind"] == "siffra":
                bl = []
                if a["chapeau"]:
                    bl.append({"label": f"artikel {n} inledning",
                               "text": a["chapeau"], "text_md": a["chapeau_md"]})
                bl.append({"label": f"artikel {n}.{d['key']}",
                           "text": d["text"], "text_md": d["text_md"]})
                for s in d["sub"]:
                    bl.append({"label": f"led {s['marker']}",
                               "text": s["text"], "text_md": s["text_md"]})
                sts.append(dict(base, id=f"GDPR-{n}.{d['key']}", punkt=d["key"], led=None,
                                nivatyp="definition" if n == 4 else "punkt",
                                niva=(f"artikel {n}.{d['key']}"
                                      + (f" – definition av ”{d['term']}”" if d["term"] else "")),
                                normtext=bl, prov=d["prov"],
                                self_term_ref=f"4.{d['key']}" if n == 4 else None))
            elif d["kind"] == "bokstav":
                bl = []
                if a["chapeau"] or a["stycken"]:
                    ch = a["chapeau"] or a["stycken"][0]["text"]
                    chm = a["chapeau_md"] or a["stycken"][0]["text_md"]
                    bl.append({"label": f"artikel {n} inledning", "text": ch, "text_md": chm})
                bl.append({"label": f"artikel {n} led {d['key']}",
                           "text": d["text"], "text_md": d["text_md"]})
                sts.append(dict(base, id=f"GDPR-{n}.{d['key']}", punkt=None, led=d["key"],
                                nivatyp="led", niva=f"artikel {n} led {d['key']}",
                                normtext=bl, prov=d["prov"], self_term_ref=None))

        if not a["punkter"] and not a.get("listposter") and a["stycken"]:
            bl = [{"label": f"artikel {n}" + (f", {i+1}:a stycket" if len(a["stycken"]) > 1 else ""),
                   "text": s["text"], "text_md": s["text_md"]}
                  for i, s in enumerate(a["stycken"])]
            sts.append(dict(base, id=f"GDPR-{n}", punkt=None, led=None,
                            nivatyp="artikel", niva=f"artikel {n}",
                            normtext=bl, prov=a["prov"], self_term_ref=None))

        for p in a["punkter"]:
            if not p["led"]:
                bl = [{"label": f"artikel {n}.{p['nr']}", "text": p["text"],
                       "text_md": p["text_md"]}]
                for s in p["avslut"]:
                    bl.append({"label": f"artikel {n}.{p['nr']} avslutande stycke",
                               "text": s["text"], "text_md": s["text_md"]})
                sts.append(dict(base, id=f"GDPR-{n}.{p['nr']}", punkt=p["nr"], led=None,
                                nivatyp="punkt", niva=f"artikel {n}.{p['nr']}",
                                normtext=bl, prov=p["prov"], self_term_ref=None))
                continue
            strecksats = all(not l["key"] for l in p["led"])
            if strecksats:
                bl = []
                if p["chapeau"]:
                    bl.append({"label": f"artikel {n}.{p['nr']} inledning",
                               "text": p["chapeau"], "text_md": p["chapeau_md"]})
                for l in p["led"]:
                    bl.append({"label": "strecksats", "text": l["text"],
                               "text_md": l["text_md"]})
                for s in p["avslut"]:
                    bl.append({"label": f"artikel {n}.{p['nr']} avslutande stycke",
                               "text": s["text"], "text_md": s["text_md"]})
                sts.append(dict(base, id=f"GDPR-{n}.{p['nr']}", punkt=p["nr"], led=None,
                                nivatyp="punkt", niva=f"artikel {n}.{p['nr']}",
                                normtext=bl, prov=p["prov"], self_term_ref=None))
                continue
            for l in p["led"]:
                bl = []
                if p["chapeau"]:
                    bl.append({"label": f"artikel {n}.{p['nr']} inledning",
                               "text": p["chapeau"], "text_md": p["chapeau_md"]})
                bl.append({"label": f"artikel {n}.{p['nr']} led {l['key']}",
                           "text": l["text"], "text_md": l["text_md"]})
                for s in l["sub"]:
                    bl.append({"label": f"led {l['key']} {s['marker']}",
                               "text": s["text"], "text_md": s["text_md"]})
                for s in p["avslut"]:
                    bl.append({"label": f"artikel {n}.{p['nr']} avslutande stycke",
                               "text": s["text"], "text_md": s["text_md"]})
                sts.append(dict(base, id=f"GDPR-{n}.{p['nr']}.{l['key']}",
                                punkt=p["nr"], led=l["key"], nivatyp="led",
                                niva=f"artikel {n}.{p['nr']} led {l['key']}",
                                normtext=bl, prov=l["prov"], self_term_ref=None))

    for st in sts:
        resolve(reg, st, terms, chapters)
        st["proveniens"] = {
            "autentisk_kalla": OJ,
            "lydelse": ("originallydelse" if st["prov"] == "B"
                        else f"ändrad lydelse enligt {RATT}"),
            "markor": "▼" + st["prov"],
            "barare": KONS,
        }
        st["forbehall"] = FORBEHALL
        st.pop("self_term_ref", None)
        st.pop("prov", None)
    return sts, reg, chapters


if __name__ == "__main__":
    sts, reg, ch = generate()
    print("lagrum:", len(sts))
    from collections import Counter
    print(Counter(s["nivatyp"] for s in sts))
    out = os.environ.get("GDPR_OUT", "dist")
    os.makedirs(out, exist_ok=True)
    json.dump(sts, open(f"{out}/statements.json", "w"),
              ensure_ascii=False, indent=1)
    s = [x for x in sts if x["id"] == "GDPR-5.1.b"][0]
    print(json.dumps(s, ensure_ascii=False, indent=1)[:3000])
