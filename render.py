"""
render.py — Renderar uttalandena till Markdown, JSON och CSV.
Normtext och infogad text ligger alltid i blockcitat, en rad per block,
så att ordalydelsen kan extraheras och verifieras maskinellt.
"""
import json, csv, re, os
from statements import generate, OJ, RATT, KONS, FORBEHALL

OUT = os.environ.get("GDPR_OUT", "dist")
os.makedirs(OUT, exist_ok=True)


def q(text):
    return "> " + text.replace("\n", " ")


def render_md(s, md=True):
    k = "text_md" if md else "text"
    L = []
    L.append(f"## {s['id']} — {s['niva']}")
    L.append("")
    L.append(f"**Kapitel:** {s['kapitel'] or '—'}  ")
    if s["avsnitt"]:
        L.append(f"**Avsnitt:** {s['avsnitt']}  ")
    L.append(f"**Artikel:** {s['artikel']} – {s['artikelrubrik']}  ")
    L.append(f"**Nivå:** {s['niva']}  ")
    p = s["proveniens"]
    L.append(f"**Proveniens:** {p['autentisk_kalla']}, {p['lydelse']} ({p['markor']}). "
             f"Bärare: {p['barare']}.")
    L.append("")
    L.append("### Normtext (ordagrant)")
    L.append("")
    for b in s["normtext"]:
        L.append(f"*{b['label']}*")
        L.append("")
        L.append(q(b[k]))
        L.append("")

    inf = [r for r in s["referenser"] if r["typ"] == "infogad"]
    for i, r in enumerate(inf, 1):
        L.append(f"### Infogad referens [{i}/{len(inf)}] — {r['mal']}")
        L.append("")
        L.append(f"Hänvisning i normtexten: ”{r['referens']}”. "
                 f"Artikelns rubrik: {r['artikelrubrik']}.")
        L.append("")
        for b in r["block"]:
            L.append(f"*{b['label']}*")
            L.append("")
            L.append(q(b[k]))
            L.append("")

    if s["termer"]:
        L.append("### Termer — artikel 4 (ordagrant)")
        L.append("")
        L.append("Artikel 4 inledning:")
        L.append("")
        L.append(q("I denna förordning avses med"))
        L.append("")
        for t in s["termer"]:
            L.append(f"*artikel {t['ref']}*")
            L.append("")
            L.append(q(t[k]))
            L.append("")

    pek = [r for r in s["referenser"] if r["typ"] == "pekare"]
    if pek:
        L.append("### Pekare (återges inte i sin helhet)")
        L.append("")
        for r in pek:
            for m in r["mal_lista"]:
                rub = f" – {m['rubrik']}" if m["rubrik"] else ""
                L.append(f"- {m['mal']}{rub}  ·  hänvisning: ”{r['referens']}”")
        L.append("")

    ext = [r for r in s["referenser"] if r["typ"] == "externt"]
    if ext:
        L.append("### Externa instrument (återges inte)")
        L.append("")
        for r in ext:
            L.append(f"- ”{r['referens']}” i {r['instrument']}")
        L.append("")

    if s["vaga_hanvisningar"]:
        L.append("### Vaga hänvisningar")
        L.append("")
        for v in s["vaga_hanvisningar"]:
            L.append(f"- ”{v['uttryck']}” — {v['not']}")
        L.append("")

    if s["referenskedja"]:
        L.append("### Referenskedja (djup 2 — redovisad, ej infogad)")
        L.append("")
        for c in s["referenskedja"]:
            L.append(f"- {c}")
        L.append("")

    L.append("### Förbehåll")
    L.append("")
    L.append(FORBEHALL)
    L.append("")
    L.append("---")
    L.append("")
    return "\n".join(L)


def render_plain(s):
    """Ren lästext för GRC-fält: normtext + infogade referenser + termer."""
    L = [f"{s['id']} — {s['niva']}",
         f"{s['kapitel'] or ''}"]
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
                L.append(f"- {m['mal']}" + (f" – {m['rubrik']}" if m["rubrik"] else ""))
        L.append("")
    ext = [r for r in s["referenser"] if r["typ"] == "externt"]
    if ext:
        L += ["EXTERNA INSTRUMENT (återges inte)"]
        L += [f"- ”{r['referens']}” i {r['instrument']}" for r in ext]
        L.append("")
    p = s["proveniens"]
    L += [f"PROVENIENS: {p['autentisk_kalla']}, {p['lydelse']} ({p['markor']}). "
          f"Bärare: {p['barare']}.",
          "", f"FÖRBEHÅLL: {FORBEHALL}"]
    return "\n".join(L)


