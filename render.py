"""
render.py — Renderar lagrummen till fyra utgåvor:

  dist/gdpr-lagrum-v1.0.md     samlingsdokument, alla lagrum
  dist/gdpr-lagrum-v1.0.json   strukturerad utgåva
  dist/gdpr-lagrum-v1.0.csv    platt utgåva, en rad per lagrum
  lagrum/artikel-NN/GDPR-*.md  ett lagrum per fil, versionshanterade

Normtext och infogad text ligger alltid i blockcitat, en rad per block, så att
ordalydelsen kan extraheras och verifieras maskinellt i samtliga utgåvor.

lagrum/ töms och byggs om vid varje körning. Lägg inga handskrivna filer där.
"""
import json, csv, os, re, shutil
from statements import generate, OJ, RATT, RATTELSER, KONS, FORBEHALL

OUT = os.environ.get("GDPR_OUT", "dist")
LAGRUM = os.environ.get("GDPR_LAGRUM", "lagrum")
BASENAME = "gdpr-lagrum-v1.0"
REPO_URL = "https://github.com/simplineers/gdpr-lagrum"


# ----------------------------------------------------------------- hjälpare

def q(text):
    return "> " + text.replace("\n", " ")


def sortkey(s):
    return (s["artikel"], int(s["punkt"]) if s["punkt"] else 0, s["led"] or "")


def artdir(n):
    return f"artikel-{n:02d}"


def relpath(s):
    return f"{artdir(s['artikel'])}/{s['id']}.md"


def esc(t):
    return t.replace("|", "\\|")


# ----------------------------------------------------------------- lagrumsblock

def body_md(s, md=True, heading=2):
    """Lagrummets innehåll utan rubrikrad. Delas av alla utgåvor."""
    k = "text_md" if md else "text"
    h = "#" * (heading + 1)
    L = [f"**Kapitel:** {s['kapitel'] or '—'}  "]
    if s["avsnitt"]:
        L.append(f"**Avsnitt:** {s['avsnitt']}  ")
    L.append(f"**Artikel:** {s['artikel']} – {s['artikelrubrik']}  ")
    L.append(f"**Nivå:** {s['niva']}  ")
    p = s["proveniens"]
    L.append(f"**Proveniens:** {p['autentisk_kalla']}, {p['lydelse']} "
             f"({p['markor']}). Bärare: {p['barare']}.")
    L += ["", f"{h} Normtext (ordagrant)", ""]
    for b in s["normtext"]:
        L += [f"*{b['label']}*", "", q(b[k]), ""]

    inf = [r for r in s["referenser"] if r["typ"] == "infogad"]
    for i, r in enumerate(inf, 1):
        L += [f"{h} Infogad referens [{i}/{len(inf)}] — {r['mal']}", "",
              f"Hänvisning i normtexten: ”{r['referens']}”. "
              f"Artikelns rubrik: {r['artikelrubrik']}.", ""]
        for b in r["block"]:
            L += [f"*{b['label']}*", "", q(b[k]), ""]

    if s["termer"]:
        L += [f"{h} Termer — artikel 4 (ordagrant)", "",
              "Artikel 4 inledning:", "", q("I denna förordning avses med"), ""]
        for t in s["termer"]:
            L += [f"*artikel {t['ref']}*", "", q(t[k]), ""]

    pek = [r for r in s["referenser"] if r["typ"] == "pekare"]
    if pek:
        L += [f"{h} Pekare (återges inte i sin helhet)", ""]
        for r in pek:
            for m in r["mal_lista"]:
                rub = f" – {m['rubrik']}" if m["rubrik"] else ""
                L.append(f"- {m['mal']}{rub}  ·  hänvisning: ”{r['referens']}”")
        L.append("")

    ext = [r for r in s["referenser"] if r["typ"] == "externt"]
    if ext:
        L += [f"{h} Externa instrument (återges inte)", ""]
        L += [f"- ”{r['referens']}” i {r['instrument']}" for r in ext]
        L.append("")

    if s["vaga_hanvisningar"]:
        L += [f"{h} Vaga hänvisningar", ""]
        L += [f"- ”{v['uttryck']}” — {v['not']}" for v in s["vaga_hanvisningar"]]
        L.append("")

    if s["referenskedja"]:
        L += [f"{h} Referenskedja (djup 2 — redovisad, ej infogad)", ""]
        L += [f"- {c}" for c in s["referenskedja"]]
        L.append("")

    L += [f"{h} Förbehåll", "", FORBEHALL, ""]
    return L


