# METOD — GDPR självständiga lagrum v1.0

Detta dokument beskriver hur lagrummen i `lagrum/` och `dist/` har
framställts, vilka val som gjorts och vilka kontroller som utförts. Syftet är
att en granskare — internrevision, IMY eller domstol — ska kunna verifiera
varje lagrum mot autentisk källa utan att lita på framställningen.

Dokumentet genereras av `metod.py` ur den faktiska körningen. Siffrorna nedan
är därför alltid aktuella och kan inte glida ifrån koden.

## 1. Källa och proveniens

| | |
|---|---|
| Rättsakt | Europaparlamentets och rådets förordning (EU) 2016/679 |
| Autentisk källa | EUT L 119, 4.5.2016, s. 1 |
| Rättelse 1 (svensk språkversion) | rättelse, EUT L 127, 23.5.2018, s. 2, markerad ▼C1 |
| Rättelse 2 (svensk språkversion) | rättelse, EUT L 74, 4.3.2021, s. 35, markerad ▼C2 |
| Bärare av ordalydelsen | konsoliderad text CELEX 02016R0679-20160504 (SV) |
| Omfattning | Artiklarna 1–99 |

Ordalydelsen är hämtad ur den konsoliderade texten, som innehåller
originaltexten med rättelsen införd. Konsoliderade texter saknar formellt
rättsverkan och utgör enligt Publikationsbyrån endast dokumentationshjälpmedel.
Därför anges i varje lagrum både den autentiska källan och rättelsen, samt
huruvida det enskilda lagrummets ordalydelse är originalets eller rättelsens.
Detta är möjligt eftersom den konsoliderade texten är märkt per textblock med
vilken rättsakt lydelsen kommer från. Fördelningen över lagrummen:

| Markör | Lydelsens ursprung | Lagrum |
|---|---|---|
| ▼B | originallydelse, EUT L 119, 4.5.2016, s. 1 | 663 |
| ▼C1 | rättelse, EUT L 127, 23.5.2018, s. 2 | 40 |
| ▼C2 | rättelse, EUT L 74, 4.3.2021, s. 35 | 2 |

Kopplingen markör till rättsakt är hämtad ur konsolideringens egen huvudtabell,
inte ur andrahandskällor. En markör som saknas i tabellen är ett hårt fel som
stoppar bygget, så att ett lagrum aldrig kan märkas med fel EUT-referens.

Skälen (1)–(173) ingår inte. De är tolkningsdata, inte bindande norm, och
blandas medvetet inte in i normtexten. Det finns dessutom ett källhinder mot
att lägga till dem — se avsnitt 7.

## 2. Lagrummets uppbyggnad

Varje lagrum består av avgränsade block i fast ordning:

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

Lagrum bildas på lägsta adresserbara normnivå:

| Nivå | ID-mönster | Exempel | Antal |
|---|---|---|---|
| Led i punkt | `GDPR-{artikel}.{punkt}.{led}` | `GDPR-5.1.b` | 352 |
| Punkt utan led | `GDPR-{artikel}.{punkt}` | `GDPR-5.2` | 312 |
| Definition i artikel 4 | `GDPR-4.{nr}` | `GDPR-4.11` | 26 |
| Artikel utan punkter | `GDPR-{artikel}` | `GDPR-16` | 15 |
| **Totalt** | | | **705** |

Identifierarna är stabila och deterministiska: de härleds ur förordningens egen
numrering, inte ur genereringsordningen. Identifieraren är också filnamn, så
sökvägen `lagrum/artikel-05/GDPR-5.1.b.md` är citerbar och beständig.

Ett led ärver alltid punktens inledning (chapeau) samt punktens eventuella
avslutande stycke, eftersom ett led annars är obegripligt fristående — jämför
artikel 6.1 f, som är oläsbar utan både inledningen och det avslutande stycket
om myndigheters behandling.

## 4. Normalisering av text

Endast två normaliseringar har tillämpats, båda icke-substantiella:

1. Hårt blanksteg (U+00A0) har ersatts med vanligt blanksteg.
2. HTML-radbrytningar och indentering har kollapsats till enkelt blanksteg.