HEAD = f"""# GDPR — självständiga normuttalanden

Förordning (EU) 2016/679 (allmän dataskyddsförordning), artikeldelen,
uppdelad i självständigt läsbara uttalanden på lägsta adresserbara normnivå.

* **Autentisk källa:** {OJ}, i lydelse enligt {RATT}
* **Bärare av ordalydelsen:** {KONS}
* **Omfattning:** artiklarna 1–99. Skäl (1)–(173) ingår inte.
* **Ordalydelse:** normtext och infogad text återges ordagrant och obrutet.
  Enda tillämpade normalisering är att hårt blanksteg (U+00A0) ersatts med
  vanligt blanksteg och att HTML-radbrytningar kollapsats till enkelt blanksteg.
  Ingen omskrivning, sammanfattning eller förkortning förekommer.
* **Metod och kontroller:** se METOD.md.

"""


def main():
    sts, reg, chapters = generate()

    # --- Markdown, komplett
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
    cur_k = cur_av = cur_a = None
    for s in sts:
        if s["kapitel"] != cur_k:
            cur_k = s["kapitel"]
            parts.append(f"\n# {cur_k}\n")
            cur_av = None
        if s["avsnitt"] and s["avsnitt"] != cur_av:
            cur_av = s["avsnitt"]
            parts.append(f"\n## {cur_av}\n")
        parts.append(render_md(s))
    md = "\n".join(parts)
    open(f"{OUT}/GDPR-uttalanden-v1.0.md", "w").write(md)

    # --- JSON
    for s in sts:
        s.pop("prov", None)
    json.dump({"kalla": {"autentisk": OJ, "rattelse": RATT, "barare": KONS},
               "omfattning": "artiklarna 1–99",
               "antal_uttalanden": len(sts),
               "uttalanden": sts},
              open(f"{OUT}/gdpr-uttalanden-v1.0.json", "w"),
              ensure_ascii=False, indent=1)

    # --- CSV
    cols = ["id", "kapitel", "avsnitt", "artikel", "artikelrubrik", "niva",
            "nivatyp", "normtext", "infogade_referenser", "pekare",
            "externa_instrument", "termer", "referenskedja",
            "vaga_hanvisningar", "lydelse", "markor", "lastext", "forbehall"]
    with open(f"{OUT}/gdpr-uttalanden-v1.0.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, quoting=csv.QUOTE_ALL)
        w.writeheader()
        for s in sts:
            inf = [r for r in s["referenser"] if r["typ"] == "infogad"]
            pek = [m["mal"] for r in s["referenser"] if r["typ"] == "pekare"
                   for m in r["mal_lista"]]
            ext = [f"{r['referens']} i {r['instrument']}"
                   for r in s["referenser"] if r["typ"] == "externt"]
            w.writerow({
                "id": s["id"], "kapitel": s["kapitel"] or "",
                "avsnitt": s["avsnitt"] or "", "artikel": s["artikel"],
                "artikelrubrik": s["artikelrubrik"], "niva": s["niva"],
                "nivatyp": s["nivatyp"],
                "normtext": "\n\n".join(f"[{b['label']}] {b['text']}"
                                        for b in s["normtext"]),
                "infogade_referenser": "; ".join(r["mal"] for r in inf),
                "pekare": "; ".join(pek),
                "externa_instrument": "; ".join(ext),
                "termer": "; ".join(f"4.{t['ref'].split('.')[1]} {t['term']}"
                                    for t in s["termer"]),
                "referenskedja": "; ".join(s["referenskedja"]),
                "vaga_hanvisningar": "; ".join(v["uttryck"]
                                               for v in s["vaga_hanvisningar"]),
                "lydelse": s["proveniens"]["lydelse"],
                "markor": s["proveniens"]["markor"],
                "lastext": render_plain(s),
                "forbehall": FORBEHALL,
            })
    print("uttalanden:", len(sts))
    print("md:", len(md), "tecken")
    return sts


if __name__ == "__main__":
    main()
