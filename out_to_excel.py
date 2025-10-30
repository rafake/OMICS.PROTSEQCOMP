import os
import re
import pandas as pd
from glob import glob
import argparse

parser = argparse.ArgumentParser(description='Extract Top 10 tables from .out files and save to Excel.')
parser.add_argument('-i', '--input', type=str, default='.', help='Input directory containing .out files (default: current directory)')
parser.add_argument('-o', '--output', type=str, default=None, help='Output directory for Excel file (default: current directory)')
args = parser.parse_args()

out_dir = args.input
input_dir_name = os.path.basename(os.path.normpath(out_dir)) or 'results'
output_file_name = f'jaccard_minhash_{input_dir_name}.xlsx'
if args.output:
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
else:
    output_dir = '.'
output_excel = os.path.join(output_dir, output_file_name)

# Pattern to match .out files (e.g., jaccard_benchmark_2cores.out)
out_files = glob(os.path.join(out_dir, '*.out'))

# Regex to extract the Top 10 table
TABLE_REGEX = re.compile(r'Top 10 most similar protein pairs:\n([+\-\w\s\.|:]+)\n\[Stage', re.MULTILINE)
# Fallback regex if [Stage is not present after table
TABLE_REGEX_FALLBACK = re.compile(r'Top 10 most similar protein pairs:\n([+\-\w\s\.|:]+)', re.MULTILINE)

tables_by_file = {}
file_names = []

for file in out_files:
    with open(file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        match = TABLE_REGEX.search(content)
        if not match:
            match = TABLE_REGEX_FALLBACK.search(content)
        if match:
            table_text = match.group(1)
            # Extract rows between the +---+ lines
            lines = [line for line in table_text.splitlines() if not line.startswith('+')]
            # Remove header if present
            if lines and 'mouse_id' in lines[0]:
                header = lines[0].split('|')[1:-1]
                lines = lines[1:]
            else:
                header = ['mouse_id', 'fish_id', 'jaccard']
            # Parse data rows
            data = [line.split('|')[1:-1] for line in lines if line.strip()]
            df = pd.DataFrame(data, columns=[h.strip() for h in header])
            # Save DataFrame by file name (sheet name)
            sheet_name = os.path.splitext(os.path.basename(file))[0][:31]  # Excel sheet name max 31 chars
            tables_by_file[sheet_name] = df
            file_names.append(os.path.basename(file))

if tables_by_file:
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        for sheet, df in tables_by_file.items():
            df.to_excel(writer, sheet_name=sheet, index=False)
    print(f"Saved summary to {output_excel} with {len(tables_by_file)} sheets from files: {file_names}")
else:
    print("No Top 10 tables found in .out files.")
