# Included custom configs change the value of MAKEFILE_LIST
# Extract the required reference beforehand so we can use it for help target
MAKEFILE_NAME := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
# Include custom config if it is available
-include Makefile.config

APP_ROOT := $(abspath $(lastword $(MAKEFILE_NAME))/..)
APP_NAME := $(shell basename $(APP_ROOT))

filter_out_substr = $(foreach v,$(2),$(if $(findstring $(1),$(v)),,$(v)))
CWL_CLI_SOURCES := $(wildcard $(APP_ROOT)/src/$(APP_NAME)/processes/*/*.py)
CWL_CLI_SOURCES := $(call filter_out_substr,test, $(CWL_CLI_SOURCES))
CWL_CLI_OUTPUTS := $(CWL_CLI_SOURCES:.py=.cwl)

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help               - Show this help message"
	@echo "  info               - Display computed variables"
	@echo "  install            - Install dependencies"
	@echo "  cwl-generate       - Generate CWL files from Python processes"
	@echo "  cwl-generate-only  - Generate CWL files without installing dependencies"

.PHONY: info
info:
	@echo "APP_ROOT:        [" $(APP_ROOT) "]"
	@echo "CWL_CLI_SOURCES: [" $(CWL_CLI_SOURCES) "]"
	@echo "CWL_CLI_OUTPUTS: [" $(CWL_CLI_OUTPUTS) "]"

.PHONY: install
install:
	@echo "Installing dependencies..."
	@pip install ".[processes]"

# For each Python file, generate the corresponding CWL file
%.cwl: %.py
	@echo "Generating CWL for [$<]..."
	click2cwl --process $< --output $@

.PHONY: cwl-generate-only
cwl-generate-only: $(CWL_CLI_OUTPUTS)

.PHONY: cwl-generate
cwl-generate: cwl-generate-only | install
