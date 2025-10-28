#!/usr/bin/env python3
"""Example: Reading an Aviti sample sheet (Sequencing Manifest).

This example demonstrates how to parse an Aviti sample sheet and extract
key information including settings, run values, and sample details with
composite index handling.

Usage:
    python examples/read_aviti.py
    # or with uv:
    uv run python examples/read_aviti.py
"""

from pathlib import Path

from elsheeto import parse_aviti


def main():
    """Parse Aviti sample sheet and display key information."""
    # Path to the example Aviti sample sheet
    sample_sheet_path = Path(__file__).parent / "aviti_example1.csv"

    # Get relative path from current working directory for display
    try:
        relative_path = sample_sheet_path.relative_to(Path.cwd())
    except ValueError:
        # Fallback to absolute path if relative path can't be computed
        relative_path = sample_sheet_path

    print(f"Reading Aviti sample sheet: {relative_path}")
    print("=" * 65)

    # Parse the sample sheet using elsheeto's facade function
    try:
        sample_sheet = parse_aviti(sample_sheet_path)
    except Exception as e:
        print(f"Error parsing sample sheet: {e}")
        return

    # Display run values information
    if sample_sheet.run_values and sample_sheet.run_values.data:
        print("RUN VALUES:")
        print("-" * 35)
        for key, value in sample_sheet.run_values.data.items():
            print(f"  {key}: {value}")
        print()

    # Display settings information
    if sample_sheet.settings and sample_sheet.settings.data:
        print("SETTINGS:")
        print("-" * 35)

        # Group settings by category for better readability
        sequencing_settings = {}
        adapter_settings = {}
        other_settings = {}

        for key, value in sample_sheet.settings.data.items():
            if any(x in key.lower() for x in ["mask", "fastq", "mismatch", "umi"]):
                sequencing_settings[key] = value
            elif any(x in key.lower() for x in ["adapter", "trim"]):
                adapter_settings[key] = value
            else:
                other_settings[key] = value

        if other_settings:
            print("  General Settings:")
            for key, value in other_settings.items():
                print(f"    {key}: {value}")
            print()

        if sequencing_settings:
            print("  Sequencing Configuration:")
            for key, value in sequencing_settings.items():
                print(f"    {key}: {value}")
            print()

        if adapter_settings:
            print("  Adapter Settings:")
            for key, value in adapter_settings.items():
                print(f"    {key}: {value}")
            print()

    # Display sample information
    print("SAMPLE INFORMATION:")
    print("-" * 35)
    print(f"Total samples: {len(sample_sheet.samples)}")
    print()

    # Categorize samples
    phix_samples = [s for s in sample_sheet.samples if "phix" in s.sample_name.lower()]
    regular_samples = [s for s in sample_sheet.samples if "phix" not in s.sample_name.lower()]

    # Display PhiX control samples
    if phix_samples:
        print("PhiX Control Samples:")
        for i, sample in enumerate(phix_samples, 1):
            print(f"  {i:2d}. Sample Name: {sample.sample_name}")
            print(f"      Index1: {sample.index1}")
            print(f"      Index2: {sample.index2}")
            if sample.lane:
                print(f"      Lane: {sample.lane}")
            if sample.project:
                print(f"      Project: {sample.project}")

            # Handle composite indices
            if "+" in sample.index1:
                index1_parts = sample.index1.split("+")
                print(f"      Index1 composite parts: {' + '.join(index1_parts)}")
            if "+" in sample.index2:
                index2_parts = sample.index2.split("+")
                print(f"      Index2 composite parts: {' + '.join(index2_parts)}")
            print()

    # Display regular samples
    if regular_samples:
        print("Regular Samples:")
        for i, sample in enumerate(regular_samples, 1):
            print(f"  {i:2d}. Sample Name: {sample.sample_name}")
            print(f"      Index1: {sample.index1}")
            print(f"      Index2: {sample.index2}")
            if sample.lane:
                print(f"      Lane: {sample.lane}")
            if sample.project:
                print(f"      Project: {sample.project}")
            if sample.external_id:
                print(f"      External ID: {sample.external_id}")
            if sample.description:
                print(f"      Description: {sample.description}")

            # Handle composite indices
            if "+" in sample.index1:
                index1_parts = sample.index1.split("+")
                print(f"      Index1 composite parts: {' + '.join(index1_parts)}")
            if "+" in sample.index2:
                index2_parts = sample.index2.split("+")
                print(f"      Index2 composite parts: {' + '.join(index2_parts)}")
            print()

    # Display summary statistics
    print("SUMMARY STATISTICS:")
    print("-" * 35)

    # Lane analysis
    lanes_used = set()
    for sample in sample_sheet.samples:
        if sample.lane:
            # Handle lane ranges like "1+2"
            if "+" in sample.lane:
                lanes_used.update(sample.lane.split("+"))
            else:
                lanes_used.add(sample.lane)

    if lanes_used:
        print(f"Lanes used: {', '.join(sorted(lanes_used))}")

    # Index analysis
    dual_indexed_samples = [s for s in sample_sheet.samples if s.index2]
    composite_index1_samples = [s for s in sample_sheet.samples if "+" in s.index1]
    composite_index2_samples = [s for s in sample_sheet.samples if "+" in s.index2]

    print(f"PhiX control samples: {len(phix_samples)}")
    print(f"Regular samples: {len(regular_samples)}")
    print(f"Dual-indexed samples: {len(dual_indexed_samples)}")
    print(f"Samples with composite Index1: {len(composite_index1_samples)}")
    print(f"Samples with composite Index2: {len(composite_index2_samples)}")

    # Project analysis
    projects = {s.project for s in sample_sheet.samples if s.project}
    if projects:
        projects.discard("")  # Remove empty strings
        if projects:
            print(f"Projects: {', '.join(sorted(projects))}")


if __name__ == "__main__":
    main()
