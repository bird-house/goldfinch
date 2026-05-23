# Included custom configs change the value of MAKEFILE_LIST
# Extract the required reference beforehand so we can use it for help target
MAKEFILE_NAME := $(word $(words $(MAKEFILE_LIST)),$(MAKEFILE_LIST))
# Include custom config if it is available
-include Makefile.config

APP_ROOT := $(abspath $(lastword $(MAKEFILE_NAME))/..)
APP_NAME := $(shell basename $(APP_ROOT))
APP_VERSION := 0.1.0
APP_DOCKER_VERSION := ghcr.io/bird-house/$(APP_NAME)
APP_DOCKER_REGISTRY := ghcr.io/bird-house/$(APP_NAME)
APP_DOCKER_IMAGE := $(APP_DOCKER_REGISTRY):$(APP_VERSION)

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
	@echo "  install-dev        - Install development dependencies"
	@echo "  check-only         - Run linting checks"
	@echo "  check              - Install dev dependencies and run linting checks"
	@echo "  fix-only           - Fix linting issues"
	@echo "  fix                - Install dev dependencies and fix linting issues"
	@echo "  test-only          - Run tests"
	@echo "  test               - Install dev dependencies and run tests"
	@echo "  clean-build        - Remove build artifacts"
	@echo "  clean-cov          - Remove coverage artifacts"
	@echo "  clean              - Run cleanup targets"
	@echo "  cwl-generate-only  - Generate CWL files without installing dependencies"
	@echo "  cwl-generate       - Install dependencies and generate CWL files"
	@echo "  cwl-generate-all   - Force regeneration of all CWL files"
	@echo "  docker-build       - Build Docker image"

.PHONY: info
info:
	@echo "APP_VERSION:     [" $(APP_VERSION) "]"
	@echo "APP_ROOT:        [" $(APP_ROOT) "]"
	@echo "CWL_CLI_SOURCES: [" $(CWL_CLI_SOURCES) "]"
	@echo "CWL_CLI_OUTPUTS: [" $(CWL_CLI_OUTPUTS) "]"

.PHONY: install
install:
	@echo "Installing dependencies..."
	@pip install ".[processes]"

.PHONY: install-dev
install-dev: install
	@echo "Installing development dependencies..."
	@pip install ".[dev,processes]"

.PHONY: check-only
check-only:
	@echo "Running linting checks..."
	@ruff check "$(APP_ROOT)" $(RUFF_XARGS)

.PHONY: check
check: install-dev check-only

.PHONY: fix-only
fix-only:
	@echo "Fixing linting issues..."
	@ruff check --fix "$(APP_ROOT)" $(RUFF_XARGS)

.PHONY: fix
fix: install-dev fix-only

.PHONY: test-only
test-only:
	@echo "Running tests..."
	@pytest "$(APP_ROOT)"

.PHONY: test
test: install-dev test-only

.PHONY: clean-build
clean-build:
	@echo "Cleaning build artifacts..."
	@find "$(APP_ROOT)" -type d \( -name "build" -o -name "dist" -o -name "*.egg-info" \) -prune -exec rm -rf {} +
	@find "$(APP_ROOT)" -type f \( -name "*.egg" -o -name "*.whl" \) -delete

.PHONY: clean-cov
clean-cov:
	@echo "Cleaning coverage artifacts..."
	@find "$(APP_ROOT)" -type f \( -name ".coverage" -o -name ".coverage.*" -o -name "coverage.xml" \) -delete
	@find "$(APP_ROOT)" -type d -name "htmlcov" -prune -exec rm -rf {} +

.PHONY: clean
clean: clean-cov clean-build

# For each Python file, generate the corresponding CWL file
# Will only run modified Python files by default
# All process modules expose the entrypoint command as 'cli'.
# Some modules (for example chain.py) define multiple Click commands, so this avoids ambiguity for command selection.
%.cwl: %.py
	@echo "Generating CWL for [$<]..."
	click2cwl \
		--process $< \
		--command cli \
		--output-cwl $@ \
		--docker "$(APP_DOCKER_IMAGE)" \
		--cwl-version v1.2 \
		--metadata "id=$(@F:.cwl=)"

.PHONY: cwl-generate-only
cwl-generate-only: $(CWL_CLI_OUTPUTS)

.PHONY: cwl-generate
cwl-generate: cwl-generate-only | install

.PHONY: cwl-generate-all
cwl-generate-all:
	$(MAKE) $(foreach file,$(CWL_CLI_SOURCES),-W $(file)) cwl-generate-only

.PHONY: docker-build
docker-build:
	@echo "Building Docker image..."
	docker build -t "$(APP_DOCKER_IMAGE)" -f "$(APP_ROOT)/docker/Dockerfile" "$(APP_ROOT)"
