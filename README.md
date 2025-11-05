[![PyPI - Version](https://img.shields.io/pypi/v/elsheeto)](http://pypi.org/project/elsheeto/)
[![PyPI - Types](https://img.shields.io/pypi/types/elsheeto)](http://pypi.org/project/elsheeto/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/elsheeto)](http://pypi.org/project/elsheeto/)
[![CI](https://github.com/medgen-mainz/elsheeto/actions/workflows/main.yml/badge.svg)](https://github.com/medgen-mainz/elsheeto/actions/workflows/main.yml)
[![docs](https://app.readthedocs.org/projects/elsheeto/badge/?version=latest)](https://elsheeto.readthedocs.io/en/latest/)

# El Sheeto

I/O and models in type-annotated Python for NGS sample sheets: Illumina (v1) and Aviti

- Python: 3.13+
- License: MIT
- [Documentation at ReadTheDocs](https://elsheeto.readthedocs.io/en/latest/)

## Features

**Parsing & Reading:**
- Parse Illumina sample sheets (v1 format)
- Parse Aviti sample sheets (Sequencing Manifests) with composite index support
- Type-safe Pydantic models with comprehensive validation
- Three-stage parsing architecture for robust error handling

**Modification & Writing:**
- Modify existing sample sheets with fluent API
- Add, remove, and update samples, run values, and settings
- Builder pattern for complex sheet construction
- Export modified sheets back to CSV format
- Round-trip compatibility: parse → modify → write → parse

**Key Capabilities:**
- Composite index handling for Aviti (e.g., `ATCG+GCTA`)
- Case-insensitive field access
- Immutable data structures with modification methods
- 100% type coverage with mypy/pyright
- Comprehensive test suite

## Quick Start

### Parsing Sample Sheets

```python
from elsheeto import parse_aviti, parse_illumina_v1

# Parse Aviti sample sheet
aviti_sheet = parse_aviti("sequencing_manifest.csv")
print(f"Found {len(aviti_sheet.samples)} samples")

# Parse Illumina v1 sample sheet
illumina_sheet = parse_illumina_v1("sample_sheet.csv")
print(f"Found {len(illumina_sheet.samples)} samples")
```

### Modifying Sample Sheets

```python
from elsheeto import parse_aviti, write_aviti_to_file
from elsheeto.models.aviti import AvitiSample

# Load and modify existing sheet
sheet = parse_aviti("experiment.csv")
modified_sheet = (sheet
    .with_sample_added(AvitiSample(
        sample_name="New_Sample",
        index1="ATCGATCG",
        project="MyProject"
    ))
    .with_sample_modified("Old_Sample", project="UpdatedProject")
    .with_run_value_added("ModificationDate", "2024-01-15")
)

# Write back to file
write_aviti_to_file(modified_sheet, "modified_experiment.csv")
```

### Creating New Sample Sheets

```python
from elsheeto.models.aviti import AvitiSheetBuilder, AvitiSample

# Build new sheet from scratch
sheet = (AvitiSheetBuilder()
    .add_run_value("Experiment", "EXP_001")
    .add_setting("ReadLength", "150")
    .add_sample(AvitiSample(
        sample_name="Sample_1",
        index1="ATCGATCG",
        project="MyProject"
    ))
    .build())

# Export to CSV
csv_content = sheet.to_csv()
```

## Examples

See the `examples/` directory for comprehensive usage examples:

- `examples/quick_start_aviti.py` - Simple introduction to key features
- `examples/modify_aviti.py` - Complete modification guide with advanced patterns
- `examples/read_aviti.py` - Parsing and analysis examples
- `examples/read_illumina_v1.py` - Illumina v1 parsing examples

## Installation

```bash
pip install elsheeto
```

## Documentation

Complete documentation is available at [ReadTheDocs](https://elsheeto.readthedocs.io/en/latest/), including:

- [API Reference](https://elsheeto.readthedocs.io/en/latest/api.html)
- [Aviti Examples](https://elsheeto.readthedocs.io/en/latest/examples_aviti.html)
- [Illumina v1 Examples](https://elsheeto.readthedocs.io/en/latest/examples_illumina_v1.html)

## Contributing

Contributions are welcome! Please see the development setup in the repository for details on:

- Type safety requirements (100% mypy/pyright compliance)
- Testing with pytest
- Code formatting with black and ruff
- Three-stage parsing architecture