Ingen omskrivning, sammanfattning, förkortning, stavningsändring eller
interpunktionsändring förekommer. Kursiverade termer i EUT-texten är i
markdownutgåvorna återgivna med `*emfas*`; i JSON finns både `text` (ren) och
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
infogas inte, vilket hindrar att lagrummet växer okontrollerat via kedjor som
17.3 b → 9.2 h → 89.1. Antal redovisade kedjeposter: 1424.

Cykel- och redundanshantering: hänvisning till lagrummets egen bestämmelse
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
förekommer i lagrummets normtext eller i dess infogade referenser. Lagrum
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
  förordningen. De ingår därför i punktens lagrum i sin helhet i stället för
  att bilda egna lagrum.
* **Hela artiklar återges inte** vid hänvisning. Ett lagrum som pekar på
  artikel 6 skulle annars svälla med cirka 1 200 ord.
* **Termmatchning är heuristisk.** Suffixregeln kan i enstaka fall missa en
  starkt oregelbunden form. Den kan också träffa en term som används i
  allmänspråklig snarare än legaldefinierad mening. Träffarna är därför alltid
  redovisade med artikelnummer så att en granskare kan avvisa dem.
* **Skäl ingår inte, och kan inte läggas till med samma metod.** Utöver att
  skälen är tolkningsdata och inte bindande norm finns ett källproblem som
  den som vill komplettera bör känna till. Den konsoliderade texten innehåller
  ingen ingress alls — EUR-Lex konsoliderar bara den normativa delen.
  Originalpubliceringen (CELEX 32016R0679) innehåller skälen men ingen av de
  två rättelserna. Och rättelserna ändrar bevisligen skältext: rådets
  korrigendumdokument bakom 2021-rättelsen (ST-11744-2020-INIT) ändrar skäl i
  flera språkversioner. Det finns därför ingen elektronisk källa som bär
  korrigerade svenska skäl. Ett skällager kan alltså inte härledas maskinellt
  ur en pinnad bärare på det sätt artikeldelen är, utan skulle kräva att
  rättelserna tillämpas för hand och redovisas per skäl. Att i stället
  publicera skälen i 2016 års lydelse skulle innebära att text som kan vara
  överspelad läggs i ett material avsett att vara citerbart.
* **Vaga hänvisningar löses inte upp.** Uttryck som ”unionsrätten” eller
  ”medlemsstaternas nationella rätt” pekar inte på ett bestämt instrument och
  kräver bedömning i det enskilda fallet. De förekommer så här ofta:
  denna förordning (180), unionsrätten (59), medlemsstaternas nationella rätt (41), denna artikel (27), detta kapitel (3), den här förordningen (2).

## 8. Utförda kontroller

Båda kontrollerna körs som obligatoriska grindar i CI. Bygget failar om en enda
ordalydelse avviker.

| Kontroll | Skript | Utfall |
|---|---|---|
| Återsammanfogning av parsat träd jämfört tecken för tecken mot källans artikeltext, alla 99 artiklar | `verify.py` | 0 avvikelser |
| Samtliga textblock i JSON återfinns ordagrant i källan (4672 block) | `final_check.py` | 0 avvikelser |
| Samtliga blockcitat i samlingsdokumentet återfinns ordagrant i källan | `final_check.py` | 0 avvikelser |
| Samtliga blockcitat i varje enskild lagrumsfil återfinns ordagrant i källan | `final_check.py` | 0 avvikelser |
| Filnamn matchar lagrummets identifierare | `final_check.py` | 705 av 705 |
| Interna länkar i lagrumsfilerna | `final_check.py` | 0 brutna |
| Unika identifierare | `final_check.py` | 705 av 705 |
| Artikeltäckning | `final_check.py` | 99 av 99 |
| Källfilens checksumma | `parse.py` | pinnad, se `source/SOURCE.md` |

## 9. Filer

