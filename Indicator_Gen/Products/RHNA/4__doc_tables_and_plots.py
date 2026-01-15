



'''
This script converts the RHNA housing cycle excel data product from a Microsoft Excel '.xlsx' file to a Microsoft Word '.docx' file
The resulting word document only includes the tables and plots from each excel workbook
The tables and plots are to be copied over to the final word document produced from running the '.py' file '4__doc.py'
'''




# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
from pathlib import Path
from tqdm import tqdm
import traceback
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches


PATH_PROD = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()
rhna.print2()



def doc_add_table(df_prod):

    '''
    Function to add a table to the word document
    Conditional statements regarding 'column_name' may need updates as more indicators are added to the for loop
    '''

    ## TODO:
    # POPEMP_1 - "Percent" column needs to be cleaned
    # Need to figure out how to properly format POPEMP_13, POPEMP_14, POPEMP_15
    # HSG_4? why
    # Need to replace "nan" with "N/A"?
    # HSG_11? why
    # RISK_1? why
    # OVER_1, OVER_2? OVER_6? OVER_7? why
    # Need to think about how to fit tables with many columns or long text columns... smaller font? short hand col names?

    cols_str = ['Geography', 'Housing Type', 'Income Level', 'Race/Ethnicity', 'Variable', 'Age Group', 'Location'
                , 'Household Type', 'Family Status', 'Household Status', 'Industry', 'Occupation', 'Class of Worker'
                , 'Earnings', 'Wage Group', 'Housing Tenure', 'Year Moved to Current Residence', 'Vacancy Type'
                , 'Year Built', 'Number of Bedrooms', 'Housing Issue', 'Home Value', 'Contract Rent', 'Income Group'
                , 'Risk Level', 'Tenure', 'Overcrowding Severity', 'Cost Burden', 'Year', 'Household Size'
                , 'Family Status', 'Disability Type', 'Disability Status', 'Residence Type', 'Characteristic'
                , 'School Year', 'Income Bracket', 'English Proficiency', 'Farm Worker', 'Shelter Status']

    table = doc.add_table(rows=1 + len(df_prod), cols=len(df_prod.columns))
    table.style = 'Table Grid'

    hdr_cells = table.rows[0].cells
    for i, column_name in enumerate(df_prod.columns):
        run = hdr_cells[i].paragraphs[0].add_run(column_name)
        run.bold = True
        run.font.size = Pt(8)

    for i, row in df_prod.iterrows():
        row_cells = table.rows[i+1].cells
        for j, column_name in enumerate(df_prod.columns):
            value = row[column_name]
            paragraph = row_cells[j].paragraphs[0]
            if column_name == 'Year':
                formatted_value = f"{value:.0f}"
            elif column_name not in cols_str and 'Percentage' not in column_name and 'Percent' not in column_name and '(%)' not in column_name:
                formatted_value = f"{value:,.0f}"  # Format as #,### (e.g., 1,234)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            # elif 'Percentage' in column_name or 'Percent' in column_name or '(%)' in column_name:
            elif 'Percentage' in column_name or '(%)' in column_name:
                formatted_value = f"{value:.1%}"  # Format as #.#% (e.g., 12.3%)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                formatted_value = str(value)
            run = row_cells[j].paragraphs[0].add_run(formatted_value)
            run.font.size = Pt(8)




def doc_add_plot(file_png):
    '''
    Function to add an image file to the Word document
    Each image is a plot of the data stored as an '.png' file
    '''
    doc.add_picture(str(file_png), width=Inches(6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER




## TODO: Something wrong here
def combine_total_pct_tables(indicator, df_prod, df_pct=None):

    col = FILE_YAML[indicator]['Word']['Subgroup']

    df_prod_ = df_prod.copy()

    if FILE_YAML[indicator]['Word']['Table Transpose']:
        df_prod_ = df_prod_.set_index(df_prod_.columns[0]).T.reset_index(names=col)
        # df_prod_.columns = [str(col) for col in df_prod_.columns]
    if FILE_YAML[indicator]['Word']['Percent Column']:
        df_pct_ = df_pct.copy()
        if FILE_YAML[indicator]['Word']['Table Transpose']:
            df_pct_ = df_pct_.set_index(df_pct_.columns[0]).T.reset_index(names=col)
        df_prod_pct = df_prod_.merge(df_pct_, on=col)

        list_new_col_names=[]
        for col_prod_pct in df_prod_pct.columns:
            if '_y' in col_prod_pct:
                col_prod_pct = col_prod_pct.replace('_y', ' (%)') # (%)
            col_prod_pct = col_prod_pct.replace('_x', '')
            list_new_col_names.append(col_prod_pct)
        df_prod_pct.columns = list_new_col_names
        if 'Percentage' not in df_prod_pct.columns:
            cols_wout_pct = [col_ for col_ in list_new_col_names if '(%)' not in col_][1:]
            for col_wout_pct in cols_wout_pct:
                col_data = df_prod_pct.pop(f'{col_wout_pct} (%)')
                df_prod_pct.insert(loc=df_prod_pct.columns.get_loc(col_wout_pct)+1, column=f'{col_wout_pct} (%)', value=col_data)

        return df_prod_pct
    else:
        return df_prod_



# Main ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    dt_errors = {}
    
    for folder in PATH_PROD.iterdir():
        rhna.print2()
        county = folder.stem; print(county); print()
        path_county = PATH_PROD / county
        for folder in path_county.iterdir():
            jurisdiction = folder.stem; print(jurisdiction)
            path_juris = path_county / jurisdiction

            file_doc    = path_juris / f'RHNA_{jurisdiction}_tables_and_plots.docx'
            file_wkbk   = path_juris / f'RHNA_{jurisdiction}.xlsx'
            path_plots  = path_juris / 'plots'
            path_tables = path_juris / 'tables'


            doc = Document()
            doc.add_heading(f'{jurisdiction}, {county} County', level=0)


            for indicator, yaml_ind in tqdm(FILE_YAML.items()):

                # if indicator != 'HSG_4':
                #     continue

                try:
    
                    theme  = yaml_ind['Theme']
                    title  = yaml_ind['Title']
                    file_png = path_plots / f'RHNA_{indicator}_.png'

                    if '1' in indicator:
                        doc.add_heading(f'{theme}', level=1)
                        doc.add_paragraph('')

                    p = doc.add_paragraph(); p.add_run(f'{indicator}: {title}').bold = True

                    df_table = pd.read_excel(file_wkbk, sheet_name=indicator, skiprows=2)
                    df_table = df_table.dropna()

                    file_tables = [file for file in path_tables.glob('*.csv') if f'{indicator}_' in str(file)]
                    if len(file_tables) == 1:
                        df_prod = pd.read_csv(file_tables[0])
                        df_prod = combine_total_pct_tables(indicator, df_prod)
                    else:
                        df_pct  = pd.read_csv(file_tables[0])
                        df_prod = pd.read_csv(file_tables[1])
                        df_prod = combine_total_pct_tables(indicator, df_prod, df_pct)

                    doc_add_table(df_prod)
                    doc.add_paragraph('')
                    doc_add_plot(file_png)
                    doc.add_page_break()

                except Exception as e:
                    print(e); traceback.print_exc(); print()
                    dt_errors[indicator] = e
                    doc.add_page_break()
                    # time.sleep(2)
            
            doc.save(file_doc)

breakpoint()
