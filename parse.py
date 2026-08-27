"""
parse.py — Parsar EUR-Lex konsoliderad HTML (CELEX 02016R0679-20160504, SV)
till ett strukturerat nodträd.

Enda tillåtna normalisering av normtext: NBSP (U+00A0) -> vanligt blanksteg,
samt kollaps av HTML-radbrytningar/indentering till enkelt blanksteg.
Ingen annan teckenändring sker. Verifieras av verify.py.
"""
import re, json, os, sys, hashlib
from bs4 import BeautifulSoup, NavigableString, Tag

# Indata pinnas med checksumma. Bygget vägrar starta mot en okänd källfil,
# så att artefakterna aldrig kan härledas ur en annan version än den avsedda.
SRC = os.environ.get("GDPR_SRC", "source/celex-02016R0679-20160504-sv.html")
EXPECTED_SHA256 = "e182db01e290f2768224dc5e6acc042a97bef0592459bf886eb00831c35fab4c"


def check_source(path=None):
    path = path or SRC
    if not os.path.exists(path):
        sys.exit(f"Källfilen saknas: {path}\n"
                 f"Se source/SOURCE.md för hur den hämtas.")
    got = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if got == EXPECTED_SHA256:
        return got
    if os.environ.get("GDPR_ALLOW_UNPINNED") == "1":
        sys.stderr.write(f"VARNING: opinnad källa. Förväntat "
                         f"{EXPECTED_SHA256}, fick {got}\n")
        return got
    sys.exit(f"Källfilens checksumma stämmer inte.\n"
             f"  förväntat: {EXPECTED_SHA256}\n"
             f"  fick:      {got}\n"
             f"Sätt GDPR_ALLOW_UNPINNED=1 för att bygga ändå.")

# ----------------------------------------------------------------- textextraktion

SKIP_CLASSES = {"modref", "anchorarrow"}


def _skip(el: Tag) -> bool:
    cls = set(el.get("class") or [])
    if cls & SKIP_CLASSES:
        return True
    if el.name == "i":
        return True
    return False


def text_of(el, italics_md=False) -> str:
    """Plocka ut text ur ett element. separator='' så inga blanksteg införs."""
    out = []

    def rec(node):
        if isinstance(node, NavigableString):
            out.append(str(node))
            return
        if not isinstance(node, Tag):
            return
        if _skip(node):
            return
        ital = italics_md and "italics" in (node.get("class") or [])
        if ital:
            out.append("*")
        for ch in node.children:
            rec(ch)
        if ital:
            out.append("*")

    rec(el)
    s = "".join(out)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\*\s+\*", " ", s)  # tomma emfasrester
    return s.strip()


def both(el):
    return text_of(el, False), text_of(el, True)


# ----------------------------------------------------------------- dokumentordning

def build_index(soup):
    order = {}
    for i, t in enumerate(soup.find_all(True)):
        order[id(t)] = i
    return order


def provenance_map(soup, order):
    """(dokumentindex, markör) för varje ▼-markering, i ordning."""
    marks = []
    for p in soup.select("p.modref"):
        m = re.search(r"▼\s*([BCM]\d*)", p.get_text(" ", strip=True))
        if m:
            marks.append((order[id(p)], m.group(1)))
    marks.sort()
    return marks


def prov_for(idx, marks):
    cur = "B"
    for i, m in marks:
        if i <= idx:
            cur = m
        else:
            break
    return cur


# ----------------------------------------------------------------- struktur

ROMAN = r"[IVX]+"


def parse():
    check_source()
    html = open(SRC, encoding="utf-8", errors="replace").read()
    soup = BeautifulSoup(html, "lxml")
    order = build_index(soup)
    marks = provenance_map(soup, order)

    chapter = section = None
    chapters, sections = {}, {}
    articles = []

    nodes = soup.select("p.title-division-1, p.title-division-2, div.eli-subdivision")
    pending = None  # ('KAPITEL'|'AVSNITT', label)

    for el in nodes:
        cls = set(el.get("class") or [])
        if "title-division-1" in cls:
            lab = text_of(el)
            if re.match(r"^KAPITEL\s", lab):
                pending = ("KAPITEL", lab)
            elif re.match(r"^AVSNITT\s", lab):
                pending = ("AVSNITT", lab)
            else:
                pending = ("ANNAT", lab)
            continue
        if "title-division-2" in cls:
            name = text_of(el)
            if pending:
                kind, lab = pending
                if kind == "KAPITEL":
                    chapter = f"{lab} – {name}"
                    section = None
                elif kind == "AVSNITT":
                    section = f"{lab} – {name}"
                pending = None
            continue
        # eli-subdivision
        aid = el.get("id") or ""
        m = re.match(r"^art_(\d+)$", aid)
        if not m:
            continue
        art = parse_article(el, int(m.group(1)), chapter, section, order, marks)
        articles.append(art)

    return articles


def is_punkt(el):
    return (
        isinstance(el, Tag)
        and el.name == "div"
        and "norm" in (el.get("class") or [])
        and el.find("span", class_="no-parag", recursive=False) is not None
    )


