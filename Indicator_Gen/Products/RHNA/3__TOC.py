

'''
Python file to include "Table of Contents" tab at the start of every jurisdiction's RHNA data product (excel workbook)
'''


import openpyxl
from openpyxl.styles import Font, Border, PatternFill, Alignment, Protection
from pathlib import Path

PATH_OUT = Path(r'C:\Users\jfontes\Documents\Projects\Local\RHNA\Final Products')

COUNTIES = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']
# COUNTIES = ['Sacramento']

CW_COUNTY_TO_JURISDICTIONS = {
    # 'Sacramento': ['Folsom'],
    'El Dorado': ['Placerville', 'South Lake Tahoe', 'Unincorporated'],
    'Placer': ['Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville', 'Unincorporated'],
    'Sacramento': ['Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento', 'Unincorporated'],
    'Sutter': ['Live Oak', 'Yuba City', 'Unincorporated'],
    'Yolo': ['Davis', 'West Sacramento', 'Winters', 'Woodland', 'Unincorporated'],
    'Yuba': ['Marysville', 'Wheatland', 'Unincorporated']
}



if __name__ == '__main__':

    print('\n'*2)

    for county in COUNTIES:
    
        print(county)
        for jurisdiction in CW_COUNTY_TO_JURISDICTIONS[county]:

            # Define the file paths
            source_workbook_path = Path(__file__).parent/'config'/'TOC.xlsx'
            destination_workbook_path = PATH_OUT / county.replace(' County', '') / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

            # Load the source workbook and get the sheet to copy
            source_wb = openpyxl.load_workbook(source_workbook_path)
            source_sheet = source_wb.active  # or source_wb['YourSheetName'] if you know the sheet name

            # Load the destination workbook
            destination_wb = openpyxl.load_workbook(destination_workbook_path)

            # Get the 'Sheet' from the destination workbook
            if 'Sheet' in destination_wb.sheetnames: # Sheet
                destination_sheet = destination_wb['Sheet']
            else:
                destination_sheet = destination_wb.active

            # Clear the destination sheet
            for row in destination_sheet.iter_rows():
                for cell in row:
                    cell.value = None

            # Copy values and styles
            for row in source_sheet.iter_rows():
                for cell in row:
                    new_cell = destination_sheet.cell(row=cell.row, column=cell.column, value=cell.value)

                    # Copy font
                    new_cell.font = Font(
                        name=cell.font.name,
                        size=cell.font.size,
                        bold=cell.font.bold,
                        italic=cell.font.italic,
                        vertAlign=cell.font.vertAlign,
                        underline=cell.font.underline,
                        strike=cell.font.strike,
                        color=cell.font.color
                    )

                    # Copy border
                    new_cell.border = Border(
                        left=cell.border.left,
                        right=cell.border.right,
                        top=cell.border.top,
                        bottom=cell.border.bottom,
                        diagonal=cell.border.diagonal,
                        diagonal_direction=cell.border.diagonal_direction,
                        outline=cell.border.outline,
                        vertical=cell.border.vertical,
                        horizontal=cell.border.horizontal
                    )

                    # Copy fill
                    new_cell.fill = PatternFill(
                        fill_type=cell.fill.fill_type,
                        start_color=cell.fill.start_color,
                        end_color=cell.fill.end_color
                    )

                    # Copy alignment
                    new_cell.alignment = Alignment(
                        horizontal=cell.alignment.horizontal,
                        vertical=cell.alignment.vertical,
                        text_rotation=cell.alignment.text_rotation,
                        wrap_text=cell.alignment.wrap_text,
                        shrink_to_fit=cell.alignment.shrink_to_fit,
                        indent=cell.alignment.indent
                    )

                    # Copy protection
                    new_cell.protection = Protection(
                        locked=cell.protection.locked,
                        hidden=cell.protection.hidden
                    )

            # Copy merged cells
            for merged_range in source_sheet.merged_cells.ranges:
                destination_sheet.merge_cells(str(merged_range))

            destination_sheet.column_dimensions['A'].width = 12
            destination_sheet.column_dimensions['B'].width = 75
            destination_sheet.column_dimensions['C'].width = 52
            destination_sheet.column_dimensions['D'].width = 25
            destination_sheet.column_dimensions['E'].width = 65
            destination_sheet.column_dimensions['F'].width = 25
            destination_sheet.column_dimensions['G'].width = 150

            for row in range(1, destination_sheet.max_row + 1):
                destination_sheet.row_dimensions[row].height = 16

            # Rename the sheet
            destination_sheet.title = 'Indicators List'
            
            # Add hyperlinks from TOC to indicator sheets
            for row in range(1, destination_sheet.max_row + 1):

                cell = destination_sheet.cell(row=row, column=1)  # Column A

                if not cell.value:
                    continue

                sheet_name = str(cell.value).strip()
                sheet_name = sheet_name.replace('-0', '_')
                sheet_name = sheet_name.replace('-', '_')

                # Only create a link if the sheet exists
                if sheet_name in destination_wb.sheetnames:
                    cell.hyperlink = f"#'{sheet_name}'!A1"
                    cell.style = "Hyperlink"

            # Save the destination workbook
            destination_wb.save(destination_workbook_path)

