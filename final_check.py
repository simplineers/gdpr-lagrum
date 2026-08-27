"""
final_check.py — verifierar de levererade filerna mot källan.

Kontrollerar samlingsdokumentet i dist/ OCH samtliga enskilda lagrumsfiler i
lagrum/, så att ingen ordalydelse kan avvika i någon utgåva. Varje blockcitat
extraheras och måste återfinnas ordagrant i källans artikeltext.
"""
import re, json, os, sys, glob
import parse as P
from bs4 import BeautifulSoup

MD = os.environ.get("GDPR_MD", "dist/gdpr-lagrum-v1.0.md")
JSON = os.environ.get("GDPR_JSON", "dist/gdpr-lagrum-v1.0.json")
LAGRUM = os.environ.get("GDPR_LAGRUM", "lagrum")

soup = BeautifulSoup(open(P.SRC, encoding="utf-8", errors="replace").read(),
                     "lxml")
full = " ".join(P.text_of(soup.find("div", id=f"art_{n}"))
                for n in range(1, 100) if soup.find("div", id=f"art_{n}"))
full = re.sub(r"\s+", " ", full)
assert "*" not in full, "källan innehåller asterisk – emfasborttagning osäker"

fel = 0


def kontrollera(path, text):
    """Varje blockcitat i filen måste finnas ordagrant i källan."""
    global fel
    quotes = [l[2:].strip() for l in text.splitlines() if l.startswith("> ")]
    bad = [q for q in quotes if q.replace("*", "") not in full]
    for b in bad:
        print(f"  ! {path}: {b.replace('*','')[:100]}")
    fel += len(bad)
    return len(quotes), len(bad)


# --- samlingsdokumentet
md = open(MD).read()
nq, nb = kontrollera(MD, md)
print(f"{MD}: {nq} blockcitat, {nb} avvikelser")

ids_md = re.findall(r"^## (GDPR-[\w.]+) — ", md, re.M)
print(f"  lagrum i dokumentet: {len(ids_md)}, unika id: {len(set(ids_md))}")

# --- json
d = json.load(open(JSON))
print(f"{JSON}: {d['antal_lagrum']} lagrum")
if d["antal_lagrum"] != len(set(ids_md)):
    print("  ! antalet lagrum skiljer sig mellan json och samlingsdokumentet")
    fel += 1

# --- enskilda lagrumsfiler
files = sorted(glob.glob(f"{LAGRUM}/artikel-*/GDPR-*.md"))
tot_q = tot_b = 0
ids_files = set()
for f in files:
    t = open(f).read()
    q, b = kontrollera(f, t)
    tot_q += q
    tot_b += b
    m = re.match(r"^# (GDPR-[\w.]+)$", t.splitlines()[0])
    if not m:
        print(f"  ! {f}: saknar id-rubrik")
        fel += 1
    else:
        ids_files.add(m.group(1))
        if os.path.basename(f) != m.group(1) + ".md":
            print(f"  ! {f}: filnamn matchar inte id {m.group(1)}")
            fel += 1
print(f"{LAGRUM}/: {len(files)} lagrumsfiler, {tot_q} blockcitat, "
      f"{tot_b} avvikelser")

# --- täckning
if ids_files != set(ids_md):
    saknas = set(ids_md) - ids_files
    extra = ids_files - set(ids_md)
    print(f"  ! id-mängderna skiljer sig. Saknas som fil: {sorted(saknas)[:5]}. "
          f"Extra filer: {sorted(extra)[:5]}")
    fel += 1

arts = sorted({int(i.split("-")[1].split(".")[0]) for i in ids_md})
ok_art = arts == list(range(1, 100))
print(f"artiklar täckta: {len(arts)} av 99 ({'ok' if ok_art else 'AVVIKELSE'})")
if not ok_art:
    fel += 1

# --- brutna interna länkar i lagrumsfilerna
brutna = 0
for f in files:
    d0 = os.path.dirname(f)
    for target in re.findall(r"\]\((?!https?:)([^)#]+)\)", open(f).read()):
        if not os.path.exists(os.path.normpath(os.path.join(d0, target))):
            print(f"  ! {f}: bruten länk {target}")
            brutna += 1
print(f"brutna interna länkar: {brutna}")
fel += brutna

print(f"\nTOTALT: {tot_q + nq} kontrollerade blockcitat, {fel} fel")
sys.exit(1 if fel else 0)
