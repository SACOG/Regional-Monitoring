

'''
This script converts the RHNA housing cycle excel data product from a Microsoft Excel '.xlsx' file to a Microsoft word '.docx' file
The resulting word document only includes the tables and plots from each excel workbook
The tables and plots are to be copied over to the final word document produced from running the '.py' file '4__doc.py'
'''




# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
import time
from pathlib import Path
from tqdm import tqdm
import traceback
from docx import Document
import win32com.client

import sys
sys.path.append(str(Path(__file__).parent/'config'))
import word
import rhna


FILE_YAML = rhna.load_yaml()
PATH_PROD = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
# PATH_PROD = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA' / 'Cycle7' / 'Final Products'




# Main ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

print('\n'*2)

if __name__ == '__main__':

    dt_errors = {}
    
    for folder in PATH_PROD.iterdir():
        print('\n'*2)
        county = folder.stem
        print(county)
        print('\n'*2)
        path_county = PATH_PROD / county
        for folder in path_county.iterdir():

            jurisdiction = folder.stem
            print('\n'*2)
            print(jurisdiction)
            path_juris = path_county / jurisdiction

            if jurisdiction != 'Yuba City':
                continue

            file_doc    = path_juris / f'RHNA_{jurisdiction}_tables_and_plots.docx'
            file_wkbk   = path_juris / f'RHNA_{jurisdiction}.xlsx'
            path_plots  = path_juris / 'plots'
            path_tables = path_juris / 'tables'

            doc = Document()
            doc.add_heading(f'{jurisdiction}, {county} County', level=0)

            for indicator, yaml_ind in tqdm(FILE_YAML.items()):

                try:
    
                    theme  = yaml_ind['Theme']
                    title  = yaml_ind['Title']
                    file_png = path_plots / f'{indicator}.png'

                    if '1' in indicator:
                        doc.add_heading(f'{theme}', level=1)
                        doc.add_paragraph('')

                    p = doc.add_paragraph()
                    p.add_run(f'{indicator}: {title}').bold = True

                    df_table = pd.read_excel(file_wkbk, sheet_name=indicator, skiprows=2)
                    df_table = df_table.dropna()

                    file_tables_prod = [file for file in path_tables.glob('*.csv') if f'{indicator}_prod' in str(file)]
                    file_tables_pct  = [file for file in path_tables.glob('*.csv') if f'{indicator}_pct' in str(file)]
                    if len(file_tables_prod)>0:
                        df_prod = pd.read_csv(path_tables/f'{indicator}_prod.csv')
                        if len(file_tables_pct)>0:
                            df_pct  = pd.read_csv(path_tables/f'{indicator}_pct.csv' )
                            df_prod = word.combine_total_pct_tables(indicator, df_prod, df_pct)
                        else:
                            df_prod = word.combine_total_pct_tables(indicator, df_prod)

                    word.doc_add_table(doc, indicator, df_prod)
                    doc.add_paragraph('')
                    word.doc_add_plot(doc, file_png)
                    doc.add_page_break()

                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    print()
                    dt_errors[indicator] = e
                    doc.add_page_break()
                    # time.sleep(2)
            
            doc.save(file_doc)




# Part 2 ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


'''
Code to replace nan and nan% values in the tables/plots doc
'''


PATH_PROD = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
print()


if __name__ == '__main__':
        
    print('\n'*3)
    print('Cleaning word doc file...')
    print('\n'*3)
    time.sleep(5)

    word_app = win32com.client.DispatchEx('Word.Application')
    word_app.Visible = False
    word_app.DisplayAlerts = False
    wd_replace=2
    wd_find_wrap=1

    for folder in PATH_PROD.iterdir():
        # if folder.stem != 'Sacramento':
        #     continue
        print()
        county = folder.stem
        print(county)
        print()
        path_county = PATH_PROD / county
        for folder in path_county.iterdir():
            # if folder.stem not in ['Folsom']:
            #     continue
            jurisdiction = folder.stem
            print(jurisdiction)

            path_juris = path_county / jurisdiction
            file_doc = path_juris / f'RHNA_{jurisdiction}_tables_and_plots.docx'

            try:
                    
                word_app.Documents.Open(str(file_doc))

                word_app.Selection.Find.Execute(
                    FindText='nan%',
                    ReplaceWith='{0% or no data available}',
                    Replace=wd_replace,
                    Forward=True,
                    MatchCase=True,
                    MatchWholeWord=True,
                    MatchWildcards=False,
                    MatchSoundsLike=False,
                    MatchAllWordForms=False,
                    Wrap=wd_find_wrap,
                    Format=True
                )

                word_app.Selection.Find.Execute(
                    FindText='nan',
                    ReplaceWith='{0 or no data available}',
                    Replace=wd_replace,
                    Forward=True,
                    MatchCase=True,
                    MatchWholeWord=True,
                    MatchWildcards=False,
                    MatchSoundsLike=False,
                    MatchAllWordForms=False,
                    Wrap=wd_find_wrap,
                    Format=True
                )

            except Exception as e:
                print(e); traceback.print_exc(); print()
                word_app.ActiveDocument.Close(SaveChanges=False)

            word_app.ActiveDocument.SaveAs(str(file_doc))
            word_app.ActiveDocument.Close(SaveChanges=False)

breakpoint()

# https://stackoverflow.com/questions/31553179/writing-a-pandas-dataframe-to-a-word-document-table-via-pywin32
# https://baysconsulting.co.uk/generating-word-documents-using-a-template-in-python/