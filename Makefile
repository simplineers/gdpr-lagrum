.RECIPEPREFIX := >
.PHONY: all check build verify clean

GDPR_SRC ?= source/celex-02016R0679-20160504-sv.html
GDPR_OUT ?= dist
export GDPR_SRC
export GDPR_OUT

all: check build verify

## check: kontrollera att kallfilen finns och har ratt checksumma
check:
> python3 -c "import parse; print('kalla ok, sha256', parse.check_source())"

## build: bygg Markdown, JSON och CSV till $(GDPR_OUT)
build:
> python3 render.py

## verify: bada grindarna, failar vid minsta avvikelse i ordalydelsen
verify:
> python3 verify.py
> GDPR_MD=$(GDPR_OUT)/GDPR-uttalanden-v1.0.md \
> GDPR_JSON=$(GDPR_OUT)/gdpr-uttalanden-v1.0.json \
> python3 final_check.py

clean:
> rm -rf $(GDPR_OUT) tree.json __pycache__
