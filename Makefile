# All targets run through `uv` against the committed `uv.lock`, so local runs
# and CI resolve to byte-identical dependency sets.

SOURCES := src tests examples

.PHONY: default
default: help

.PHONY: help
help:
	@echo "Available targets:"
	@echo "  help                   Show this help message"
	@echo "  sync                   Install the locked dev environment"
	@echo "  fix                    Format source code"
	@echo "  check                  Run lint and type checks"
	@echo "  test                   Run tests"
	@echo "  examples               Run example scripts and generate output files"
	@echo "  docs                   Build documentation"
	@echo "  docs-clean             Clean documentation build"
	@echo "  build                  Build sdist and wheel"
	@echo "  check-package          Build and verify the distribution artifacts"

.PHONY: sync
sync:
	uv sync --locked --all-groups

.PHONY: fix
fix:
	uv run black $(SOURCES)
	uv run ruff check --fix --unsafe-fixes $(SOURCES)
	$(MAKE) check

.PHONY: check
check:
	uv lock --check
	uv run black --check --diff --preview $(SOURCES)
	uv run ruff check $(SOURCES)
	uv run pyright $(SOURCES)

.PHONY: test
test:
	uv run pytest --cov=src/elsheeto --cov-report=term-missing --durations 5 -s tests/ src/elsheeto

.PHONY: test-snapshot
test-snapshot:
	uv run pytest --cov=src/elsheeto --cov-report=term-missing --durations 5 -s --snapshot-update tests/ src/elsheeto

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
	uv run sphinx-build -b html docs docs/_build/html

.PHONY: docs-clean
docs-clean:
	rm -rf docs/_build

.PHONY: docs-serve
docs-serve:
	uv run python -m http.server 8000 --directory docs/_build/html

.PHONY: build
build:
	rm -rf dist
	uv build

# Guards against the class of packaging bug where the sdist is malformed and a
# wheel rebuilt from it is empty but still installable.
.PHONY: check-package
check-package: build
	rm -rf dist-from-sdist
	uv build --wheel --out-dir dist-from-sdist dist/*.tar.gz
	uvx twine check dist/* dist-from-sdist/*
	uvx check-wheel-contents dist-from-sdist/*.whl
	uv run --isolated --no-project --with dist-from-sdist/*.whl \
		python -c "import elsheeto, pathlib; \
		assert (pathlib.Path(elsheeto.__file__).parent / 'py.typed').is_file(), 'py.typed missing from wheel'; \
		print('package OK:', elsheeto.__version__)"
