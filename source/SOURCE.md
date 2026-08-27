# Pinnad indata

All normtext härleds ur en enda källfil. Filen pinnas med checksumma och
bygget vägrar starta om summan inte stämmer. Syftet är att artefakterna aldrig
ska kunna härledas ur en annan version av förordningen än den avsedda.

## Filen

```
sökväg    source/celex-02016R0679-20160504-sv.html
CELEX     02016R0679-20160504
språk     svenska
format    HTML, konsoliderad text från EUR-Lex
storlek   547 185 byte
SHA-256   e182db01e290f2768224dc5e6acc042a97bef0592459bf886eb00831c35fab4c
```

## Så hämtas den

Öppna den konsoliderade svenska versionen på EUR-Lex och spara sidan som HTML:

<https://eur-lex.europa.eu/legal-content/sv/TXT/?uri=CELEX:02016R0679-20160504>

Spara som HTML, inte PDF. PDF-extraktion inför radbrytnings- och
avstavningsartefakter mitt i lagtexten, vilket gör ordagrann återgivning
omöjlig.

Kontrollera därefter:

```sh
sha256sum source/celex-02016R0679-20160504-sv.html
```

EUR-Lex kan ändra sidans omgivande markup utan att lagtexten ändras. Om summan
inte stämmer ska den nya filen granskas och `EXPECTED_SHA256` i `parse.py`
uppdateras i en egen commit med diff mot den gamla filen, så att ändringen är
spårbar. Bygg aldrig tyst mot en opinnad källa i något som ska vara citerbart.

För att bygga mot en annan fil under utveckling:

```sh
GDPR_SRC=nagon/annan/fil.html GDPR_ALLOW_UNPINNED=1 make all
```

## Autenticitet

Den konsoliderade texten är ett dokumentationshjälpmedel utan rättslig verkan.
Den autentiska källan är EUT L 119, 4.5.2016, s. 1, i lydelse enligt rättelse
i EUT L 127, 23.5.2018, s. 16. Till EUT:s elektroniska utgåva hör en
elektronisk signatur som garanterar äkthet, integritet och oföränderlighet,
och som kan kontrolleras med Publikationsbyråns verktyg CheckLex eller ett
tredjepartsverktyg som uppfyller de fastställda standarderna. En validering av
signaturerna på L 119 och L 127 skulle sluta proveniensskedjan hela vägen från
ett verifierat lagrum till en kryptografiskt bekräftad autentisk källa.
