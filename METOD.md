# METOD — GDPR självständiga normuttalanden v1.0

Detta dokument beskriver hur uttalandena i `GDPR-uttalanden-v1.0.md`,
`gdpr-uttalanden-v1.0.json` och `gdpr-uttalanden-v1.0.csv` har framställts,
vilka val som gjorts och vilka kontroller som utförts. Syftet är att en
granskare — internrevision, IMY eller domstol — ska kunna verifiera varje
uttalande mot autentisk källa utan att lita på framställningen.

## 1. Källa och proveniens

| | |
|---|---|
| Rättsakt | Europaparlamentets och rådets förordning (EU) 2016/679 |
| Autentisk källa | EUT L 119, 4.5.2016, s. 1 |
| Rättelse (svensk språkversion) | EUT L 127, 23.5.2018, s. 16 |
| Bärare av ordalydelsen | Konsoliderad text, CELEX 02016R0679-20160504 (SV) |
| Omfattning | Artiklarna 1–99 |

Ordalydelsen är hämtad ur den konsoliderade texten, som innehåller
originaltexten med rättelsen införd. Konsoliderade texter saknar formellt
rättsverkan och utgör enligt Publikationsbyrån endast dokumentationshjälpmedel.
Därför anges i varje uttalande både den autentiska källan och rättelsen, samt
huruvida det enskilda uttalandets ordalydelse är originalets eller rättelsens.
Detta är möjligt eftersom den konsoliderade texten är märkt med `▼B`
(originallydelse) respektive `▼C1` (lydelse enligt rättelsen). Av
705 uttalanden har 42 ändrad lydelse enligt rättelsen.

Skälen (1)–(173) ingår inte. De är tolkningsdata, inte bindande norm, och
blandas medvetet inte in i normtexten.

## 2. Uttalandets uppbyggnad

Varje uttalande består av avgränsade block i fast ordning:

1. **Normtext** — den bindande bestämmelsen, ordagrant och obrutet.
2. **Infogad referens** — text som normtexten hänvisar till, ordagrant, i eget
   block med angivande av vilken hänvisning i normtexten som föranlett den.
3. **Termer** — de definitioner i artikel 4 vars termer faktiskt förekommer,
   ordagrant.
4. **Pekare** — hänvisningar som inte återges i sin helhet, med artikelrubrik.
5. **Externa instrument** — hänvisningar utanför förordningen, aldrig återgivna.
6. **Vaga hänvisningar** — uttryck utan angivet instrument, annoterade.
7. **Referenskedja** — hänvisningar på djup 2, redovisade men inte infogade.
8. **Proveniens** och **förbehåll**.

Infogad text placeras alltid **efter** normtexten, aldrig inne i den. Skälet är
att normtexten måste kunna läsas som den är antagen; text som splitsas in mitt i
en mening blir grammatiskt bruten och är inte längre lagtexten.

## 3. Granularitet och identifierare

Uttalanden bildas på lägsta adresserbara normnivå:

| Nivå | ID-mönster | Exempel | Antal |
|---|---|---|---|
| Led i punkt | `GDPR-{artikel}.{punkt}.{led}` | `GDPR-5.1.b` | 352 |
| Punkt utan led | `GDPR-{artikel}.{punkt}` | `GDPR-5.2` | 312 |
| Definition i artikel 4 | `GDPR-4.{nr}` | `GDPR-4.11` | 26 |
| Artikel utan punkter | `GDPR-{artikel}` | `GDPR-16` | 15 |
| **Totalt** | | | **705** |

Identifierarna är stabila och deterministiska: de härleds ur förordningens egen
numrering, inte ur genereringsordningen. Ett led ärver alltid punktens
inledning (chapeau) samt punktens eventuella avslutande stycke, eftersom ett led
annars är obegripligt fristående — jämför artikel 6.1 f, som är oläsbar utan
både inledningen och det avslutande stycket om myndigheters behandling.

## 4. Normalisering av text

Endast två normaliseringar har tillämpats, båda icke-substantiella:

1. Hårt blanksteg (U+00A0) har ersatts med vanligt blanksteg.
2. HTML-radbrytningar och indentering har kollapsats till enkelt blanksteg.

Ingen omskrivning, sammanfattning, förkortning, stavningsändring eller
interpunktionsändring förekommer. Kursiverade termer i EUT-texten är i
markdown-utgåvan återgivna med `*emfas*`; i JSON finns både `text` (ren) och
`text_md` (med emfas).

## 5. Referenshantering

| Hänvisningstyp | Behandling |
|---|---|
| Bestämd nivå inom förordningen (t.ex. artikel 89.1, punkt 2 h) | Infogas ordagrant |
| Hel artikel (t.ex. artikel 6) | Pekare med artikelrubrik, infogas inte |
| Artikelintervall (t.ex. artiklarna 12–22) | Expanderas till pekarlista |
| Kapitel (t.ex. kapitel V) | Pekare med kapitelrubrik |
| Externt instrument | Annoteras, infogas aldrig |
| Vagt uttryck (t.ex. ”denna förordning”) | Annoteras |

Rekursionsdjup är 1. Hänvisningar i infogad text redovisas i referenskedjan men
infogas inte, vilket hindrar att uttalandet växer okontrollerat via kedjor som
17.3 b → 9.2 h → 89.1. Antal redovisade kedjeposter: 1424.

