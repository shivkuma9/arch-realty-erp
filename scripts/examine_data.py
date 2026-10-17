import openpyxl
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

def examine_file(path):
    print("="*70)
    print("ANALYZING:", os.path.basename(path))
    print("="*70)
    wb = openpyxl.load_workbook(path, data_only=True)
    for sname in wb.sheetnames:
        sheet = wb[sname]
        print(f"\n--- Sheet: {sname} (Rows: {sheet.max_row}, Cols: {sheet.max_column}) ---")
        headers = []
        # Find first non-empty row with >= 3 values
        for r_idx, row in enumerate(sheet.iter_rows(values_only=True)):
            vals = [str(c).strip() if c is not None else '' for c in row]
            non_empty = [v for v in vals if v]
            if len(non_empty) >= 3:
                print(f"Header Row {r_idx+1}: {non_empty[:12]}")
                # Print one sample data row
                for next_row in sheet.iter_rows(min_row=r_idx+2, max_row=r_idx+3, values_only=True):
                    sample_vals = [str(c).strip() if c is not None else '' for c in next_row]
                    print(f"Sample Data: {sample_vals[:12]}")
                break
    wb.close()

p1 = r"c:\Users\sakth\OneDrive\Documents\Arch realty\IT\company project\Excel data for software\commerical.xlsx"
p2 = r"c:\Users\sakth\OneDrive\Documents\Arch realty\IT\company project\Excel data for software\Land & Plot.xlsx"
p3 = r"c:\Users\sakth\OneDrive\Documents\Arch realty\IT\company project\Excel data for software\Warehouse data.xlsx"
p4 = r"c:\Users\sakth\OneDrive\Documents\Arch realty\IT\company project\Excel data for software\Pre Lease Property Data 2026.xlsx"
p5 = r"c:\Users\sakth\OneDrive\Documents\Arch realty\IT\company project\Excel data for software\Client Management.xlsx"

for p in [p1, p2, p3, p4, p5]:
    if os.path.exists(p):
        examine_file(p)
