# Project setup
PROJ      = worship
BUILD     = ./build
DOCS      = ./docs

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
	python3 tex2html.py morning.tex $(BUILD)/morning.html
	python3 tex2html.py midday.tex $(BUILD)/midday.html
	python3 tex2html.py evening.tex $(BUILD)/evening.html
	python3 tex2html.py night.tex $(BUILD)/night.html

## Remove generated HTML files.
clean-html:
	rm -f $(BUILD)/morning.html $(BUILD)/midday.html $(BUILD)/evening.html $(BUILD)/night.html $(BUILD)/style.css

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