Cykel- och redundanshantering: hänvisning till uttalandets egen bestämmelse
eller egen punkt infogas inte, eftersom texten redan finns i normtexten. Om en
hel punkt infogas utesluts separat infogning av enskilda led i samma punkt.

Utfall: 454 infogade referenser, 218 pekare,
9 externa. Samtliga hänvisningar kunde upplösas; noll oupplösta.

Externa instrument som förekommer: Europaparlamentets och rådets direktiv (EU) 2015/1535, direktiv 95/46/EG, förordning (EU) nr 182/2011.

**Tolkningsregel för bokstaven ”i”.** I svensk lagtext är ”i” både ett led
(”punkt 2 h, i eller j”) och prepositionen ”i” (”punkt 1 i denna artikel”).
Ett ensamt ”i” tolkas som led endast när nästa token inte är ett ord, annars som
preposition. Regeln är tillämpad maskinellt och gav noll felklassificeringar i
kontrollen.

## 6. Termhantering

Definitionerna i artikel 4 infogas ordagrant för de termer som faktiskt
förekommer i uttalandets normtext eller i dess infogade referenser. Uttalanden
med minst en term: 633 av 705.

Matchningen sker mot ett slutet svenskt böjningssuffix (bestämd/obestämd form,
plural, genitiv) och kräver ordgräns, så att sammansättningar inte ger
felträffar: ”behandlingen” och ”behandlingar” matchar termen *behandling*, men
”behandlingsverksamhet” gör det inte. Längsta term matchas först och matchade
teckenpositioner maskeras, så att *bindande företagsbestämmelser* inte också
utlöser *företag*.

Två redaktionella alias har införts där lagtextens termform inte förekommer i
brukstexten:

| Definition | Termform i artikel 4 | Tillagt alias | Skäl |
|---|---|---|---|
| 4.11 | samtycke av den registrerade | samtycke | Brukstexten skriver genomgående ”samtycke” |
| 4.6 | register | registret, registren, registrets | Oregelbunden böjning som suffixregeln inte täcker |

En definition injicerar aldrig sig själv.

## 7. Kända begränsningar och redaktionella val

* **Strecksatser** (t.ex. artikel 53.1) är inte självständigt adresserbara i
  förordningen. De ingår därför i punktens uttalande i sin helhet i stället för
  att bilda egna uttalanden.
* **Hela artiklar återges inte** vid hänvisning. Ett uttalande som pekar på
  artikel 6 skulle annars svälla med cirka 1 200 ord.
* **Termmatchning är heuristisk.** Suffixregeln kan i enstaka fall missa en
  starkt oregelbunden form. Den kan också träffa en term som används i
  allmänspråklig snarare än legaldefinierad mening. Träffarna är därför alltid
  redovisade med artikelnummer så att en granskare kan avvisa dem.
* **Skäl ingår inte.** Om skälen ska kopplas bör det ske som ett separat
  lager med egen märkning, inte som del av normtexten.
* **Vaga hänvisningar löses inte upp.** Uttryck som ”unionsrätten” eller
  ”medlemsstaternas nationella rätt” pekar inte på ett bestämt instrument och
  kräver bedömning i det enskilda fallet. De förekommer så här ofta:
  denna förordning (180), unionsrätten (59), medlemsstaternas nationella rätt (41), denna artikel (27), detta kapitel (3), den här förordningen (2).

## 8. Utförda kontroller

| Kontroll | Utfall |
|---|---|
| Återsammanfogning av parsat träd jämfört tecken för tecken mot källans artikeltext, alla 99 artiklar | 0 avvikelser |
| Samtliga textblock i JSON återfinns ordagrant i källan (4 498 block) | 0 avvikelser |
| Samtliga blockcitat i levererad markdown återfinns ordagrant i källan (5 305 citat) | 0 avvikelser |
| Unika identifierare | 705 av 705 |
| Artikeltäckning | 99 av 99 (artiklarna 1–99) |
| Oupplösta hänvisningar | 0 |

Kontrollerna är återkörbara med `verify.py` och `final_check.py` i
`gdpr-generator-v1.0.zip`.

## 9. Filer

| Fil | Innehåll |
|---|---|
| `GDPR-uttalanden-v1.0.md` | Fullständigt läsdokument, 705 uttalanden, innehållsförteckning per kapitel |
| `gdpr-uttalanden-v1.0.json` | Strukturerad utgåva för systeminläsning |
| `gdpr-uttalanden-v1.0.csv` | Platt utgåva, en rad per uttalande, inklusive kolumnen `lastext` med färdig lästext för GRC-fält |
| `METOD.md` | Detta dokument |
| `gdpr-generator-v1.0.zip` | Parser, generator, renderare och kontrollskript |

CSV-kolumner: `id`, `kapitel`, `avsnitt`, `artikel`, `artikelrubrik`, `niva`,
`nivatyp`, `normtext`, `infogade_referenser`, `pekare`, `externa_instrument`,
`termer`, `referenskedja`, `vaga_hanvisningar`, `lydelse`, `markor`,
`lastext`, `forbehall`.

## 10. Statistik

* Uttalanden: 705
* Normtextens längd per uttalande: median 309 tecken,
  max 1863 tecken
* Uttalanden utan hänvisningar (fristående redan i normtexten): 302
* Flest uttalanden i en artikel: artikel 58 (29 st)

*Genererad 2026-08-27. Version 1.0.*
