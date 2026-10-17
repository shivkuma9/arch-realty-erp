import openpyxl
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

file_path = r"c:\Users\sakth\OneDrive\Documents\Arch realty\IT\company project\Excel data for software\Real_Estate_Consultancy_ERP_Operations_Structure.xlsx"

wb = openpyxl.load_workbook(file_path, data_only=True)
for sname in wb.sheetnames:
    sheet = wb[sname]
    print(f"\n=================== SHEET: {sname} ===================")
    for i, row in enumerate(sheet.iter_rows(values_only=True)):
        if i > 40:  # print first 40 rows
            print(f"... and {sheet.max_row - 40} more rows")
            break
        cleaned_row = [str(c).strip() if c is not None else '' for c in row if c is not None and str(c).strip() != '']
        if cleaned_row:
            print(f"Row {i+1}: {cleaned_row}")

wb.close()
