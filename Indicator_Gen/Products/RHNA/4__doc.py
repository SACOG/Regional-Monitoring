

'''
This script converts the RHNA housing cycle excel data product from a Microsoft Excel '.xlsx' file to a Microsoft Word '.docx' file


Good news - very organized and streamlined way of finding/replacing text in tempalte word document
Bad news - cannot insert tables into template word doc, would need to have tables pre-made then use find/replace for text in tables
'''



# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

from pathlib import Path
from tqdm import tqdm
import time
import traceback
import win32com.client
import warnings

import sys
sys.path.append(str(Path(__file__).parent/'config'))
import word
import rhna
warnings.filterwarnings("ignore")


PATH_PROD = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
FILE_WORD_TEMP = PATH_PROD.parent / 'TEMPLATE_RHNA_Jurisdiction.docx'

FILE_YAML = rhna.load_yaml()





# Main ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



indicators = [
    'POPEMP_1'
    , 'POPEMP_2'
    , 'POPEMP_4'
    , 'POPEMP_5'
    , 'POPEMP_6'
    , 'POPEMP_11'
    , 'POPEMP_12'
    , 'POPEMP_13'
    , 'POPEMP_14'
    , 'POPEMP_15'
    , 'POPEMP_16'
    , 'POPEMP_18'
    , 'POPEMP_20'
    , 'POPEMP_21'
    , 'POPEMP_22'
    , 'POPEMP_23'
    , 'POPEMP_25'
    , 'POPEMP_27'
    , 'HSG_1'
    , 'HSG_2'
    , 'HSG_3'
    , 'HSG_4'
    , 'HSG_5'
    , 'HSG_6'
    , 'HSG_7'
    , 'HSG_8'
    , 'HSG_9'
    , 'HSG_10'
    , 'HSG_11'
    , 'RISK_1'
    , 'OVER_1'
    , 'OVER_3'
    , 'OVER_4'
    , 'OVER_5'
    , 'OVER_6'
    , 'OVER_8'
    , 'OVER_9'
    , 'FARM_1'
    , 'FARM_2'
    , 'LGFEM_1'
    , 'LGFEM_2'
    , 'LGFEM_3'
    , 'LGFEM_4'
    , 'LGFEM_5'
    , 'SEN_1'
    , 'SEN_2'
    , 'SEN_3'
    , 'DISAB_2'
    , 'DISAB_4'
    , 'DISAB_5'
    , 'HOMELS_1'
    , 'HOMELS_2'
    , 'HOMELS_3'
    , 'HOMELS_4'
    , 'ELI_1'
    , 'ELI_3'
    , 'ELI_4'
    , 'AFFH_2'
    , 'AFFH_3'
    ]


TEST_RUN=False
# indicators = ['POPEMP_14']


if __name__ == '__main__':

    word_app = win32com.client.DispatchEx('Word.Application')
    word_app.Visible = False
    word_app.DisplayAlerts = False

    dt_errors = {}

    for folder in PATH_PROD.iterdir():
        # if folder.stem != 'Sacramento':
        #     continue
        print('\n'*2)
        county = folder.stem
        print(county)
        dt_errors[county] = {}

        path_county = PATH_PROD / county
        for folder in path_county.iterdir():
            if folder.stem not in ['Yuba City']:
                continue
            jurisdiction = folder.stem
            print('\n'*2)
            print(jurisdiction)
            print()
            dt_errors[county][jurisdiction] = {}

            path_juris = path_county / jurisdiction

            file_doc    = path_juris / f'RHNA_{jurisdiction}.docx'
            path_tables = path_juris / 'tables'

            try:

                if not TEST_RUN:
                    word_app.Documents.Open(str(FILE_WORD_TEMP))
                    dt_find_replace = word.set_main_find_replace(county, jurisdiction)
                    word.find_replace_all(word_app, dt_find_replace)

                for indicator in tqdm(indicators):

                    try:

                        dt_errors[county][jurisdiction][indicator] = {}
                        dt_find_replace = word.set_indicator_find_replace(indicator, county, jurisdiction, path_tables)
                        word.find_replace_all(word_app, dt_find_replace)

                    except Exception as e:
                        print(e)
                        traceback.print_exc()
                        print()
                        dt_errors[county][jurisdiction][indicator]['error'] = e

                word_app.ActiveDocument.SaveAs(str(file_doc))
                word_app.ActiveDocument.Close(SaveChanges=False)

            except Exception as e:
                print(e)
                traceback.print_exc()
                print()
                word_app.ActiveDocument.Close(SaveChanges=False)


