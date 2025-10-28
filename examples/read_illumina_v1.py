#!/usr/bin/env python3
"""Example: Reading an Illumina v1 sample sheet.

This example demonstrates how to parse an Illumina v1 sample sheet and extract
key information including header metadata and sample details.

Usage:
    python examples/read_illumina_v1.py
    # or with uv:
    uv run python examples/read_illumina_v1.py
"""

from pathlib import Path

from elsheeto import parse_illumina_v1


def main():
    """Parse Illumina v1 sample sheet and display key information."""
    # Path to the example Illumina v1 sample sheet
    sample_sheet_path = Path(__file__).parent / "illumina_v1_example1.csv"

    # Get relative path from current working directory for display
    try:
        relative_path = sample_sheet_path.relative_to(Path.cwd())
    except ValueError:
        # Fallback to absolute path if relative path can't be computed
        relative_path = sample_sheet_path

    print(f"Reading Illumina v1 sample sheet: {relative_path}")
    print("=" * 60)

    # Parse the sample sheet using elsheeto's facade function
    try:
        sample_sheet = parse_illumina_v1(sample_sheet_path)
    except Exception as e:
        print(f"Error parsing sample sheet: {e}")
        return

    # Extract and display header information
    header = sample_sheet.header
    print("HEADER INFORMATION:")
    print("-" * 30)

    # Display date
    if header.date:
        print(f"Date: {header.date}")
    else:
        print("Date: Not specified")

    # Display experiment description
    if header.experiment_name:
        print(f"Experiment Name: {header.experiment_name}")
    else:
        print("Experiment Name: Not specified")

    if header.description:
        print(f"Description: {header.description}")
    else:
        print("Description: Not specified")

    # Display additional header fields
    print(f"Workflow: {header.workflow}")
    if header.application:
        print(f"Application: {header.application}")
    if header.instrument_type:
        print(f"Instrument Type: {header.instrument_type}")
    if header.assay:
        print(f"Assay: {header.assay}")

    print()

    # Display reads information
    if sample_sheet.reads:
        print("READS INFORMATION:")
        print("-" * 30)
        print(f"Read lengths: {sample_sheet.reads.read_lengths}")
        print()

    # Display sample information
    print("SAMPLE INFORMATION:")
    print("-" * 30)
    print(f"Total samples: {len(sample_sheet.data)}")
    print()

    # Display sample names and IDs
    print("Sample Details:")
    for i, sample in enumerate(sample_sheet.data, 1):
        sample_name = sample.sample_name or "(No name)"
        print(f"  {i:2d}. Sample ID: {sample.sample_id}")
        print(f"      Sample Name: {sample_name}")
        if sample.sample_project:
            print(f"      Project: {sample.sample_project}")
        if sample.description:
            print(f"      Description: {sample.description}")
        if sample.index:
            print(f"      Index: {sample.index}")
        if sample.index2:
            print(f"      Index2: {sample.index2}")
        print()

    # Display index information summary
    print("INDEX SUMMARY:")
    print("-" * 30)
    indexed_samples = [s for s in sample_sheet.data if s.index]
    dual_indexed_samples = [s for s in sample_sheet.data if s.index and s.index2]

    print(f"Samples with index: {len(indexed_samples)}")
    print(f"Samples with dual indexing: {len(dual_indexed_samples)}")

    if indexed_samples:
        print("Index adapters used:")
        unique_i7_ids = {s.i7_index_id for s in indexed_samples if s.i7_index_id}
        unique_i5_ids = {s.i5_index_id for s in indexed_samples if s.i5_index_id}
        if unique_i7_ids:
            print(f"  I7 Index IDs: {', '.join(sorted(unique_i7_ids))}")
        if unique_i5_ids:
            print(f"  I5 Index IDs: {', '.join(sorted(unique_i5_ids))}")


if __name__ == "__main__":
    main()
