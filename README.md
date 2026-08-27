# gdpr-lagrum

GDPR:s artiklar 1–99 uppdelade i självständigt läsbara lagrum, med ordagrann
normtext, infogade hänvisningar och de definitioner ur artikel 4 som faktiskt
behövs. Varje lagrum går att läsa och citera utan att ha resten av
förordningen framför sig.

*English: the 99 articles of the GDPR (Swedish language version) split into
self-contained, citable provisions. Verbatim normative text, referenced
provisions quoted in full, and the Article 4 definitions actually used. Every
quoted string is machine-verified character-for-character against the source.
See `METOD.md` for method, `NOTICE` for sources and terms.*

## Vad ett lagrum ser ut som

`GDPR-5.1.b` innehåller punktens inledning och ledet ordagrant, därefter
artikel 89.1 i sin helhet i ett eget block, därefter definitionerna av
*personuppgifter*, *behandling* och *pseudonymisering*. Ingenting splitsas in
i normtexten — den ska kunna läsas som den är antagen.

```
NORMTEXT (ordagrant)
[artikel 5.1 inledning]
Vid behandling av personuppgifter ska följande gälla:

[artikel 5.1 led b]
De ska samlas in för särskilda, uttryckligt angivna och berättigade ändamål
och inte senare behandlas på ett sätt som är oförenligt med dessa ändamål.
Ytterligare behandling för arkivändamål av allmänt intresse, vetenskapliga
eller historiska forskningsändamål eller statistiska ändamål i enlighet med
artikel 89.1 ska inte anses vara oförenlig med de ursprungliga ändamålen
(ändamålsbegränsning).

INFOGAD REFERENS [1/1] — artikel 89.1 (hänvisning: ”artikel 89.1”)
[artikel 89.1]
Behandling för arkivändamål av allmänt intresse, vetenskapliga eller
historiska forskningsändamål eller statistiska ändamål ska omfattas av
lämpliga skyddsåtgärder i enlighet med denna förordning för den
registrerades rättigheter och friheter. …

TERMER — ARTIKEL 4 (ordagrant)
…
```

## Omfattning

| | |
|---|---|
| Lagrum | 705 |
| Fördelning | 352 led, 312 punkter, 26 definitioner, 15 artiklar utan punktindelning |
| Artiklar | 1–99, samtliga |
| Infogade hänvisningar | 454 |
| Pekare | 218 |
| Externa instrument | 9, aldrig återgivna |
| Skäl (1)–(173) | ingår inte |

Skälen är tolkningsdata, inte bindande norm, och blandas medvetet inte in i
normtexten.

## Källa och autenticitet

Normtexten kommer från förordning (EU) 2016/679, autentiskt offentliggjord i
EUT L 119, 4.5.2016, s. 1, i lydelse enligt rättelse i EUT L 127, 23.5.2018,
s. 16. Den svenska rättelsen omfattar sex sidor och finns inte i
originalpubliceringen — därför används den konsoliderade texten som bärare av
ordalydelsen.

Endast EUT:s elektroniska utgåva är giltig och har rättslig verkan (rådets
förordning (EU) nr 216/2013). Konsoliderade texter är dokumentationshjälpmedel
utan rättslig verkan. Varje lagrum anger båda källorna och om just den
ordalydelsen är originalets (`▼B`) eller rättelsens (`▼C1`).

Indata pinnas med SHA-256. Bygget vägrar starta mot en okänd källfil, så
artefakterna kan inte härledas ur en annan version än den avsedda. Se
`source/SOURCE.md`.

## Bygga

```sh
pip install -r requirements.txt
make all
```

`make all` kontrollerar källans checksumma, bygger artefakterna till `dist/`
och kör båda verifieringarna. Artefakterna versionshanteras inte — de byggs i
CI och läggs som release-assets.

## Verifiering

Två grindar, båda obligatoriska i CI. Bygget failar om en enda ordalydelse
avviker.

| Kontroll | Skript | Utfall |
|---|---|---|
| Det parsade trädet återsammanfogas och jämförs tecken för tecken mot källans artikeltext, alla 99 artiklar | `verify.py` | 0 avvikelser |
| Samtliga 5 305 blockcitat i det levererade dokumentet återfinns ordagrant i källan | `final_check.py` | 0 avvikelser |

Enda tillämpade normalisering är att hårt blanksteg (U+00A0) ersatts med
vanligt blanksteg och att HTML-radbrytningar kollapsats till enkelt blanksteg.
Ingen omskrivning, sammanfattning eller förkortning förekommer.

## Struktur

```
parse.py           EUR-Lex-HTML -> nodträd, med checksumpinne
statements.py      lagrum, referensupplösning, termupplösning, proveniens
render.py          Markdown, JSON och CSV
verify.py          återsammanfogning mot källan
final_check.py     kontroll av den levererade filen
METOD.md           metod, designval, kända begränsningar
NOTICE             källor, licensvillkor, redovisade ändringar
source/SOURCE.md   pinnad indata
```

## Artefakter

| Fil | Innehåll |
|---|---|
| `GDPR-uttalanden-v1.0.md` | läsdokument, alla 705 lagrum, innehållsförteckning per kapitel |
| `gdpr-uttalanden-v1.0.json` | strukturerad utgåva för systeminläsning |
| `gdpr-uttalanden-v1.0.csv` | en rad per lagrum, med kolumnen `lastext` färdig för GRC-fält |

## Begränsningar

Termmatchningen är heuristisk och kan i enstaka fall missa en oregelbunden
böjningsform eller träffa en term i allmänspråklig mening. Träffarna redovisas
alltid med artikelnummer så att en granskare kan avvisa dem. Hela artiklar och
kapitel återges inte vid hänvisning, bara pekare med rubrik. Vaga uttryck som
”unionsrätten” löses inte upp. Samtliga val är dokumenterade i `METOD.md`
avsnitt 6 och 7.

Materialet ersätter inte en rättslig bedömning.

## Licens

Kod och `METOD.md`: se `LICENSE`. Normtexten är EU-material — se `NOTICE` för
källangivelse, licensvillkor och redovisning av gjorda ändringar.
