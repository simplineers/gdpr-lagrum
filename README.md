# gdpr-lagrum

GDPR:s artiklar 1–99 uppdelade i 705 självständigt läsbara lagrum, med
ordagrann normtext, infogade hänvisningar och de definitioner ur artikel 4 som
faktiskt behövs. **Ett lagrum per fil** — varje bestämmelse går att läsa, länka
till och citera utan att ha resten av förordningen framför sig.

*English: the 99 articles of the GDPR (Swedish language version) split into 705
self-contained, citable provisions, one per file. Verbatim normative text,
referenced provisions quoted in full, and the Article 4 definitions actually
used. Every quoted string is machine-verified character-for-character against
the source. See `METOD.md` for method, `NOTICE` for sources and terms.*

## Börja här

[**lagrum/**](lagrum/README.md) — index per kapitel och artikel.

Filnamnet är lagrummets identifierare, så sökvägen är stabil och citerbar:

```
lagrum/artikel-05/GDPR-5.1.b.md
lagrum/artikel-04/GDPR-4.11.md
lagrum/artikel-06/GDPR-6.1.f.md
```

## Vad en fil innehåller

`GDPR-5.1.b.md` börjar med punktens inledning och ledet ordagrant, därefter
artikel 89.1 i sin helhet i ett eget block, därefter definitionerna av
*personuppgifter*, *behandling* och *pseudonymisering*. Ingenting splitsas in i
normtexten — den ska kunna läsas som den är antagen.

```
## Normtext (ordagrant)

*artikel 5.1 inledning*
> Vid behandling av personuppgifter ska följande gälla:

*artikel 5.1 led b*
> De ska samlas in för särskilda, uttryckligt angivna och berättigade ändamål
> och inte senare behandlas på ett sätt som är oförenligt med dessa ändamål.
> Ytterligare behandling … i enlighet med artikel 89.1 ska inte anses vara
> oförenlig med de ursprungliga ändamålen (ändamålsbegränsning).

## Infogad referens [1/1] — artikel 89.1
Hänvisning i normtexten: ”artikel 89.1”.

*artikel 89.1*
> Behandling för arkivändamål av allmänt intresse … ska omfattas av lämpliga
> skyddsåtgärder i enlighet med denna förordning för den registrerades
> rättigheter och friheter. …

## Termer — artikel 4 (ordagrant)
…
```

Utöver detta: pekare till hänvisningar som inte återges i sin helhet, externa
instrument, vaga hänvisningar, referenskedja på djup 2, proveniens och
förbehåll.

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
s. 2, och rättelse i EUT L 74, 4.3.2021, s. 35. Rättelserna finns inte i originalpubliceringen — därför används den
konsoliderade texten som bärare av ordalydelsen.

Endast EUT:s elektroniska utgåva är giltig och har rättslig verkan (rådets
förordning (EU) nr 216/2013). Konsoliderade texter är dokumentationshjälpmedel
utan rättslig verkan. Varje lagrum anger den autentiska källan och vilken rättsakt just den
ordalydelsen kommer från: originalet (`▼B`, 663 lagrum), 2018-rättelsen
(`▼C1`, 40 lagrum) eller 2021-rättelsen (`▼C2`, 2 lagrum).

Indata pinnas med SHA-256. Bygget vägrar starta mot en okänd källfil, så
artefakterna kan inte härledas ur en annan version än den avsedda. Se
[`source/SOURCE.md`](source/SOURCE.md).

## Bygga

```sh
pip install -r requirements.txt
make all
```

Bygget är deterministiskt: `lagrum/`, `METOD.md` och JSON blir bitidentiska
mellan körningar. Inga datumstämplar förekommer, just för att en omgenerering
ska ge en tom diff när ingenting ändrats.

`lagrum/` och `METOD.md` är genererade men versionshanterade. Det är avsiktligt:
när generatorn eller källan ändras ger omgenereringen en granskningsbar diff
per enskilt lagrum, vilket är en revisionskontroll i sig. `make sync` failar om
de inte är aktuella, och CI kör den. Samlingsutgåvorna i `dist/` är däremot
inte versionshanterade utan byggs i CI.

## Verifiering

Tre grindar, samtliga obligatoriska i CI. Bygget failar om en enda ordalydelse
avviker.

| Kontroll | Skript | Utfall |
|---|---|---|
| Det parsade trädet återsammanfogas och jämförs tecken för tecken mot källans artikeltext, alla 99 artiklar | `verify.py` | 0 avvikelser |
| Samtliga blockcitat i samlingsdokumentet och i varje enskild lagrumsfil återfinns ordagrant i källan | `final_check.py` | 10 610 citat, 0 avvikelser |
| Filnamn matchar identifierare, unika id, artikeltäckning, interna länkar | `final_check.py` | 705/705, 99/99, 0 brutna |
| `lagrum/` och `METOD.md` är aktuella | `make sync` | tom diff krävs |

Enda tillämpade normalisering är att hårt blanksteg (U+00A0) ersatts med
vanligt blanksteg och att HTML-radbrytningar kollapsats till enkelt blanksteg.
Ingen omskrivning, sammanfattning eller förkortning förekommer.

## Struktur

```
lagrum/artikel-NN/GDPR-*.md   ett lagrum per fil, versionshanterade
lagrum/artikel-NN/README.md   artikelindex
lagrum/README.md              rotindex per kapitel

parse.py                      EUR-Lex-HTML -> nodträd, med checksumpinne
statements.py                 lagrum, referens- och termupplösning, proveniens
render.py                     lagrum/ samt samlingsutgåvorna i dist/
metod.py                      METOD.md ur den faktiska körningen
verify.py                     återsammanfogning mot källan
final_check.py                kontroll av samtliga levererade filer

METOD.md                      metod, designval, kända begränsningar
NOTICE                        källor, licensvillkor, redovisade ändringar
source/SOURCE.md              pinnad indata
```

## Samlingsutgåvor

| Fil | Innehåll |
|---|---|
| `dist/gdpr-lagrum-v1.0.md` | samlingsdokument, alla lagrum, innehållsförteckning per kapitel |
| `dist/gdpr-lagrum-v1.0.json` | strukturerad utgåva; `kalla`, `omfattning`, `antal_lagrum`, `lagrum[]` |
| `dist/gdpr-lagrum-v1.0.csv` | tabell, en rad per lagrum, 29 kolumner |
| `dist/gdpr-referenser-v1.0.csv` | tabell, en rad per hänvisning, nyckel `lagrum_id` |
| `dist/gdpr-termer-v1.0.csv` | tabell, en rad per term och lagrum, nyckel `lagrum_id` |

CSV-utgåvorna är semikolonseparerade och UTF-8 med BOM, alltså direkt öppningsbara
i svensk Excel utan importguide. Ingen cell innehåller radbrytning och fältantalet
är konstant. Flervärda fält är normaliserade till barntabeller i stället för att
packas i en cell. Se `METOD.md` avsnitt 9.

## Begränsningar

Termmatchningen är heuristisk och kan i enstaka fall missa en oregelbunden
böjningsform eller träffa en term i allmänspråklig mening. Träffarna redovisas
alltid med artikelnummer så att en granskare kan avvisa dem. Hela artiklar och
kapitel återges inte vid hänvisning, bara pekare med rubrik. Vaga uttryck som
”unionsrätten” löses inte upp. Strecksatser är inte självständigt adresserbara
i förordningen och ingår därför i punktens lagrum. Samtliga val är dokumenterade
i [`METOD.md`](METOD.md) avsnitt 6 och 7.

Materialet ersätter inte en rättslig bedömning.

## Licens

Repot innehåller två slags material med olika licens.

| Material | Licens | Fil |
|---|---|---|
| Normtext, genererade lagrumsfiler och samlingsutgåvor | CC BY 4.0 | [`LICENSE`](LICENSE) |
| Generator, kontrollskript och `METOD.md` | Apache-2.0 | [`LICENSE-CODE`](LICENSE-CODE) |

Normtexten är derivat av EU:s konsoliderade text, som själv är CC BY 4.0, och
kan därför inte licensieras mer restriktivt. Koden ligger under Apache-2.0
eftersom Creative Commons-licenser inte är avsedda för mjukvara: de innehåller
ingen patentupplåtelse och skiljer inte mellan käll- och binärform.

Se [`NOTICE`](NOTICE) för källangivelse och för den redovisning av gjorda
ändringar i EU-materialet som CC BY 4.0 kräver.
