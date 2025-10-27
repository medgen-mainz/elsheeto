# GitHub Copilot Instructions for Library Development

This document guides GitHub Copilot usage for this library, focusing on building a robust, type-safe, well-tested, and maintainable Python 3.13+ library for bioinformatics sample sheet parsing (Illumina, Element Biosciences Aviti).

Copilot suggestions must be critically reviewed for adherence to these principles.

---

## 1. Core Principles

- **Readability**: Code must be clear, concise, and easy to understand. Prioritize explicit over implicit.
- **Modularity**: Functions and classes should have single responsibilities.
- **Pythonic**: Leverage Python's idioms and standard library features.
- **Performance**: Consider performance implications, especially for large files.
- **Security**: Be aware of potential vulnerabilities (e.g., file I/O).

---

## 2. Type Safety & Validation (Pydantic & Mypy)

This library strongly emphasizes type safety and data validation.

- **Type Hints**: Always use type hints for arguments, return values, and attributes. Utilize `typing` module for complex types.
  - **Copilot**: Proactively suggest type hints.
- **Pydantic Models**:
  - All data structures representing parsed sample sheet content **must** use Pydantic `BaseModel`s.
  - Use `pydantic.Field` with `description`.
  - Leverage `@validator` and `@field_validator` for data cleansing, transformation, and custom validation (e.g., splitting composite platform-specific indices, DNA sequence validation).
  - **Copilot**: Prioritize Pydantic `BaseModel` definitions with appropriate fields and validators.
- **Pyright Compliance**: The codebase aims for 100% `pyright` compliance.
  - **Copilot**: Avoid suggestions that introduce type errors.

---

## 3. Testing (Pytest & TDD)

All new features and bug fixes require comprehensive tests.

- **Pytest**: All tests use `pytest`. Use fixtures for setup/teardown and common test data.
  - **Copilot**: When generating code, suggest corresponding test cases using `pytest`. Focus on edge cases and invalid inputs.
- **Coverage**: Aim for high test coverage.
- **Mocking**: Use `unittest.mock` for isolating units.
- **Realistic Data**: Use realistic (anonymized/simplified) sample sheet examples in tests.

---

## 4. Architecture Adherence (Three-Stage Parsing)

Adhere strictly to the three-stage parsing architecture:

- **Stage 1: Raw Sectioned Data Parsing**:
  - Focus on reading the file, splitting by sections, and segmenting rows/cells as raw strings into a generic Pydantic model for sectioned data.
  - **Copilot**: Generate code populating this generic sectioned data model with `str` values.
- **Stage 2: Structured Section Content Interpretation**:
  - Transform raw sections into either key-value structures (Dict[str, str]) or tabular structures (List[Dict[str, str]]) within a Pydantic model for structured sample sheet content.
  - **Copilot**: Assist in writing logic to determine section types and populate this structured content model.
- **Stage 3: Platform-Specific Validated Models**:
  - Apply domain-specific knowledge and strict validation, converting the structured content into platform-specific Pydantic models (e.g., for Illumina v1, Illumina v2, or Aviti).
  - **Copilot**: Generate platform-specific Pydantic models with specific fields, types (e.g., `List[str]` for Aviti's composite indices), and custom validators.
  - **Type Identification**: Suggest logic to identify the sample sheet type (Illumina v1/v2, Aviti) based on header information.

---

## 5. Documentation

- **Docstrings**: All modules, classes, methods, and functions **must** have clear, concise docstrings following the Google style guide.
  - **Copilot**: Generate comprehensive docstrings including `Args:`, `Returns:`, and `Raises:` sections.
- **Comments**: Use sparingly to explain _why_, not _what_.

---

## 6. Code Style & Formatting

- **PEP 8**: Adhere to PEP 8.
- **Linters/Formatters**: The project uses `black` and `flake8`.
  - **Copilot**: Generate code that `black` would format correctly and `flake8` would pass.

---

## 7. Context Reminders

- **Composite Aviti Indexes**: Aviti's `Index1`/`Index2` can contain `+` separated sequences (e.g., `ATGC+TCGA`). This requires explicit splitting/handling within the relevant Aviti sample Pydantic model using a validator.
- **Case Sensitivity**: Be mindful of field names (e.g., `SampleName`, `Sample_ID`).
- **Optional Fields**: Model appropriately with `Optional[Type]` or default values.
- **Comments in Files**: Parsers must correctly ignore comments (e.g., lines starting with `#`).
- **CSV Quoting**: Stage 1 parsing logic must handle quoted fields correctly.

---

## 8. Copilot's Proactive Assistance

- **Suggest Refactors**: Identify and suggest opportunities for cleaner, more modular code.
- **Error Handling**: Proactively suggest appropriate error handling (e.g., custom exceptions).
- **Missing Tests**: Suggest creating tests for functions/classes lacking coverage.
- **Pydantic Model Completion**: Suggest relevant fields for Pydantic models based on common formats.

---

## 9. Tools

You can use the following `make` targets:

- `make check`: Run linters to check code style and type annotations.
- `make fix`: Automatically format code using `black` and `ruff`.
- `make test`: Run all tests using `pytest`.
