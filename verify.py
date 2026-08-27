"""
verify.py — Kontrollerar att parsningen inte tappat eller ändrat en enda
teckensekvens. Återsammanfogar nodträdet per artikel och jämför mot en
oberoende extraktion av samma artikeldiv.
"""
import re, sys, difflib
from bs4 import BeautifulSoup
import parse as P


def reassemble(a):
    out = [f"Artikel {a['artikel']}", a["rubrik"]]
    if a.get("chapeau"):
        out.append(a["chapeau"])
    for s in a["stycken"]:
        out.append(s["text"])
    for d in a.get("listposter", []):
        out.append(d['marker'])
        out.append(d["text"])
        for sub in d["sub"]:
            out.append(sub['marker'])
            out.append(sub["text"])
    for p in a["punkter"]:
        out.append(f"{p['nr']}.")
        if p["text"]:
            out.append(p["text"])
        else:
            if p["chapeau"]:
                out.append(p["chapeau"])
            for l in p["led"]:
                out.append(l['marker'])
                out.append(l["text"])
                for sub in l["sub"]:
                    out.append(sub['marker'])
                    out.append(sub["text"])
        for s in p["avslut"]:
            out.append(s["text"])
    return re.sub(r"\s+", " ", " ".join(x for x in out if x)).strip()


def source_text(div):
    return P.text_of(div)


def main():
    html = open(P.SRC, encoding="utf-8", errors="replace").read()
    soup = BeautifulSoup(html, "lxml")
    arts = P.parse()
    bad = 0
    for a in arts:
        div = soup.find("div", id=f"art_{a['artikel']}")
        src = source_text(div)
        got = reassemble(a)
        if src != got:
            bad += 1
            print(f"### AVVIKELSE artikel {a['artikel']}")
            sm = difflib.SequenceMatcher(None, src, got)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag != "equal":
                    print(f"  {tag}: KÄLLA={src[i1:i2][:160]!r}")
                    print(f"        PARSAD={got[j1:j2][:160]!r}")
            if bad > 6:
                print("...avbryter"); break
    print(f"\nKontrollerade {len(arts)} artiklar, avvikelser: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
