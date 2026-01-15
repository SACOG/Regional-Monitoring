



'''
This script converts the RHNA housing cycle excel data product from a Microsoft Excel '.xlsx' file to a Microsoft Word '.docx' file
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


PATH_PROD = Path.home() / 'Documents' / 'Projects' / 'General' / 'RHNA' / 'Final Products'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()
rhna.print2()





def doc_add_summary(indicator, jurisdiction, df_prod, df_pct=None):

    '''
    Function to include a summary/interpretation of data, specific to each indicator
    Each indicator needs its own conditional statement to match with the "Word" parameter in the 'rhna.yaml' file
    '''

    if indicator == 'POPEMP_1':
        max_year = df_prod['Year'].max()
        value1 = df_prod[df_prod['Year']==max_year][jurisdiction].values[0]
        value2 = df_prod[df_prod['Year']==max_year][f'Percent Difference from 2000: {jurisdiction}'].values[0]
        doc.add_paragraph(word.format(max_year=max_year, jurisdiction=jurisdiction, value1=value1, value2=value2))
    if indicator == 'HSG_1':
        value1 = df_prod[df_prod['Housing Type']=='Single Family Detached']['Year 2024'].values[0]
        value2 = df_prod[df_prod['Housing Type']=='Single Family Attached']['Year 2024'].values[0]
        doc.add_paragraph(word.format(jurisdiction=jurisdiction, value1=value1, value2=value2))
    if indicator == 'HSG_2':
        value1 = round(df_pct[df_pct['Geography']==      jurisdiction]['Occupied housing units'].values[0]*100, 1)
        value2 = round(df_pct[df_pct['Geography']==f'{county} County']['Occupied housing units'].values[0]*100, 1)
        value3 = round(df_pct[df_pct['Geography']==    'SACOG Region']['Occupied housing units'].values[0]*100, 1)
        doc.add_paragraph(word.format(jurisdiction=jurisdiction, value1=value1, value2=value2, value3=value3))
    if indicator == 'SEN_1':
        value1 = round(df_pct[df_pct['Income Level']==            '0%-30% of AMI']['Owner occupied'].values[0]*100, 1)
        value2 = round(df_pct[df_pct['Income Level']== 'Greater than 100% of AMI']['Owner occupied'].values[0]*100, 1)
        doc.add_paragraph(word.format(jurisdiction=jurisdiction, value1=value1, value2=value2))


def doc_add_table(df_prod):

    '''
    Function to add a table to the word document
    Conditional statements regarding 'column_name' may need updates as more indicators are added to the for loop
    '''

    table = doc.add_table(rows=1 + len(df_prod), cols=len(df_prod.columns))
    table.style = 'Table Grid'

    hdr_cells = table.rows[0].cells
    for i, column_name in enumerate(df_prod.columns):
        run = hdr_cells[i].paragraphs[0].add_run(column_name)
        run.bold = True
        run.font.size = Pt(11)

    for i, row in df_prod.iterrows():
        row_cells = table.rows[i+1].cells
        for j, column_name in enumerate(df_prod.columns):
            value = row[column_name]
            paragraph = row_cells[j].paragraphs[0]
            if column_name == 'Year':
                formatted_value = f"{value:.0f}"
            elif column_name not in ['Geography', 'Housing Type', 'Income Level'] and 'Percentage' not in column_name:
                formatted_value = f"{value:,.0f}"  # Format as #,### (e.g., 1,234)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            elif 'Percentage' in column_name or 'Percent' in column_name:
                formatted_value = f"{value:.1%}%"  # Format as #.#% (e.g., 12.3%)
                paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            else:
                formatted_value = str(value)
            run = row_cells[j].paragraphs[0].add_run(formatted_value)
            run.font.size = Pt(10)



def doc_add_plot(file_png):
    '''
    Function to add an image file to the Word document
    Each image is a plot of the data stored as an '.png' file
    '''
    doc.add_picture(str(file_png), width=Inches(6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER







# Main ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    indicators = ['POPEMP_1', 'POPEMP_2', 'HSG_1', 'HSG_2', 'SEN_1']
    
    for folder in PATH_PROD.iterdir():
        rhna.print2()
        county = folder.stem; print(county); print()
        path_county = PATH_PROD / county
        for folder in path_county.iterdir():
            jurisdiction = folder.stem; print(jurisdiction)
            path_juris = path_county / jurisdiction

            file_doc    = path_juris / f'RHNA_{jurisdiction}.docx'
            file_wkbk   = path_juris / f'RHNA_{jurisdiction}.xlsx'
            path_plots  = path_juris / 'plots'
            path_tables = path_juris / 'tables'


            doc = Document()
            doc.add_heading(f'{jurisdiction}, {county} County', level=0)


            for indicator in tqdm(indicators):

                try:
    
                    theme  = FILE_YAML[indicator]['Theme' ][0]
                    title  = FILE_YAML[indicator]['Title' ][0]
                    source = FILE_YAML[indicator]['Source'][0]
                    word   = FILE_YAML[indicator][  'Word']
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
                    else:
                        df_pct  = pd.read_csv(file_tables[0])
                        df_prod = pd.read_csv(file_tables[1])

                    try: doc_add_summary(indicator, jurisdiction, df_prod, df_pct)
                    except: doc_add_summary(indicator, jurisdiction, df_prod)
                    doc_add_table(df_prod)

                    p = doc.add_paragraph(f'Source: {source}')
                    # doc.add_paragraph('')

                    doc_add_plot(file_png)

                    doc.add_page_break()


                except Exception as e: print(e); traceback.print_exc(); print(); doc.add_page_break()

            doc.save(file_doc)
