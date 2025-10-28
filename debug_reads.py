from elsheeto.parser import stage1, stage2
from elsheeto.parser.common import ParserConfiguration

csv_content = """[Header],,
IEMFileVersion,4,,
Experiment Name,Mixed Read Test,,
Date,2025-10-28,,
Workflow,GenerateFASTQ,,
[Reads],,
150,,
8,,
130,,
[Data],,
Sample_ID,Sample_Name,Sample_Project
Sample1,Test Sample 1,Project1"""

config = ParserConfiguration()

# Stage 1: Parse raw CSV
raw_sheet = stage1.from_csv(data=csv_content, config=config)
print("Raw sheet sections:")
for section in raw_sheet.sections:
    print(f"Section name: '{section.name}', data: {section.data}")

# Stage 2: Convert to structured format
structured_sheet = stage2.from_stage1(raw_sheet=raw_sheet, config=config)
print(f"\nStructured sheet has {len(structured_sheet.header_sections)} header sections")
print(f"Data section headers: {structured_sheet.data_section.headers if structured_sheet.data_section else 'None'}")
