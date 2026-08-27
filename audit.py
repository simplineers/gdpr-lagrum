"""
audit.py — Kvalitetsgranskning av lagrummen.

Kompletterar verify.py och final_check.py. Dessa bevisar att ordalydelsen är
ordagrann. Detta skript prövar tre andra frågor:

  1. Täckning: hamnar varje textnod i källträdet i minst ett lagrum, eller
     tappas något tyst på vägen?
  2. Självständighet: går varje lagrum att läsa utan lagboken, dvs upplöses
     varje hänvisning i texten till infogad text eller pekare?
  3. Struktur och typografi: stämmer id mot nivåfälten, finns
     extraktionsartefakter kvar?
"""
import re, sys, collections
import parse as P
import statements as S

fel = []
varn = []


def F(kat, txt):
    fel.append((kat, txt))


def V(kat, txt):
    varn.append((kat, txt))


def rubrik(t):
    print(f"\n{'=' * 72}\n{t}\n{'=' * 72}")


arts = P.parse()
sts, reg, chapters = S.generate()
by_id = {s["id"]: s for s in sts}
ids = set(by_id)

# ---------------------------------------------------------------- 1. täckning

rubrik("1. TÄCKNING — hamnar varje textnod i minst ett lagrum?")

leaves = []          # (beskrivning, text)
for a in arts:
    n = a["artikel"]
    if a["chapeau"]:
        leaves.append((f"art {n} chapeau", a["chapeau"]))
    for i, s in enumerate(a["stycken"]):
        leaves.append((f"art {n} stycke {i + 1}", s["text"]))
    for d in a.get("listposter", []):
        leaves.append((f"art {n} listpost {d['marker']}", d["text"]))
        for sub in d["sub"]:
            leaves.append((f"art {n} listpost {d['marker']}{sub['marker']}",
                           sub["text"]))
    for p in a["punkter"]:
        if p["text"]:
            leaves.append((f"art {n}.{p['nr']}", p["text"]))
        if p["chapeau"]:
            leaves.append((f"art {n}.{p['nr']} chapeau", p["chapeau"]))
        for l in p["led"]:
            leaves.append((f"art {n}.{p['nr']} {l['marker']}", l["text"]))
            for sub in l["sub"]:
                leaves.append(
                    (f"art {n}.{p['nr']} {l['marker']}{sub['marker']}",
                     sub["text"]))
        for i, s in enumerate(p["avslut"]):
            leaves.append((f"art {n}.{p['nr']} avslut {i + 1}", s["text"]))

norm_texts = collections.Counter()
for s in sts:
    for b in s["normtext"]:
        norm_texts[b["text"]] += 1

saknas = [(d, t) for d, t in leaves if t and t not in norm_texts]
print(f"textnoder i källträdet: {len(leaves)}")
print(f"unika normtextblock i lagrummen: {len(norm_texts)}")
print(f"noder som INTE finns i något lagrum: {len(saknas)}")
for d, t in saknas[:15]:
    F("täckning", f"{d}: {t[:90]!r}")
    print(f"  ! {d}: {t[:90]!r}")

# omvänt: normtext som inte finns i trädet (ska vara noll)
leaf_set = {t for _, t in leaves if t}
extra = [t for t in norm_texts if t not in leaf_set]
print(f"normtextblock som inte finns i källträdet: {len(extra)}")
for t in extra[:5]:
    F("täckning", f"okänt block: {t[:90]!r}")

# ---------------------------------------------------- 2. självständighet

rubrik("2. SJÄLVSTÄNDIGHET — upplöses varje hänvisning i normtexten?")

CUE = re.compile(r"\b(artiklarna|artikel|punkterna|punkt|leden|led|kapitel|"
                 r"avsnitt|stycket|stycke)\b", re.I)

oupplost = []
for s in sts:
    hay = " ".join(b["text"] for b in s["normtext"])
    if not CUE.search(hay):
        continue
    raw = S.parse_refs(hay, s["artikel"], s.get("punkt"))
    redovisade = set()
    for r in s["referenser"]:
        if r["typ"] == "infogad":
            redovisade.add(r["mal"])
        elif r["typ"] == "pekare":
            for m in r["mal_lista"]:
                redovisade.add(m["mal"])
        else:
            redovisade.add(r["referens"])
    a, p, l = s["artikel"], s.get("punkt"), s.get("led")
    for r in raw:
        if r["typ"] == "externt":
            if r["raw"] not in redovisade:
                oupplost.append((s["id"], r["raw"], "externt ej redovisat"))
            continue
        t = r["mal"]
        if t[0] == "kap":
            if f"kapitel {t[1]}" not in redovisade:
                oupplost.append((s["id"], r["raw"], f"kapitel {t[1]}"))
            continue
        if t[0] == "art":
            if t[1] == a:
                continue
            if f"artikel {t[1]}" not in redovisade:
                oupplost.append((s["id"], r["raw"], f"artikel {t[1]}"))
            continue
        _, ta, tp, tl = t
        if (ta, tp, tl) == (a, p, l):
            continue
        if ta == a and tp == p and tl is None:
            continue
        lbl = S.niva_label(ta, tp, tl, "")
        if lbl not in redovisade and lbl.split(" led ")[0] not in redovisade:
            oupplost.append((s["id"], r["raw"], lbl))

