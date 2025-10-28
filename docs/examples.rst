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
