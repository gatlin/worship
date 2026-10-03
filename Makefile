# Project setup
PROJ      = worship
BUILD     = ./build
DOCS      = ./docs

# Pages that get HTML.  Auto-discovered: every .tex in the repo except the
# preamble and any listed in EXCLUDE_TEX.  Add a file -> it builds automatically.
# To keep a draft file out of the site, either rename it with a hyphen prefix
# (e.g., "-scratch.tex") or list it here.
EXCLUDE_TEX := worship-preamble.tex melody-test.tex abcjs-experiment.html
PAGES       := $(filter-out $(EXCLUDE_TEX),$(wildcard *.tex))

.PHONY: all clean burn timing html clean-html docs

# COLORS
GREEN  := $(shell tput -Txterm setaf 2)
YELLOW := $(shell tput -Txterm setaf 3)
WHITE  := $(shell tput -Txterm setaf 7)
RESET  := $(shell tput -Txterm sgr0)

## Build the service PDFs from source.
all morning.tex midday.tex evening.tex night.tex worship-preamble.tex:
	mkdir -p $(BUILD)
	xelatex --output-directory=$(BUILD) morning.tex
	xelatex --output-directory=$(BUILD) midday.tex
	xelatex --output-directory=$(BUILD) evening.tex
	xelatex --output-directory=$(BUILD) night.tex

## Clean up build artifacts.
clean:
	rm -rf $(BUILD)

## Build HTML versions of all four services.
html:
	mkdir -p $(BUILD)
	cp assets/style.css $(BUILD)/style.css
	cp assets/abcjs-basic-min.js $(BUILD)/abcjs-basic-min.js
	cp assets/manifest.json $(BUILD)/manifest.json
	cp assets/sw.js $(BUILD)/sw.js
	cp assets/icon.svg $(BUILD)/icon.svg
	for p in $(PAGES); do \
		python3 tex2html.py $$p $(BUILD)/$${p%.tex}.html; \
	done

## Copy built HTML into docs/ for GitHub Pages deployment.
docs: html
	mkdir -p $(DOCS)
	for p in $(PAGES); do cp $(BUILD)/$${p%.tex}.html $(DOCS)/; done
	cp $(BUILD)/style.css $(BUILD)/abcjs-basic-min.js $(BUILD)/manifest.json $(BUILD)/sw.js $(BUILD)/icon.svg $(DOCS)/

## Remove generated HTML files.
clean-html:
	rm -f $(PAGES:%.tex=$(BUILD)/%.html) $(BUILD)/style.css $(BUILD)/abcjs-basic-min.js
	rm -f $(BUILD)/manifest.json $(BUILD)/sw.js $(BUILD)/icon.svg
	rm -f $(PAGES:%.tex=$(DOCS)/%.html) $(DOCS)/style.css $(DOCS)/abcjs-basic-min.js
	rm -f $(DOCS)/manifest.json $(DOCS)/sw.js $(DOCS)/icon.svg

## Print help message.
help:
		@echo ''
		@echo '${WHITE}Usage:${RESET}'
		@echo '  ${YELLOW}make${RESET} ${GREEN}<target>${RESET}'
		@echo ''
		@echo '${WHITE}Targets:${RESET}'
		@echo ''
		@awk '/^[a-zA-Z\-\_0-9]+:|^all.*:/ { \
				helpMessage = match(lastLine, /^## (.*)/); \
				if (helpMessage) { \
						helpCommand = substr($$1, 0, index($$1, ":")-1); \
						helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
						if ("" == helpCommand) { \
							helpCommand = "(none)" \
						} \
						printf "  ${YELLOW}%-$(TARGET_MAX_CHAR_NUM)s${RESET} \n\t${GREEN}%s${RESET}\n", helpCommand, helpMessage; \
				} \
		} \
		{ lastLine = $$0 }' $(MAKEFILE_LIST)