print(f"oupplösta hänvisningar: {len(oupplost)}")
for sid, raw, mal in oupplost[:20]:
    F("självständighet", f"{sid}: ”{raw}” -> {mal}")
    print(f"  ! {sid}: ”{raw}” -> {mal}")

# led måste ärva punktens inledning
utan_inledning = [s["id"] for s in sts if s["nivatyp"] == "led"
                  and s.get("punkt")
                  and not any("inledning" in b["label"]
                              for b in s["normtext"])]
print(f"led-lagrum utan ärvd punktinledning: {len(utan_inledning)}")
for i in utan_inledning[:10]:
    p = S.Reg(arts).punkt.get((by_id[i]["artikel"], by_id[i]["punkt"]))
    if p and p["chapeau"]:
        F("självständighet", f"{i}: punkten har inledning men den ärvdes inte")
        print(f"  ! {i}: punkten HAR inledning men den ärvdes inte")

# mål för infogade referenser ska motsvara verkliga lagrum
saknade_mal = []
for s in sts:
    for r in s["referenser"]:
        if r["typ"] != "infogad":
            continue
        m = re.match(r"^artikel (\d+)\.(\d+)(?: led ([a-zåäö]))?$", r["mal"])
        if not m:
            saknade_mal.append((s["id"], r["mal"], "oväntat målformat"))
            continue
        cand = f"GDPR-{m.group(1)}.{m.group(2)}" + (
            f".{m.group(3)}" if m.group(3) else "")
        # En punkt som är indelad i led har inget eget lagrum-id; leden bär
        # id:na. Målet är då giltigt om något led-lagrum finns.
        barn = f"GDPR-{m.group(1)}.{m.group(2)}."
        if cand not in ids and not any(i.startswith(barn) for i in ids):
            saknade_mal.append((s["id"], r["mal"], f"{cand} finns inte"))
print(f"infogade mål utan motsvarande lagrum: {len(saknade_mal)}")
for sid, mal, why in saknade_mal[:10]:
    V("mål", f"{sid}: {mal} — {why}")
    print(f"  ~ {sid}: {mal} — {why}")

# ---------------------------------------------------- 3. struktur

rubrik("3. STRUKTUR — id, nivåfält och rubriker")

for s in sts:
    exp = f"GDPR-{s['artikel']}"
    if s["punkt"]:
        exp += f".{s['punkt']}"
    if s["led"]:
        exp += f".{s['led']}" if s["punkt"] else f".{s['led']}"
    if s["id"] != exp:
        F("struktur", f"{s['id']}: id stämmer inte mot fälten (väntat {exp})")
    if not s["artikelrubrik"]:
        F("struktur", f"{s['id']}: artikelrubrik saknas")
    if not s["kapitel"]:
        F("struktur", f"{s['id']}: kapitel saknas")
    if not s["normtext"]:
        F("struktur", f"{s['id']}: normtext saknas")
    for b in s["normtext"]:
        if not b["text"].strip():
            F("struktur", f"{s['id']}: tomt normtextblock {b['label']!r}")

dubbletter = [t for t, c in norm_texts.items() if c > 1]
print(f"normtextblock som förekommer i flera lagrum: {len(dubbletter)}")
print("  (förväntat: punktinledningar som ärvs av flera led)")
misstankta = [t for t in dubbletter
              if not any(t == p["chapeau"] for a in arts for p in a["punkter"])
              and not any(t == a["chapeau"] for a in arts)
              and not any(t == s["text"] for a in arts for p in a["punkter"]
                          for s in p["avslut"])]
print(f"  varav inte inledning eller avslutande stycke: {len(misstankta)}")
print("  (art. 13, 14 och 15 upprepar samma informationskrav ordagrant;")
print("   identisk text i skilda lagrum med skilda id är korrekt)")
for t in misstankta[:3]:
    print(f"    {t[:80]!r}")

