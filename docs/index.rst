Elsheeto Docs
=============

**elsheeto** is a Python library for parsing NGS sample sheets from Illumina and Element Biosciences Aviti platforms.
It provides type-annotated, validated models using Pydantic and supports a three-stage parsing architecture for robust data processing.

Features
--------

* **Multi-platform support**: Parse both Illumina v1 and Aviti sample sheets
* **Type safety**: Full type annotations with Pydantic validation
* **Three-stage parsing**: Raw CSV → Structured data → Platform-specific models
* **Robust error handling**: Comprehensive validation and error reporting
* **Flexible column consistency**: Automatic padding or strict validation modes
* **Easy-to-use API**: Simple facade functions for common use cases

Quick Start
-----------

Install elsheeto:

.. code-block:: bash

   pip install elsheeto

Parse an Illumina v1 sample sheet:

.. code-block:: python

   from elsheeto import parse_illumina_v1

   # Parse from file
   sheet = parse_illumina_v1("path/to/samplesheet.csv")

   # Access parsed data
   print(f"Experiment: {sheet.header.experiment_name}")
   print(f"Samples: {len(sheet.data)}")

Parse an Aviti sample sheet:

.. code-block:: python

   from elsheeto import parse_aviti

   # Parse from file
   sheet = parse_aviti("path/to/samplesheet.csv")

   # Access parsed data
   print(f"Samples: {len(sheet.samples)}")
   if sheet.settings:
       print(f"Settings: {sheet.settings.data}")

Architecture
------------

elsheeto uses a three-stage parsing architecture:

1. **Stage 1 (Raw CSV)**: Parse the raw CSV file into sectioned data
2. **Stage 2 (Structured)**: Convert sectioned data into key-value and tabular structures
3. **Stage 3 (Platform-specific)**: Transform into validated platform-specific models

This architecture ensures robust parsing and allows for easy extension to new platforms.

Column Consistency Modes
------------------------

elsheeto provides flexible handling of CSV files with inconsistent column counts:

* **WARN_AND_PAD (default)**: Automatically pads missing cells with empty strings and issues warnings
* **PAD**: Silently pads missing cells without warnings
* **STRICT_SECTIONED**: Requires consistent columns within each section (raises exceptions)
* **STRICT_GLOBAL**: Requires the same column count across all sections (raises exceptions)
* **LOOSE**: No consistency requirements

The default behavior changed from strict validation to warning-based padding to improve usability with real-world sample sheets that may have formatting inconsistencies.

.. code-block:: python

   from elsheeto import parse_illumina_v1
   from elsheeto.parser.common import ColumnConsistency, ParserConfiguration

   # Default: warnings for inconsistencies, automatic padding
   sheet = parse_illumina_v1("samplesheet.csv")

   # Silent padding (no warnings)
   config = ParserConfiguration(column_consistency=ColumnConsistency.PAD)
   sheet = parse_illumina_v1("samplesheet.csv", config=config)

   # Strict validation (old behavior)
   config = ParserConfiguration(column_consistency=ColumnConsistency.STRICT_SECTIONED)
   sheet = parse_illumina_v1("samplesheet.csv", config=config)

Table of Contents
-----------------

.. toctree::
    :maxdepth: 1
    :caption: Contents

    self

.. toctree::
    :maxdepth: 1
    :caption: Examples

    examples
    examples_aviti
    examples_illumina_v1

.. toctree::
    :maxdepth: 1
    :caption: API Docs

    api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
