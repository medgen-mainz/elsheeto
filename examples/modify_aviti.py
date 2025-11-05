#!/usr/bin/env python3
"""Example script demonstrating Aviti sample sheet modification and writing.

This script shows common patterns for modifying Aviti sample sheets using
the new builder pattern and fluent API, then writing them back to CSV format.
"""

from pathlib import Path

from elsheeto.facade import parse_aviti, write_aviti_to_file, write_aviti_to_string
from elsheeto.models.aviti import (
    AvitiSample,
    AvitiSettingEntry,
    AvitiSheet,
    AvitiSheetBuilder,
)
from elsheeto.writer.base import WriterConfiguration


def example_create_from_scratch():
    """Example: Create a new Aviti sample sheet from scratch using the builder pattern."""
    print("=== Creating a new Aviti sample sheet from scratch ===")

    # Use the builder pattern for complex sheet construction
    builder = AvitiSheetBuilder()

    sheet = (
        builder
        # Add run values (metadata about the sequencing run)
        .add_run_value("Experiment", "EXAMPLE_001")
        .add_run_value("Date", "2024-01-15")
        .add_run_value("Operator", "Lab_Tech_01")
        # Add settings (sequencing parameters)
        .add_setting("ReadLength", "150")
        .add_setting("Cycles", "300", "1+2")  # Lane-specific setting
        .add_setting("IndexLength", "8")
        # Add samples
        .add_sample(
            AvitiSample(
                sample_name="Sample_001",
                index1="ATCGATCG",
                index2="GCTAGCTA",
                lane="1",
                project="Project_Alpha",
                external_id="EXT_001",
                description="Control sample",
            )
        )
        .add_sample(
            AvitiSample(
                sample_name="Sample_002",
                index1="CGTAGCTA",
                index2="ATCGATCG",
                lane="1",
                project="Project_Alpha",
                external_id="EXT_002",
                description="Treatment sample",
            )
        )
        .add_sample(
            AvitiSample(
                sample_name="Sample_003",
                index1="ATCG+GCTA",  # Composite index
                index2="TTTT+AAAA",  # Composite index
                lane="2",
                project="Project_Beta",
            )
        )
        # Build the immutable sheet
        .build()
    )

    # Export to CSV
    csv_content = sheet.to_csv()
    print("Generated CSV content:")
    print(csv_content)

    return sheet


def example_modify_existing():
    """Example: Load, modify, and save an existing sample sheet using fluent API."""
    print("\n=== Modifying an existing sample sheet ===")

    # First, create a sample sheet (normally you'd load from file)
    original_sheet = (
        AvitiSheetBuilder()
        .add_sample(AvitiSample(sample_name="Old_Sample_1", index1="AAAA", project="OldProject"))
        .add_sample(AvitiSample(sample_name="Old_Sample_2", index1="TTTT", project="OldProject"))
        .add_run_value("OriginalExperiment", "OLD_001")
        .build()
    )

    print("Original sheet has", len(original_sheet.samples), "samples")

    # Apply modifications using fluent API (for simple changes)
    modified_sheet = (
        original_sheet
        # Add a new sample
        .with_sample_added(AvitiSample(sample_name="New_Sample", index1="CCCC", index2="GGGG", project="NewProject"))
        # Modify an existing sample
        .with_sample_modified("Old_Sample_1", project="UpdatedProject", lane="1")
        # Remove a sample
        .with_sample_removed("Old_Sample_2")
        # Add run values
        .with_run_value_added("ModificationDate", "2024-01-15").with_run_values_updated(
            {"Status": "Modified", "Version": "2.0"}
        )
        # Add settings
        .with_setting_added("NewSetting", "NewValue", "1+2")
    )

    print("Modified sheet has", len(modified_sheet.samples), "samples")
    print("Modified samples:")
    for sample in modified_sheet.samples:
        print(f"  - {sample.sample_name}: project={sample.project}, lane={sample.lane}")

    # Export the modified sheet
    csv_content = write_aviti_to_string(modified_sheet)
    print("\nModified CSV (first 500 chars):")
    print(csv_content[:500] + "..." if len(csv_content) > 500 else csv_content)

    return modified_sheet


def example_complex_modifications():
    """Example: Complex modifications using builder pattern for batch operations."""
    print("\n=== Complex modifications using builder pattern ===")

    # Start with an existing sheet
    original_sheet = (
        AvitiSheetBuilder()
        .add_samples(
            [AvitiSample(sample_name=f"Sample_{i:03d}", index1="ATCG", project="BatchProject") for i in range(1, 6)]
        )
        .build()
    )

    print(f"Starting with {len(original_sheet.samples)} samples")

    # Use builder for complex batch operations
    builder = AvitiSheetBuilder.from_sheet(original_sheet)

    # Remove samples by project
    builder.remove_samples_by_project("BatchProject")

    # Add new batch of samples with different configurations
    new_samples = []
    for i in range(1, 4):
        sample = AvitiSample(
            sample_name=f"NewBatch_{i:03d}",
            index1=f"{'ATCG' * (i % 3 + 1)}",  # Variable length indices
            index2=f"{'GCTA' * (i % 2 + 1)}",
            lane=str((i % 2) + 1),
            project="NewBatchProject",
            description=f"Batch sample {i}",
        )
        new_samples.append(sample)

    builder.add_samples(new_samples)

    # Add comprehensive run values
    builder.add_run_values(
        {
            "BatchExperiment": "BATCH_001",
            "ProcessingDate": "2024-01-15",
            "TechnicalReplicate": "Yes",
            "QualityControl": "Passed",
        }
    )

    # Add multiple settings
    builder.add_settings(
        [
            AvitiSettingEntry(name="ReadLength", value="150"),
            AvitiSettingEntry(name="IndexLength", value="8"),
            AvitiSettingEntry(name="ClusterDensity", value="200", lane="1"),
            AvitiSettingEntry(name="ClusterDensity", value="250", lane="2"),
        ]
    )

    final_sheet = builder.build()

    print(f"Final sheet has {len(final_sheet.samples)} samples")
    print("Run values:")
    if final_sheet.run_values:
        for key, value in final_sheet.run_values.data.items():
            print(f"  {key}: {value}")

    return final_sheet


