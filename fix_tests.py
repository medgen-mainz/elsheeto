import re

def fix_header_section_calls(content):
    # Pattern to match HeaderSection calls without name parameter
    pattern = r'HeaderSection\(\s*rows='
    
    # Replace with HeaderSection with name parameter
    def replace_func(match):
        return 'HeaderSection(name="header", rows='
    
    return re.sub(pattern, replace_func, content)

def fix_header_row_calls(content):
    # Pattern to match HeaderRow calls with values parameter
    pattern = r'HeaderRow\(([^)]*), values=\[\][^)]*\)'
    
    # Replace removing values parameter
    def replace_func(match):
        args = match.group(1)
        return f'HeaderRow({args})'
    
    return re.sub(pattern, replace_func, content)

# Read the file
with open('tests/unit/test_parser_illumina_v1.py', 'r') as f:
    content = f.read()

# Apply fixes
content = fix_header_section_calls(content)
content = fix_header_row_calls(content)

# Write back
with open('tests/unit/test_parser_illumina_v1.py', 'w') as f:
    f.write(content)

print("Fixed HeaderSection calls")
