#!/usr/bin/env python3
"""Quick start example for Aviti sample sheet modification.

This is a simple introduction to the key features for modifying Aviti sample sheets.
For more comprehensive examples, see modify_aviti.py.
"""

from elsheeto.facade import write_aviti_to_string
from elsheeto.models.aviti import AvitiSample, AvitiSheetBuilder


def quick_start_example():
    """Quick demonstration of key modification features."""
    print("Quick Start: Aviti Sample Sheet Modification")
    print("=" * 50)

    # 1. Create a new sample sheet from scratch
    print("\n1. Creating a new sample sheet:")
    sheet = (
        AvitiSheetBuilder()
        .add_run_value("Experiment", "QS_001")
        .add_setting("ReadLength", "150")
        .add_sample(AvitiSample(sample_name="Sample_A", index1="ATCGATCG", project="ProjectAlpha"))
        .add_sample(AvitiSample(sample_name="Sample_B", index1="CGTAGCTA", project="ProjectAlpha"))
        .build()
    )

    print(f"Created sheet with {len(sheet.samples)} samples")

    # 2. Make simple modifications using fluent API
    print("\n2. Making simple modifications:")
    modified_sheet = (
        sheet.with_sample_added(AvitiSample(sample_name="Sample_C", index1="TTTTAAAA", project="ProjectBeta"))
        .with_sample_modified("Sample_A", lane="1", description="Control")
        .with_run_value_added("Status", "Modified")
    )

    print(f"Modified sheet now has {len(modified_sheet.samples)} samples")
    for sample in modified_sheet.samples:
        desc = f" ({sample.description})" if sample.description else ""
        lane = f", lane {sample.lane}" if sample.lane else ""
        print(f"  - {sample.sample_name}: {sample.project}{lane}{desc}")

    # 3. Export to CSV
    print("\n3. Exporting to CSV:")
    csv_content = write_aviti_to_string(modified_sheet)
    print("Generated CSV content:")
    print(csv_content)

    # 4. Parse and modify existing files (if you have one)
    print("\n4. Working with existing files:")
    print("To modify an existing file:")
    print("  sheet = parse_aviti('path/to/existing.csv')")
    print("  modified = sheet.with_sample_added(...)")
    print("  write_aviti_to_file(modified, 'path/to/output.csv')")


if __name__ == "__main__":
    quick_start_example()