def example_file_operations():
    """Example: Working with files - read, modify, write."""
    print("\n=== File operations example ===")

    # Create a sample sheet
    sheet = (
        AvitiSheetBuilder()
        .add_sample(AvitiSample(sample_name="FileTest", index1="ATCG"))
        .add_run_value("FileExperiment", "FILE_001")
        .build()
    )

    # Write to file
    output_path = Path("example_output.csv")
    write_aviti_to_file(sheet, output_path)
    print(f"Wrote sample sheet to {output_path}")

    # Read back from file
    if output_path.exists():
        loaded_sheet = parse_aviti(output_path)
        print(f"Loaded sheet with {len(loaded_sheet.samples)} samples")

        # Modify and save again
        modified_sheet = loaded_sheet.with_sample_added(AvitiSample(sample_name="AddedSample", index1="GCTA"))

        modified_path = Path("example_modified.csv")
        write_aviti_to_file(modified_sheet, modified_path)
        print(f"Wrote modified sheet to {modified_path}")

        # Clean up
        output_path.unlink()
        modified_path.unlink()
        print("Cleaned up example files")


def example_advanced_filtering():
    """Example: Advanced sample filtering and manipulation."""
    print("\n=== Advanced filtering and manipulation ===")

    # Create a diverse set of samples
    samples = [
        AvitiSample(sample_name="Control_1", index1="AAAA", project="Control", lane="1"),
        AvitiSample(sample_name="Control_2", index1="TTTT", project="Control", lane="1"),
        AvitiSample(sample_name="Treatment_1", index1="CCCC", project="Treatment", lane="2"),
        AvitiSample(sample_name="Treatment_2", index1="GGGG", project="Treatment", lane="2"),
        AvitiSample(sample_name="QC_Sample", index1="ATCG", project="QualityControl", lane="1"),
    ]

    sheet = AvitiSheet(samples=samples)
    print(f"Original sheet: {len(sheet.samples)} samples")

    # Filter to keep only treatment samples
    treatment_only = sheet.with_samples_filtered(lambda s: s.project == "Treatment")
    print(f"Treatment samples only: {len(treatment_only.samples)} samples")

    # Filter to keep only lane 1 samples
    lane1_only = sheet.with_samples_filtered(lambda s: s.lane == "1")
    print(f"Lane 1 samples only: {len(lane1_only.samples)} samples")

    # Complex filtering: Control or QC samples in lane 1
    filtered_sheet = sheet.with_samples_filtered(lambda s: s.lane == "1" and s.project in ["Control", "QualityControl"])
    print(f"Control/QC in lane 1: {len(filtered_sheet.samples)} samples")

    for sample in filtered_sheet.samples:
        print(f"  - {sample.sample_name} ({sample.project})")


def example_writer_configuration():
    """Example: Using writer configuration options."""
    print("\n=== Writer configuration example ===")

    sheet = (
        AvitiSheetBuilder()
        .add_sample(AvitiSample(sample_name="ConfigTest", index1="ATCG"))
        .add_run_value("Test", "Value")
        .build()
    )

    # Default configuration
    default_csv = sheet.to_csv()
    print("Default CSV format (with empty lines):")
    print(repr(default_csv))

    # Configuration without empty lines
    compact_config = WriterConfiguration(include_empty_lines=False)
    compact_csv = sheet.to_csv(compact_config)
    print("\nCompact CSV format (no empty lines):")
    print(repr(compact_csv))


def main():
    """Run all examples."""
    print("Aviti Sample Sheet Modification Examples")
    print("=" * 50)

    try:
        # Run examples
        example_create_from_scratch()
        example_modify_existing()
        example_complex_modifications()
        example_file_operations()
        example_advanced_filtering()
        example_writer_configuration()

        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nKey takeaways:")
        print("- Use AvitiSheetBuilder for complex sheet construction")
        print("- Use fluent API (with_*) methods for simple modifications")
        print("- All operations preserve immutability")
        print("- Round-trip parsing works: parse → modify → write → parse")
        print("- Writer configuration allows format customization")

    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure the elsheeto package is installed and available")
    except Exception as e:
        print(f"Error running examples: {e}")
        raise


if __name__ == "__main__":
    main()
