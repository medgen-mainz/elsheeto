Examples
========

This section provides comprehensive examples demonstrating how to use elsheeto to parse different types of sample sheets.

Overview
--------

The examples demonstrate:

* **Basic parsing**: Using the facade functions for simple parsing
* **Data extraction**: Accessing header information, settings, and sample data
* **Platform-specific features**: Handling unique features like Aviti's composite indices
* **Real-world scenarios**: Complete workflows from file to analysis

Each example includes:

* Complete, runnable Python scripts
* Step-by-step explanations
* Sample data files
* Expected output

Running the Examples
--------------------

All examples are available in the ``examples/`` directory of the elsheeto repository.
You can run them directly:

.. code-block:: bash

   # Run all examples and generate output files
   make examples

   # Or run individual examples
   uv run python examples/read_illumina_v1.py
   uv run python examples/read_aviti.py

The ``make examples`` command will create output files in ``examples/output/`` showing the results of parsing each sample sheet type.

Advanced Configuration
----------------------

Column Consistency Handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

elsheeto provides flexible handling of sample sheets with inconsistent column counts. This is particularly useful when working with real-world sample sheets that may have formatting inconsistencies.

.. code-block:: python

   from elsheeto import parse_illumina_v1
   from elsheeto.parser.common import ColumnConsistency, ParserConfiguration
   import warnings

   # Default behavior: warnings for inconsistencies with automatic padding
   sheet = parse_illumina_v1("samplesheet.csv")

   # Silent padding (no warnings)
   config = ParserConfiguration(column_consistency=ColumnConsistency.PAD)
   sheet = parse_illumina_v1("samplesheet.csv", config=config)

   # Strict validation (raises exceptions for inconsistencies)
   config = ParserConfiguration(column_consistency=ColumnConsistency.STRICT_SECTIONED)
   sheet = parse_illumina_v1("samplesheet.csv", config=config)

   # Capture warnings programmatically
   with warnings.catch_warnings(record=True) as w:
       warnings.simplefilter("always")
       sheet = parse_illumina_v1("samplesheet.csv")
       if w:
           for warning in w:
               print(f"Warning: {warning.message}")
