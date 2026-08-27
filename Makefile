.RECIPEPREFIX := >
.PHONY: all check build verify sync clean

# GDPR_SRC lamnas avsiktligt osatt. parse.py loser upp kallan i source/
# genom att matcha SHA-256 mot pinnen, sa filnamnet spelar ingen roll.
# Satt GDPR_SRC bara for att bygga mot en fil utanfor source/.
GDPR_OUT ?= dist
GDPR_LAGRUM ?= lagrum
export GDPR_OUT
export GDPR_LAGRUM

all: check build verify

## check: kontrollera att kallan i source/ matchar pinnen
check:
> python3 -c "import parse; print('kalla ok, sha256', parse.check_source())"

## build: bygg lagrum/, METOD.md och samlingsutgavorna i $(GDPR_OUT)
build:
> python3 render.py
> python3 metod.py

## verify: bada grindarna, failar vid minsta avvikelse i ordalydelsen
verify:
> python3 verify.py
> python3 final_check.py

## sync: kontrollera att versionshanterade genererade filer ar aktuella
sync:
> git diff --exit-code -- $(GDPR_LAGRUM) METOD.md \
> || { echo "lagrum/ eller METOD.md ar inte aktuella. Kor 'make build' och committa."; exit 1; }

clean:
> rm -rf $(GDPR_OUT) __pycache__
