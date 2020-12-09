MOD_DIR := ez_life

IPYNB := $(shell find $(MOD_DIR) -name *.ipynb)
MODPY := $(IPYNB:.ipynb=.py)
TESTPY := $(addprefix test_, $(notdir $(MODPY)))

.PHONY: all test

all: $(MODPY)
	echo $^

test: $(TESTPY)
	echo $^
	for file in $^; do \
		echo testing $${file}; \
		python3 $${file}; \
	done

#@for f in $(shell ls ${MYDIR}); do echo $${f}; done


%.py: %.ipynb
	jupyter nbconvert $< --to="python" # --output=$@


