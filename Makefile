.PHONY: default
default: help

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help                   Show this help message"
	@echo "  fix                    Format source code"
	@echo "  check                  Run checks"
	@echo "  test                   Run tests"
	@echo "  examples               Run example scripts and generate output files"
	@echo "  docs                   Build documentation"
	@echo "  docs-clean             Clean documentation build"
	@echo "  sdist                  Build source distribution"

.PHONY: fix
fix:
	uv run hatch run quality:format

.PHONY: check
check:
	uv run hatch run quality:check
	uv run hatch run quality:typecheck

.PHONY: test
test:
	uv run hatch run tests:run

.PHONY: test-snapshot
test-snapshot:
	uv run hatch run tests:run-snapshot

.PHONY: examples
examples:
	@echo "Running example scripts and generating output files..."
	@mkdir -p examples/output
	@echo "Running Illumina v1 example..."
	uv run python examples/read_illumina_v1.py > examples/output/illumina_v1_output.txt
	@echo "Running Aviti example..."
	uv run python examples/read_aviti.py > examples/output/aviti_output.txt
	@echo "Example outputs generated in examples/output/"
	@echo "  - illumina_v1_output.txt"
	@echo "  - aviti_output.txt"

.PHONY: docs
docs:
	uv run hatch run docs:build

.PHONY: docs-clean
docs-clean:
	uv run hatch run docs:clean

.PHONY: sdist
sdist:
	uv run hatch run build:run