def parse_article(div, num, chapter, section, order, marks):
    title = ""
    t = div.find("p", class_="stitle-article-norm")
    if t:
        title = text_of(t)

    art = {
        "artikel": num,
        "rubrik": title,
        "kapitel": chapter,
        "avsnitt": section,
        "chapeau": None,
        "chapeau_md": None,
        "punkter": [],
        "stycken": [],   # onumrerade stycken för artiklar utan punkter
        "prov": prov_for(order[id(div)], marks),
    }

    seen_punkt = False
    for child in div.find_all(recursive=False):
        cls = set(child.get("class") or [])
        if child.name == "p" and cls & {"title-article-norm", "modref"}:
            continue
        if "eli-title" in cls:
            continue

        if is_punkt(child):
            seen_punkt = True
            art["punkter"].append(parse_punkt(child, order, marks))
            continue

        if child.name == "p" and "norm" in cls:
            txt, txt_md = both(child)
            if not txt:
                continue
            if not seen_punkt and not art["punkter"]:
                if art["chapeau"] is None and not art["stycken"]:
                    # kan vara artikelchapeau (art. 4) ELLER hela artikeltexten
                    art["stycken"].append({"text": txt, "text_md": txt_md,
                                           "prov": prov_for(order[id(child)], marks)})
                else:
                    art["stycken"].append({"text": txt, "text_md": txt_md,
                                           "prov": prov_for(order[id(child)], marks)})
            else:
                # avslutande stycke som hör till föregående punkt
                art["punkter"][-1]["avslut"].append(
                    {"text": txt, "text_md": txt_md,
                     "prov": prov_for(order[id(child)], marks)})
            continue

        if child.name == "div" and "grid-container" in cls:
            # numrerad lista direkt under artikeln (artikel 4: definitioner)
            art.setdefault("listposter", []).append(parse_item(child, order, marks))
            continue

    # artikel 4-mönstret: första p.norm är chapeau till definitionslistan
    if art.get("listposter") and art["stycken"]:
        art["chapeau"] = art["stycken"][0]["text"]
        art["chapeau_md"] = art["stycken"][0]["text_md"]
        art["stycken"] = art["stycken"][1:]

    return art


def parse_punkt(div, order, marks):
    nr = text_of(div.find("span", class_="no-parag", recursive=False)).rstrip(". ")
    inner = div.find("div", class_="norm", recursive=False)
    if inner is None:
        inner = div
    p = {"nr": nr, "chapeau": None, "chapeau_md": None, "text": None,
         "text_md": None, "led": [], "avslut": [],
         "prov": prov_for(order[id(div)], marks)}

    lists = inner.find_all("div", class_="grid-container", recursive=False)
    intro = inner.find("p", class_="norm", recursive=False)

    if not lists:
        txt, txt_md = both(inner)
        p["text"], p["text_md"] = txt, txt_md
        return p

    if intro is not None:
        p["chapeau"], p["chapeau_md"] = both(intro)
    for g in lists:
        p["led"].append(parse_item(g, order, marks))

    # ev. stycke efter listan men inom samma div
    for pp in inner.find_all("p", class_="norm", recursive=False):
        if pp is intro:
            continue
        txt, txt_md = both(pp)
        if txt:
            p["avslut"].append({"text": txt, "text_md": txt_md,
                                "prov": prov_for(order[id(pp)], marks)})
    return p


def parse_item(g, order, marks):
    col1 = g.find("div", class_="grid-list-column-1", recursive=False)
    col2 = g.find("div", class_="grid-list-column-2", recursive=False)
    marker_raw = text_of(col1).strip() if col1 else ""
    key = marker_raw.rstrip(")").rstrip(".").strip()
    kind = ("bokstav" if re.fullmatch(r"[a-zåäö]", key)
            else "siffra" if re.fullmatch(r"\d+", key)
            else "romersk" if re.fullmatch(r"[ivx]+", key)
            else "strecksats")
    if kind == "strecksats":
        key = ""
    it = {"marker": marker_raw, "key": key, "kind": kind,
          "text": "", "text_md": "", "sub": [],
          "term": None, "prov": prov_for(order[id(g)], marks)}
    if col2 is None:
        return it
    body = col2.find("p", class_="norm", recursive=False)
    subs = col2.find_all("div", class_="grid-container", recursive=False)
    if body is not None:
        it["text"], it["text_md"] = both(body)
        ital = body.find("span", class_="italics")
        if ital is not None and both(body)[0].startswith(text_of(ital)):
            it["term"] = text_of(ital)
    else:
        it["text"], it["text_md"] = both(col2)
    for s in subs:
        it["sub"].append(parse_item(s, order, marks))
    return it


if __name__ == "__main__":
    arts = parse()
    print("artiklar:", len(arts))
    json.dump(arts, open("tree.json", "w"),
              ensure_ascii=False, indent=1)
    # snabb sanity
    a5 = [a for a in arts if a["artikel"] == 5][0]
    print(a5["kapitel"], "|", a5["avsnitt"])
    print("art5 punkter:", [(p["nr"], len(p["led"]), len(p["avslut"])) for p in a5["punkter"]])
    a4 = [a for a in arts if a["artikel"] == 4][0]
    print("art4 chapeau:", a4["chapeau"])
    print("art4 def:", len(a4.get("listposter", [])),
          [(d["marker"], d["term"]) for d in a4.get("listposter", [])][:5])
    a6 = [a for a in arts if a["artikel"] == 6][0]
    print("art6 p1 avslut:", [x["text"][:60] for x in a6["punkter"][0]["avslut"]])
    a16 = [a for a in arts if a["artikel"] == 16][0]
    print("art16 stycken:", len(a16["stycken"]), a16["stycken"][0]["text"][:70])
