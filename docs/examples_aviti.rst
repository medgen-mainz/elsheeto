Aviti Sample Sheet Example
==========================

This example demonstrates how to parse an Aviti sample sheet (Sequencing Manifest) using elsheeto and extract key information including settings, run values, and sample details with composite index handling.

Sample Sheet Format
-------------------

Aviti sample sheets (Sequencing Manifests) are organized into sections:

* **[Settings]**: Sequencing configuration parameters
* **[RunValues]**: Custom experiment metadata (optional)
* **[Samples]**: Sample information with indexing details

A key feature of Aviti sample sheets is support for **composite indices** using ``+`` separators (e.g., ``ATGT+CGCT``).

Example Script
--------------

Here's the complete example script (``examples/read_aviti.py``):

.. literalinclude:: ../examples/read_aviti.py
   :language: python
   :linenos:

Key Features Demonstrated
-------------------------

Import and Parsing
~~~~~~~~~~~~~~~~~~~

The script uses the simple facade function:

.. code-block:: python

   from elsheeto import parse_aviti
   sample_sheet = parse_aviti(sample_sheet_path)

This single function call handles the entire three-stage parsing process.

Run Values Access
~~~~~~~~~~~~~~~~~

Aviti sheets can contain custom experiment metadata:

.. code-block:: python

   if sample_sheet.run_values and sample_sheet.run_values.data:
       for key, value in sample_sheet.run_values.data.items():
           print(f"  {key}: {value}")

Settings Organization
~~~~~~~~~~~~~~~~~~~~~

The script categorizes settings for better readability:

.. code-block:: python

   # Group settings by category
   sequencing_settings = {}
   adapter_settings = {}
   other_settings = {}

   for key, value in sample_sheet.settings.data.items():
       if any(x in key.lower() for x in ['mask', 'fastq', 'mismatch', 'umi']):
           sequencing_settings[key] = value
       elif any(x in key.lower() for x in ['adapter', 'trim']):
           adapter_settings[key] = value
       else:
           other_settings[key] = value

Sample Categorization
~~~~~~~~~~~~~~~~~~~~~

The script intelligently categorizes samples:

.. code-block:: python

   # Categorize samples
   phix_samples = [s for s in sample_sheet.samples if "phix" in s.sample_name.lower()]
   regular_samples = [s for s in sample_sheet.samples if "phix" not in s.sample_name.lower()]

Composite Index Handling
~~~~~~~~~~~~~~~~~~~~~~~~~

A unique feature of Aviti is composite index support:

.. code-block:: python

   # Handle composite indices
   if "+" in sample.index1:
       index1_parts = sample.index1.split("+")
       print(f"      Index1 composite parts: {' + '.join(index1_parts)}")

Lane Range Processing
~~~~~~~~~~~~~~~~~~~~~

Aviti supports lane ranges like ``1+2``:

.. code-block:: python

   # Handle lane ranges like "1+2"
   if "+" in sample.lane:
       lanes_used.update(sample.lane.split("+"))
   else:
       lanes_used.add(sample.lane)

Sample Data File
----------------

The example uses ``aviti_example1.csv``:

.. literalinclude:: ../examples/aviti_example1.csv
   :language: text
   :linenos:

Expected Output
---------------

When you run the example script, you should see output like this:

.. literalinclude:: ../examples/output/aviti_output.txt
   :language: text

Key Output Sections
~~~~~~~~~~~~~~~~~~~

1. **Run Values**: Custom experiment metadata
2. **Settings**: Organized by category (General, Sequencing Configuration, Adapter Settings)
3. **Sample Information**: Separated into PhiX controls and regular samples
4. **Summary Statistics**: Analysis of indexing patterns and lane usage

The output shows:

* **6 total samples**: 4 PhiX controls + 2 regular samples
* **Dual indexing**: All samples have both Index1 and Index2
* **Lane configuration**: All samples run on lanes 1+2
* **Organized settings**: Grouped by function for easy reading

Advanced Features
-----------------

Composite Index Example
~~~~~~~~~~~~~~~~~~~~~~~

Here's how elsheeto handles composite indices. If you had a sample with:

.. code-block:: text

   SampleName,Index1,Index2
   CompositeSample,ATGT+CGCT,GGAA+TTCC

The script would output:

