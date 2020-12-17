DEV_DIR := ez_life
PACKAGE_DIR := ez_life_package

IPYNB := $(shell find $(DEV_DIR) -name *.ipynb)
MODPY := $(IPYNB:.ipynb=.py)
TESTPY := $(addprefix test_, $(notdir $(MODPY)))

.PHONY: all test package

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
	jupyter nbconvert $< --to="python" \
	--TemplateExporter.exclude_markdown=True \
	--TemplateExporter.exclude_output_prompt=True \
	--TemplateExporter.exclude_input_prompt=True # --output=$@

package: $(PACKAGE_DIR)
	rsync -avr --exclude='*.ipynb' --delete $(DEV_DIR)/ $(PACKAGE_DIR)
