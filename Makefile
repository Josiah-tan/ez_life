MOD_DIR := ez_life

IPYNB := $(shell find $(MOD_DIR) -name *.ipynb)
MODPY := $(IPYNB:.ipynb=.py)
#FILES_OUT_1 = $(FILES_IN:.doc=.docx)

.PHONY: all

all: $(MODPY)
	echo $^

%.py: %.ipynb
	jupyter nbconvert $< --to="python" # --output=$@