def render_collected(s):
    return "\n".join([f"## {s['id']} — {s['niva']}", ""]
                     + body_md(s, heading=2) + ["---", "", ""])


FOOTER = f"""
---

Källa: förordning (EU) 2016/679, {OJ}, i lydelse enligt {RATT}. Bärare av
ordalydelsen: {KONS}, © Europeiska unionen, CC BY 4.0. Konsoliderade texter är
dokumentationshjälpmedel utan rättslig verkan; endast EUT:s elektroniska
utgåva är giltig och har rättslig verkan (rådets förordning (EU) nr 216/2013).
Ordalydelsen är oförändrad och maskinellt verifierad tecken för tecken mot
källan. Gjorda ändringar redovisas i `NOTICE`. Genererad fil — redigera inte.
"""


def render_single(s, prev, nxt):
    L = [f"# {s['id']}", "", f"*{s['niva']}*", ""] + body_md(s, heading=1)
    nav = []
    if prev:
        nav.append(f"[← {prev['id']}]({prev['id']}.md)")
    nav.append(f"[Artikel {s['artikel']}](README.md)")
    nav.append("[Alla lagrum](../README.md)")
    if nxt:
        nav.append(f"[{nxt['id']} →]({nxt['id']}.md)")
    L += ["  ·  ".join(nav), ""]
    return "\n".join(L) + FOOTER


def first_line(s, n=110):
    t = s["normtext"][-1]["text"]
    return (t[:n].rstrip() + "…") if len(t) > n else t


def render_article_index(n, group):
    s0 = group[0]
    L = [f"# Artikel {n} – {s0['artikelrubrik']}", "",
         f"**Kapitel:** {s0['kapitel'] or '—'}  "]
    if s0["avsnitt"]:
        L.append(f"**Avsnitt:** {s0['avsnitt']}  ")
    L += [f"**Lagrum i artikeln:** {len(group)}", "",
          "| Lagrum | Nivå | Normtext |", "|---|---|---|"]
    for s in group:
        L.append(f"| [{s['id']}]({s['id']}.md) | {s['niva']} | "
                 f"{esc(first_line(s))} |")
    L += ["", "[Alla lagrum](../README.md)"]
    return "\n".join(L) + FOOTER


def render_root_index(sts, byart):
    L = ["# Lagrum", "",
         f"GDPR:s artiklar 1–99 som {len(sts)} självständigt läsbara lagrum, "
         "ett per fil. Varje fil går att läsa, länka till och citera utan "
         "resten av förordningen.", "",
         "Filnamnet är lagrummets identifierare, så sökvägen är stabil och "
         "citerbar: `lagrum/artikel-05/GDPR-5.1.b.md`.", ""]
    cur_k = cur_av = None
    behov = False
    for n in sorted(byart):
        g = byart[n]
        s0 = g[0]
        if s0["kapitel"] != cur_k:
            cur_k = s0["kapitel"]
            cur_av = None
            L += ["", f"## {cur_k}", ""]
            behov = True
        if s0["avsnitt"] != cur_av:
            cur_av = s0["avsnitt"]
            if cur_av:
                L += [f"### {cur_av}", ""]
                behov = True
        if behov:
            L += ["| Artikel | Rubrik | Lagrum |", "|---|---|---|"]
            behov = False
        L.append(f"| [{n}]({artdir(n)}/README.md) | {esc(s0['artikelrubrik'])} "
                 f"| {len(g)} |")
    return "\n".join(L) + FOOTER


# ----------------------------------------------------------------- lästext

