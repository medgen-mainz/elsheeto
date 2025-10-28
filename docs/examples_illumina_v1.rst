Illumina v1 Sample Sheet Example
=================================

This example demonstrates how to parse an Illumina v1 sample sheet using elsheeto and extract key information including header metadata and sample details.

Sample Sheet Format
-------------------

Illumina v1 sample sheets are organized into sections:

* **[Header]**: Experiment metadata and configuration
* **[Reads]**: Read length specifications
* **[Settings]**: Runtime settings (optional)
* **[Data]**: Sample information with indexing details

Example Script
--------------

Here's the complete example script (``examples/read_illumina_v1.py``):

.. literalinclude:: ../examples/read_illumina_v1.py
   :language: python
   :linenos:

Key Features Demonstrated
-------------------------

Import and Parsing
~~~~~~~~~~~~~~~~~~~

The script uses the simple facade function:

.. code-block:: python

   from elsheeto import parse_illumina_v1
   sample_sheet = parse_illumina_v1(sample_sheet_path)

This single function call handles the entire three-stage parsing process.

Header Information Access
~~~~~~~~~~~~~~~~~~~~~~~~~

The parsed header provides access to experiment metadata:

.. code-block:: python

   header = sample_sheet.header
   print(f"Date: {header.date}")
   print(f"Experiment Name: {header.experiment_name}")
   print(f"Description: {header.description}")

Sample Data Processing
~~~~~~~~~~~~~~~~~~~~~~

Individual samples can be accessed and processed:

.. code-block:: python

   for sample in sample_sheet.data:
       print(f"Sample ID: {sample.sample_id}")
       print(f"Index: {sample.index}")
       print(f"Index2: {sample.index2}")

Index Analysis
~~~~~~~~~~~~~~

The script demonstrates how to analyze indexing patterns:

.. code-block:: python

   indexed_samples = [s for s in sample_sheet.data if s.index]
   dual_indexed_samples = [s for s in sample_sheet.data if s.index and s.index2]

Sample Data File
----------------

The example uses ``illumina_v1_example1.csv``:

.. literalinclude:: ../examples/illumina_v1_example1.csv
   :language: text
   :linenos:

Expected Output
---------------

When you run the example script, you should see output like this:

.. literalinclude:: ../examples/output/illumina_v1_output.txt
   :language: text

Key Output Sections
~~~~~~~~~~~~~~~~~~~

1. **Header Information**: Date, experiment name, description, and technical details
2. **Sample Information**: Complete list of all samples with their metadata
3. **Index Summary**: Statistics about indexing patterns used in the experiment

The output shows:

* **4 dual-indexed samples** with both I7 and I5 indices
* **Index adapter IDs** AD81-AD84 for systematic indexing
* **Complete sample metadata** including projects and descriptions

Error Handling
--------------

The script includes proper error handling:

.. code-block:: python

   try:
       sample_sheet = parse_illumina_v1(sample_sheet_path)
   except Exception as e:
       print(f"Error parsing sample sheet: {e}")
       return

This ensures graceful handling of malformed files or parsing issues.

Running the Example
-------------------

You can run this example in several ways:

.. code-block:: bash

   # Using uv (recommended)
   uv run python examples/read_illumina_v1.py

   # Or generate output file
   make examples

   # Direct execution (if elsheeto is installed)
   python examples/read_illumina_v1.py

The example demonstrates elsheeto's type-safe parsing and shows how easy it is to extract meaningful information from Illumina sample sheets.
