DEV_DIR := develop
PACKAGE_DIR := ez_life

IPYNB := $(shell find $(DEV_DIR) -name *.ipynb)
MODPY := $(IPYNB:.ipynb=.py)
TESTPY := $(addprefix test_, $(notdir $(MODPY)))

.PHONY: all test package testpypi pypi

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

testpypi: $(PACKAGE_DIR)
	python3 setup.py sdist bdist_wheel
	twine check dist/*
	twine upload --skip-existing --repository-url https://test.pypi.org/legacy/ dist/*

pypi: $(PACKAGE_DIR)
	python3 setup.py sdist bdist_wheel
	twine check dist/*
	twine upload --skip-existing --repository-url https://upload.pypi.org/legacy/ dist/*

package: $(PACKAGE_DIR)

$(PACKAGE_DIR): $(DEV_DIR)
	rsync -avr --exclude='*.ipynb' --delete $(DEV_DIR)/ $(PACKAGE_DIR)