def render_plain(s):
    L = [f"{s['id']} — {s['niva']}", f"{s['kapitel'] or ''}"]
    if s["avsnitt"]:
        L.append(s["avsnitt"])
    L += [f"Artikel {s['artikel']} – {s['artikelrubrik']}", "",
          "NORMTEXT (ordagrant)"]
    for b in s["normtext"]:
        L += [f"[{b['label']}]", b["text"], ""]
    inf = [r for r in s["referenser"] if r["typ"] == "infogad"]
    for i, r in enumerate(inf, 1):
        L += [f"INFOGAD REFERENS [{i}/{len(inf)}] — {r['mal']} "
              f"(hänvisning: ”{r['referens']}”)"]
        for b in r["block"]:
            L += [f"[{b['label']}]", b["text"], ""]
    if s["termer"]:
        L += ["TERMER — ARTIKEL 4 (ordagrant)", "I denna förordning avses med"]
        for t in s["termer"]:
            L += [f"[artikel {t['ref']}]", t["text"], ""]
    pek = [r for r in s["referenser"] if r["typ"] == "pekare"]
    if pek:
        L += ["PEKARE (återges inte i sin helhet)"]
        for r in pek:
            for m in r["mal_lista"]:
                L.append(f"- {m['mal']}"
                         + (f" – {m['rubrik']}" if m["rubrik"] else ""))
        L.append("")
    ext = [r for r in s["referenser"] if r["typ"] == "externt"]
    if ext:
        L += ["EXTERNA INSTRUMENT (återges inte)"]
        L += [f"- ”{r['referens']}” i {r['instrument']}" for r in ext]
        L.append("")
    p = s["proveniens"]
    L += [f"PROVENIENS: {p['autentisk_kalla']}, {p['lydelse']} "
          f"({p['markor']}). Bärare: {p['barare']}.",
          "", f"FÖRBEHÅLL: {FORBEHALL}"]
    return "\n".join(L)


HEAD = f"""# GDPR — självständiga lagrum

Förordning (EU) 2016/679 (allmän dataskyddsförordning), artikeldelen,
uppdelad i självständigt läsbara lagrum på lägsta adresserbara normnivå.

* **Autentisk källa:** {OJ}, i lydelse enligt {RATT}
* **Bärare av ordalydelsen:** {KONS}
* **Omfattning:** artiklarna 1–99. Skäl (1)–(173) ingår inte.
* **Ordalydelse:** normtext och infogad text återges ordagrant och obrutet.
  Enda tillämpade normalisering är att hårt blanksteg (U+00A0) ersatts med
  vanligt blanksteg och att HTML-radbrytningar kollapsats till enkelt
  blanksteg. Ingen omskrivning, sammanfattning eller förkortning förekommer.
* **Metod och kontroller:** se METOD.md.
* **Ett lagrum per fil:** se katalogen `lagrum/`.

"""



# ----------------------------------------------------------------- csv

CSV_SEP = ";"
CSV_JOIN = " | "          # skiljetecken inuti celler, aldrig semikolon
CSV_ENC = "utf-8-sig"     # BOM så att Excel läser åäö rätt
CSV_EOL = "\r\n"


def flat(text):
    """En cell får aldrig innehålla radbrytning. Då är det ingen tabell."""
    return re.sub(r"\s+", " ", (text or "").replace("\r", " ")
                  .replace("\n", " ")).strip()


def kap_nr(kapitel):
    m = re.match(r"KAPITEL\s+([IVX]+)", kapitel or "")
    if not m:
        return ""
    rom = {"I": 1, "V": 5, "X": 10}
    s, prev, tot = m.group(1), 0, 0
    for ch in reversed(s):
        v = rom[ch]
        tot += -v if v < prev else v
        prev = max(prev, v)
    return tot


def avs_nr(avsnitt):
    m = re.match(r"Avsnitt\s+(\d+)", avsnitt or "", re.I)
    return int(m.group(1)) if m else ""


def _writer(path, cols):
    fh = open(path, "w", newline="", encoding=CSV_ENC)
    w = csv.DictWriter(fh, fieldnames=cols, delimiter=CSV_SEP,
                       quoting=csv.QUOTE_MINIMAL, lineterminator=CSV_EOL)
    w.writeheader()
    return fh, w