c = collections.Counter(s["nivatyp"] for s in sts)
print(f"nivåtyper: {dict(c)}")
print(f"artiklar utan lagrum: "
      f"{sorted({a['artikel'] for a in arts} - {s['artikel'] for s in sts})}")

# ---------------------------------------------------- 4. typografi

rubrik("4. TYPOGRAFI — extraktionsartefakter")

ARTEFAKT = {
    "hårt blanksteg kvar": "\u00a0",
    "ändringsmarkör i text": "▼",
    "dubbelt blanksteg": "  ",
    "ensam asterisk": None,
}
alla_block = [(s["id"], b["label"], b["text"], b["text_md"])
              for s in sts for b in s["normtext"]]
alla_block += [(s["id"], b["label"], b["text"], b["text_md"])
               for s in sts for r in s["referenser"]
               for b in r.get("block", [])]
alla_block += [(s["id"], f"term {t['ref']}", t["text"], t["text_md"])
               for s in sts for t in s["termer"]]

for namn, needle in ARTEFAKT.items():
    if needle:
        träff = [(i, lb) for i, lb, t, _ in alla_block if needle in t]
    elif namn.startswith("ensam"):
        träff = [(i, lb) for i, lb, _, md in alla_block
                 if md.count("*") % 2]
    else:
        träff = []
    status = "ok" if not träff else f"{len(träff)} träffar"
    print(f"  {namn:26s} {status}")
    if träff:
        V("typografi", f"{namn}: {träff[:3]}")
        for i, lb in träff[:3]:
            print(f"      {i} / {lb}")

print()
oupplosta_fn = []
for s in sts:
    hay = " ".join([b["text"] for b in s["normtext"]]
                   + [b["text"] for r in s["referenser"]
                      if r["typ"] == "infogad" for b in r["block"]])
    nrs = set(re.findall(r"\(\s*(\d+)\s*\)", hay))
    lösta = {f["markor"].strip("()") for f in s.get("fotnoter", [])}
    for n in nrs - lösta:
        oupplosta_fn.append((s["id"], n))
print(f"  fotnotsmarkörer utan upplöst fotnot: {len(oupplosta_fn)}")
for sid, n in oupplosta_fn[:8]:
    F("fotnot", f"{sid}: markör ({n}) saknar fotnotstext")
    print(f"      ! {sid}: ({n})")
med = sum(1 for s in sts if s.get("fotnoter"))
print(f"  lagrum med upplöst fotnot: {med}")

# ---------------------------------------------------- 5. termer

rubrik("5. TERMER — missade böjningsformer")

# Grov delstrangssokning ger bara brus. Istallet provas formulerade varianter
# for de flerordiga termerna, dar attributet kongruensbojs.
VARIANT = {
    "4.3":  r"begränsning(?:en|ar|arna)?\s+av\s+behandling",
    "4.10": r"tredje\s+part",
    "4.15": r"uppgifter(?:na)?\s+om\s+hälsa",
    "4.16": r"huvudsaklig(?:t|a|e)?\s+verksamhetsställe",
    "4.20": r"bindande\s+företagsbestämmelser",
    "4.22": r"berörd(?:a|e|t)?\s+tillsynsmyndighet",
    "4.23": r"gränsöverskridande\s+behandling",
    "4.24": r"relevant(?:a|)\s+och\s+motiverad(?:e|)\s+invändning",
    "4.25": r"informationssamhällets\s+tjänster",
    "4.26": r"internationell(?:a|t)?\s+organisation",
}
missade = []
for s in sts:
    inj = {t["ref"] for t in s["termer"]}
    egen = f"4.{s['punkt']}" if s["artikel"] == 4 and s["punkt"] else None
    hay = " ".join(b["text"] for b in s["normtext"]) + " " + " ".join(
        b["text"] for r in s["referenser"] if r["typ"] == "infogad"
        for b in r["block"])
    for ref, pat in VARIANT.items():
        if ref in inj or ref == egen:
            continue
        if re.search(pat, hay, re.I):
            missade.append((s["id"], ref))
print(f"lagrum där en flerordig term förekommer men inte injicerats: "
      f"{len(missade)}")
for sid, ref in missade[:12]:
    F("termer", f"{sid}: {ref} förekommer i texten men injicerades inte")
    print(f"  ! {sid}: {ref}")

# ---------------------------------------------------- summering

rubrik("SUMMERING")
print(f"FEL:       {len(fel)}")
print(f"VARNINGAR: {len(varn)}")
for kat, txt in fel[:20]:
    print(f"  FEL  [{kat}] {txt}")
kat_v = collections.Counter(k for k, _ in varn)
for k, v in kat_v.most_common():
    print(f"  varn [{k}] {v} st")
sys.exit(1 if fel else 0)