| Fil | Innehåll |
|---|---|
| `lagrum/artikel-NN/GDPR-*.md` | ett lagrum per fil, 705 filer, versionshanterade |
| `lagrum/artikel-NN/README.md` | artikelindex med samtliga lagrum i artikeln |
| `lagrum/README.md` | rotindex per kapitel och avsnitt |
| `dist/gdpr-lagrum-v1.0.md` | samlingsdokument, alla lagrum |
| `dist/gdpr-lagrum-v1.0.json` | strukturerad utgåva för systeminläsning |
| `dist/gdpr-lagrum-v1.0.csv` | tabell, en rad per lagrum |
| `dist/gdpr-referenser-v1.0.csv` | tabell, en rad per hänvisning, nyckel `lagrum_id` |
| `dist/gdpr-termer-v1.0.csv` | tabell, en rad per term och lagrum, nyckel `lagrum_id` |
| `METOD.md` | detta dokument, genererat av `metod.py` |
| `NOTICE` | källor, licensvillkor, redovisade ändringar |

Innehållet i `lagrum/` och `METOD.md` är genererat men versionshanterat, så att
varje omgenerering ger en granskningsbar diff per lagrum. `dist/` är inte
versionshanterat utan byggs i CI.

### CSV-utgåvorna

Tabellerna är avsedda att arbetas vidare i, inte bara läsas. Därför gäller:

* **Semikolon** som fältavgränsare och **UTF-8 med BOM**, vilket är vad
  svensk Excel förväntar sig. Radslut är CRLF. Filerna öppnas korrekt med
  dubbelklick, utan importguide.
* **Ingen cell innehåller radbrytning.** Fältantalet är konstant på varje rad.
* **Flervärda fält har egna tabeller.** Referenser och termer är normaliserade
  till barntabeller med `lagrum_id` som nyckel, eftersom flera värden i en
  cell blockerar allt vidare arbete. Sammanslagna översikter finns kvar i
  moderfilen för filtrering, med ` | ` som skiljetecken inuti cellen — aldrig
  semikolon, som är fältavgränsare.
* **Inga konstantkolumner.** Förbehållet, som är identiskt för alla lagrum,
  ligger i detta dokument och i lagrumsfilerna, inte som 705 identiska celler.
* **Kolumnen `nr`** bevarar ursprunglig ordning så att en sortering alltid kan
  återställas. `kapitel_nr` och `avsnitt_nr` är heltal för att sortering ska
  bli numerisk och inte alfabetisk.
* **Kolumnen `url`** pekar på lagrummets fil i repot, så en rad i ett
  GRC-verktyg kan länka direkt till den verifierade ordalydelsen.

Moderfilen `gdpr-lagrum-v1.0.csv`: `nr`, `id`, `kapitel_nr`, `kapitel`,
`avsnitt_nr`, `avsnitt`, `artikel`, `artikelrubrik`, `punkt`, `led`,
`nivatyp`, `niva`, `normtext`, `normtext_tecken`, `antal_normtextblock`,
`antal_infogade_referenser`, `antal_pekare`, `antal_externa_instrument`,
`antal_termer`, `antal_kedjeposter`, `infogade_referenser`, `pekare`,
`externa_instrument`, `termer`, `vaga_hanvisningar`, `markor`, `lydelse`,
`fil`, `url`.

`gdpr-referenser-v1.0.csv`: `nr`, `lagrum_id`, `typ`, `referens`, `mal`,
`mal_rubrik`, `instrument`, `mal_text`, `not`.

`gdpr-termer-v1.0.csv`: `nr`, `lagrum_id`, `term_ref`, `term`, `definition`.

JSON-struktur: `kalla`, `omfattning`, `antal_lagrum`, `lagrum[]`.

## 10. Statistik

* Lagrum: 705
* Normtextens längd per lagrum: median 309 tecken,
  max 1863 tecken
* Lagrum utan hänvisningar (fristående redan i normtexten): 302
* Flest lagrum i en artikel: artikel 58
  (29 st)

*Version 1.0. Genererad av `metod.py` ur källfil med SHA-256
`e182db01e290f2768224dc5e6acc042a97bef0592459bf886eb00831c35fab4c`. Inget datum anges eftersom dokumentet ska vara
bitidentiskt vid omgenerering — se avsnitt 8 om sync-grinden.*