def write_csv(sts):
    """Tre tabeller: ett lagrum per rad, plus normaliserade barntabeller för
    de flervärda fälten. Flervärda värden i en cell blockerar vidare arbete,
    så referenser och termer får egna rader med lagrum_id som nyckel."""

    # --- lagrum: en rad per lagrum
    cols = ["nr", "id", "kapitel_nr", "kapitel", "avsnitt_nr", "avsnitt",
            "artikel", "artikelrubrik", "punkt", "led", "nivatyp", "niva",
            "normtext", "normtext_tecken", "antal_normtextblock",
            "antal_infogade_referenser", "antal_pekare",
            "antal_externa_instrument", "antal_termer", "antal_kedjeposter",
            "infogade_referenser", "pekare", "externa_instrument", "termer",
            "vaga_hanvisningar", "markor", "lydelse", "fil", "url"]
    fh, w = _writer(f"{OUT}/{BASENAME}.csv", cols)
    for i, s in enumerate(sts, 1):
        inf = [r for r in s["referenser"] if r["typ"] == "infogad"]
        pek = [m["mal"] for r in s["referenser"] if r["typ"] == "pekare"
               for m in r["mal_lista"]]
        ext = [f"{r['referens']} i {r['instrument']}"
               for r in s["referenser"] if r["typ"] == "externt"]
        nt = " ".join(f"[{b['label']}] {flat(b['text'])}"
                      for b in s["normtext"])
        w.writerow({
            "nr": i, "id": s["id"],
            "kapitel_nr": kap_nr(s["kapitel"]), "kapitel": flat(s["kapitel"]),
            "avsnitt_nr": avs_nr(s["avsnitt"]), "avsnitt": flat(s["avsnitt"]),
            "artikel": s["artikel"], "artikelrubrik": flat(s["artikelrubrik"]),
            "punkt": s["punkt"] or "", "led": s["led"] or "",
            "nivatyp": s["nivatyp"], "niva": s["niva"],
            "normtext": nt, "normtext_tecken": len(nt),
            "antal_normtextblock": len(s["normtext"]),
            "antal_infogade_referenser": len(inf),
            "antal_pekare": len(pek),
            "antal_externa_instrument": len(ext),
            "antal_termer": len(s["termer"]),
            "antal_kedjeposter": len(s["referenskedja"]),
            "infogade_referenser": CSV_JOIN.join(r["mal"] for r in inf),
            "pekare": CSV_JOIN.join(pek),
            "externa_instrument": CSV_JOIN.join(ext),
            "termer": CSV_JOIN.join(f"{t['ref']} {t['term']}"
                                    for t in s["termer"]),
            "vaga_hanvisningar": CSV_JOIN.join(
                v["uttryck"] for v in s["vaga_hanvisningar"]),
            "markor": s["proveniens"]["markor"],
            "lydelse": flat(s["proveniens"]["lydelse"]),
            "fil": f"{LAGRUM}/{relpath(s)}",
            "url": f"{REPO_URL}/blob/main/{LAGRUM}/{relpath(s)}",
        })
    fh.close()

    # --- referenser: en rad per hänvisning
    rcols = ["nr", "lagrum_id", "typ", "referens", "mal", "mal_rubrik",
             "instrument", "mal_text", "not"]
    fh, w = _writer(f"{OUT}/gdpr-referenser-v1.0.csv", rcols)
    n = 0
    for s in sts:
        for r in s["referenser"]:
            if r["typ"] == "infogad":
                n += 1
                w.writerow({"nr": n, "lagrum_id": s["id"], "typ": "infogad",
                            "referens": flat(r["referens"]), "mal": r["mal"],
                            "mal_rubrik": flat(r["artikelrubrik"]),
                            "instrument": "",
                            "mal_text": " ".join(
                                f"[{b['label']}] {flat(b['text'])}"
                                for b in r["block"]),
                            "not": ""})
            elif r["typ"] == "pekare":
                for m in r["mal_lista"]:
                    n += 1
                    w.writerow({"nr": n, "lagrum_id": s["id"],
                                "typ": "pekare",
                                "referens": flat(r["referens"]),
                                "mal": m["mal"],
                                "mal_rubrik": flat(m.get("rubrik", "")),
                                "instrument": "", "mal_text": "",
                                "not": flat(r.get("not", ""))})
            else:
                n += 1
                w.writerow({"nr": n, "lagrum_id": s["id"], "typ": "externt",
                            "referens": flat(r["referens"]), "mal": "",
                            "mal_rubrik": "",
                            "instrument": flat(r["instrument"]),
                            "mal_text": "", "not": flat(r.get("not", ""))})
    fh.close()
    nref = n

    # --- termer: en rad per term och lagrum
    tcols = ["nr", "lagrum_id", "term_ref", "term", "definition"]
    fh, w = _writer(f"{OUT}/gdpr-termer-v1.0.csv", tcols)
    n = 0
    for s in sts:
        for t in s["termer"]:
            n += 1
            w.writerow({"nr": n, "lagrum_id": s["id"],
                        "term_ref": f"artikel {t['ref']}", "term": t["term"],
                        "definition": flat(t["text"])})
    fh.close()
    print(f"{OUT}/{BASENAME}.csv: {len(sts)} rader, {len(cols)} kolumner")
    print(f"{OUT}/gdpr-referenser-v1.0.csv: {nref} rader")
    print(f"{OUT}/gdpr-termer-v1.0.csv: {n} rader")


