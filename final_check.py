"""final_check.py — verifierar den levererade markdownfilen mot källan."""
import re, json, os
import parse as P
from bs4 import BeautifulSoup

MD = os.environ.get("GDPR_MD", "dist/GDPR-uttalanden-v1.0.md")
soup = BeautifulSoup(open(P.SRC, encoding="utf-8", errors="replace").read(), "lxml")
full = " ".join(P.text_of(soup.find("div", id=f"art_{n}"))
                for n in range(1, 100) if soup.find("div", id=f"art_{n}"))
full = re.sub(r"\s+", " ", full)
assert "*" not in full, "källan innehåller asterisk – emfasborttagning osäker"

md = open(MD).read()
quotes = [l[2:].strip() for l in md.splitlines() if l.startswith("> ")]
bad = []
for qline in quotes:
    plain = qline.replace("*", "")
    if plain not in full:
        bad.append(plain[:100])
print(f"blockcitat i leveransen: {len(quotes)}")
print(f"ordagranna träffar i källan: {len(quotes)-len(bad)}")
print(f"AVVIKELSER: {len(bad)}")
for b in bad[:10]:
    print("  !", b)

ids = re.findall(r"^## (GDPR-[\w.]+) — ", md, re.M)
print(f"uttalanden i dokumentet: {len(ids)}, unika id: {len(set(ids))}")
d = json.load(open(os.environ.get("GDPR_JSON", "dist/gdpr-uttalanden-v1.0.json")))
print(f"uttalanden i json: {d['antal_uttalanden']}")
arts = sorted({int(i.split('-')[1].split('.')[0]) for i in ids})
print(f"artiklar täckta: {len(arts)} (1–99: {arts == list(range(1,100))})")