# https://stackoverflow.com/questions/31553179/writing-a-pandas-dataframe-to-a-word-document-table-via-pywin32
# https://baysconsulting.co.uk/generating-word-documents-using-a-template-in-python/

    print('\n'*3)
    print('Switching over to replacing all images in document...')
    print()
    time.sleep(10)

    from docx import Document
    from docx.shared import Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    def replace_image_placeholder(doc, placeholder, path_png, width=Inches(6)):
        for para in doc.paragraphs:
            if placeholder in para.text:
                para.clear()
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
                run = para.add_run()
                run.add_picture(path_png, width=width)
                break

    indicators = ['POPEMP_1'
                    , 'POPEMP_4'
                    , 'SEN_2'
                    , 'POPEMP_2'
                    , 'POPEMP_11'
                    , 'POPEMP_10'
                    , 'POPEMP_14'
                    , 'POPEMP_13'
                    , 'POPEMP_6'
                    , 'POPEMP_15'
                    , 'ELI_1'
                    , 'POPEMP_21'
                    , 'ELI_3'
                    , 'ELI_4'
                    , 'POPEMP_16'
                    , 'POPEMP_20'
                    , 'POPEMP_18'
                    , 'POPEMP_22'
                    , 'POPEMP_25'
                    , 'HSG_1'
                    , 'HSG_4'
                    , 'HSG_3'
                    , 'HSG_11'
                    , 'HSG_7'
                    , 'HSG_8'
                    , 'HSG_9'
                    , 'HSG_10'
                    , 'OVER_6'
                    , 'OVER_5'
                    , 'OVER_8'
                    , 'OVER_9'
                    , 'SEN_3'
                    , 'OVER_1'
                    , 'OVER_4'
                    , 'OVER_3'
                    , 'LGFEM_1'
                    , 'HSG_5'
                    , 'POPEMP_23'
                    , 'LGFEM_5'
                    , 'SEN_1'
                    , 'DISAB_1'
                    , 'HOMELS_1'
                    , 'HOMELS_2'
                    , 'HOMELS_3'
                    , 'FARM_2'
                    , 'AFFH_3'
                    ]

    for folder in PATH_PROD.iterdir():
        # if folder.stem != 'Sacramento':
        #     continue
        print('\n'*2)
        county = folder.stem
        print(county)
        print('\n'*2)
        dt_errors[county] = {}

        path_county = PATH_PROD / county
        for folder in path_county.iterdir():
            if folder.stem not in ['Yuba City']:
                continue
            jurisdiction = folder.stem
            print('\n'*3)
            print(jurisdiction)
            print()
            dt_errors[county][jurisdiction] = {}

            path_juris = path_county / jurisdiction

            file_doc   = path_juris / f'RHNA_{jurisdiction}.docx'
            path_plots = path_juris / 'plots'

            doc = Document(file_doc)

            for indicator in tqdm(indicators):
                file_png = path_plots/f'{indicator}.png'
                try:
                    replace_image_placeholder(
                        doc,
                        f"[[FIG_{indicator}]]",
                        str(file_png),
                        width=Inches(6)
                    )
                except Exception as e:
                    print(e)
                    traceback.print_exc()
                    print()
                    dt_errors[county][jurisdiction][indicator] = e
            doc.save(file_doc)