# ----------------------------------------------------------------- main

def main():
    sts, reg, chapters = generate()
    sts.sort(key=sortkey)
    os.makedirs(OUT, exist_ok=True)

    parts = [HEAD, "## Innehåll\n"]
    cur_k = cur_a = None
    for s in sts:
        if s["kapitel"] != cur_k:
            cur_k = s["kapitel"]
            parts.append(f"\n**{cur_k}**\n")
            cur_a = None
        if s["artikel"] != cur_a:
            cur_a = s["artikel"]
            parts.append(f"- Artikel {cur_a} – {s['artikelrubrik']}")
    parts.append("\n\n---\n")
    cur_k = cur_av = None
    for s in sts:
        if s["kapitel"] != cur_k:
            cur_k = s["kapitel"]
            parts.append(f"\n# {cur_k}\n")
            cur_av = None
        if s["avsnitt"] and s["avsnitt"] != cur_av:
            cur_av = s["avsnitt"]
            parts.append(f"\n## {cur_av}\n")
        parts.append(render_collected(s))
    md = "\n".join(parts)
    open(f"{OUT}/{BASENAME}.md", "w").write(md)

    byart = {}
    for s in sts:
        byart.setdefault(s["artikel"], []).append(s)

    if os.path.isdir(LAGRUM):
        shutil.rmtree(LAGRUM)
    os.makedirs(LAGRUM, exist_ok=True)
    nfiles = 0
    for n in sorted(byart):
        g = byart[n]
        d = os.path.join(LAGRUM, artdir(n))
        os.makedirs(d, exist_ok=True)
        for i, s in enumerate(g):
            prev = g[i - 1] if i else None
            nxt = g[i + 1] if i + 1 < len(g) else None
            open(os.path.join(d, f"{s['id']}.md"), "w").write(
                render_single(s, prev, nxt))
            nfiles += 1
        open(os.path.join(d, "README.md"), "w").write(
            render_article_index(n, g))
    open(os.path.join(LAGRUM, "README.md"), "w").write(
        render_root_index(sts, byart))

    json.dump({"kalla": {"autentisk": OJ,
                         "rattelser": {f"C{i}": RATTELSER[f"C{i}"]
                                       for i in range(1, len(RATTELSER) + 1)},
                         "barare": KONS},
               "omfattning": "artiklarna 1–99",
               "antal_lagrum": len(sts),
               "lagrum": sts},
              open(f"{OUT}/{BASENAME}.json", "w"),
              ensure_ascii=False, indent=1)

    write_csv(sts)

    print(f"lagrum: {len(sts)}")
    print(f"{OUT}/{BASENAME}.md: {len(md)} tecken")
    print(f"{LAGRUM}/: {nfiles} lagrumsfiler + {len(byart) + 1} indexfiler")
    return sts


if __name__ == "__main__":
    main()
