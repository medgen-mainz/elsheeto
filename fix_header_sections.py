#!/usr/bin/env python3
"""Helper script to convert HeaderSection(key_values={...}) to HeaderSection(rows=[...])."""

import re
import sys

def convert_key_values_to_rows(content: str) -> str:
    """Convert HeaderSection(key_values={...}) to HeaderSection(rows=[...])."""

    # Pattern to match HeaderSection(key_values={...})
    pattern = r'HeaderSection\(\s*key_values\s*=\s*\{([^}]*)\}\s*\)'

    def replace_func(match):
        key_values_content = match.group(1).strip()

        if not key_values_content:
            return 'HeaderSection(rows=[])'

        # Parse the key-value pairs
        # This is a simple parser - for real production code, you'd want something more robust
        rows = []

        # Split by commas, but be careful of quoted strings
        pairs = []
        current_pair = ""
        in_quotes = False
        quote_char = None

        for char in key_values_content + ',':  # Add comma to ensure last pair is processed
            if char in ['"', "'"] and (not in_quotes or char == quote_char):
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                else:
                    in_quotes = False
                    quote_char = None
                current_pair += char
            elif char == ',' and not in_quotes:
                if current_pair.strip():
                    pairs.append(current_pair.strip())
                current_pair = ""
            else:
                current_pair += char

        # Convert each pair to HeaderRow
        for pair in pairs:
            if ':' in pair:
                key_part, value_part = pair.split(':', 1)
                key = key_part.strip().strip('"').strip("'")
                value = value_part.strip().strip('"').strip("'")
                rows.append(f'HeaderRow(key="{key}", value="{value}", values=[])')

        if rows:
            rows_str = ', '.join(rows)
            return f'HeaderSection(rows=[{rows_str}])'
        else:
            return 'HeaderSection(rows=[])'

    return re.sub(pattern, replace_func, content, flags=re.DOTALL)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python fix_header_sections.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    with open(file_path, 'r') as f:
        content = f.read()

    new_content = convert_key_values_to_rows(content)

    with open(file_path, 'w') as f:
        f.write(new_content)

    print(f"Fixed {file_path}")