.. code-block:: text

   Sample Name: CompositeSample
   Index1: ATGT+CGCT
   Index1 composite parts: ATGT + CGCT
   Index2: GGAA+TTCC
   Index2 composite parts: GGAA + TTCC

Validation Features
~~~~~~~~~~~~~~~~~~~

elsheeto automatically validates:

* **Index sequences**: Ensures valid DNA sequences or alphanumeric IDs
* **Composite format**: Validates ``+`` separated composite indices
* **Required fields**: Ensures ``SampleName`` and ``Index1`` are present

Error Handling
--------------

The script includes proper error handling:

.. code-block:: python

   try:
       sample_sheet = parse_aviti(sample_sheet_path)
   except Exception as e:
       print(f"Error parsing sample sheet: {e}")
       return

This ensures graceful handling of malformed files or validation errors.

Running the Example
-------------------

You can run this example in several ways:

.. code-block:: bash

   # Using uv (recommended)
   uv run python examples/read_aviti.py

   # Or generate output file
   make examples

   # Direct execution (if elsheeto is installed)
   python examples/read_aviti.py

The example demonstrates elsheeto's advanced features including composite index handling, intelligent sample categorization, and comprehensive settings analysis.

Modifying Aviti Sample Sheets
-----------------------------

In addition to parsing, elsheeto provides powerful capabilities for modifying and writing Aviti sample sheets. This is useful for:

* Adding new samples to existing experiments
* Updating sample metadata (project names, descriptions, etc.)
* Removing samples that failed quality control
* Changing experimental parameters (run values, settings)

Quick Start: Simple Modifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For simple modifications, use the fluent API:

.. code-block:: python

   from elsheeto import parse_aviti, write_aviti_to_file
   from elsheeto.models.aviti import AvitiSample

   # Load existing sheet
   sheet = parse_aviti("experiment.csv")

   # Make modifications using fluent API
   modified_sheet = (sheet
       .with_sample_added(AvitiSample(
           sample_name="New_Sample",
           index1="ATCGATCG",
           project="NewProject"
       ))
       .with_sample_modified("Old_Sample", project="UpdatedProject")
       .with_run_value_added("ModificationDate", "2024-01-15")
   )

   # Write back to file
   write_aviti_to_file(modified_sheet, "modified_experiment.csv")

Complex Modifications: Builder Pattern
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For complex operations, use the builder pattern:

.. code-block:: python

   from elsheeto.models.aviti import AvitiSheetBuilder, AvitiSample

   # Create new sheet from scratch or modify existing
   builder = AvitiSheetBuilder()  # or AvitiSheetBuilder.from_sheet(existing_sheet)

   # Add multiple samples
   samples = [
       AvitiSample(sample_name=f"Sample_{i}", index1="ATCG", project="BatchProject")
       for i in range(1, 10)
   ]
   builder.add_samples(samples)

   # Add run values and settings
   builder.add_run_values({
       "Experiment": "BATCH_001",
       "Date": "2024-01-15"
   })
   builder.add_setting("ReadLength", "150")

   # Build the immutable sheet
   final_sheet = builder.build()

Modification Examples
~~~~~~~~~~~~~~~~~~~~~

See the comprehensive examples in:

* ``examples/quick_start_aviti.py``: Simple introduction to modification features
* ``examples/modify_aviti.py``: Complete guide with advanced patterns

Key modification features:

* **Immutable operations**: All modifications return new objects, preserving originals
* **Fluent API**: Chain multiple modifications for readable code
* **Batch operations**: Add/remove multiple samples efficiently
* **Round-trip compatibility**: Modified sheets parse correctly when re-read
* **Composite index support**: Full support for ``+`` separated indices
* **Validation**: All modifications are validated according to Aviti format requirements

Available Modification Methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Sample Operations:**

* ``with_sample_added(sample)`` - Add a new sample
* ``with_sample_modified(name, **kwargs)`` - Update sample fields
* ``with_sample_removed(name)`` - Remove a sample by name
* ``with_samples_filtered(predicate)`` - Keep only samples matching criteria

**Run Values Operations:**

* ``with_run_value_added(key, value)`` - Add single run value
* ``with_run_values_updated(dict)`` - Add/update multiple run values

**Settings Operations:**

* ``with_setting_added(name, value, lane=None)`` - Add setting entry

The modification system maintains full type safety and validation while providing both simple and advanced APIs for different use cases.
