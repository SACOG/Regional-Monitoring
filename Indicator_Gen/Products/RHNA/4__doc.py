





'''
This script converts the RHNA housing cycle excel data product from a Microsoft Excel '.xlsx' file to a Microsoft Word '.docx' file


Good news - very organized and streamlined way of finding/replacing text in tempalte word document
Bad news - cannot insert tables/plots into template word doc, would need to have tables pre-made then use find/replace for text in tables
would need to copy/paste plots :(
'''


## TODO:
# How do we want to report on the "year" for the ACS 5 year data?



# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import traceback
import win32com.client


PATH_PROD = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'
FILE_WORD_TEMP = PATH_PROD.parent / 'TEMPLATE_RHNA_Jurisdiction.docx'

import sys
sys.path.append(str(PATH_CONFIG))
import word
import rhna
FILE_YAML = rhna.load_yaml()
rhna.print2()



ACS_YEAR_MAX = 2023
CHAS_YEAR_MAX = 2021




def create_find_replace_dictionary(indicator, county, jurisdiction):

    '''
    Function to include a summary/interpretation of data, specific to each indicator
    Each indicator needs its own conditional statement to match with the "Word" parameter in the 'rhna.yaml' file
    '''

    file_tables = [file for file in path_tables.glob('*.csv') if f'{indicator}_' in str(file)]
    if len(file_tables) == 1:
        df_prod = pd.read_csv(file_tables[0])
    else:
        df_pct  = pd.read_csv(file_tables[0])
        df_prod = pd.read_csv(file_tables[1])


    if jurisdiction == 'Unincorporated':
        dt_find_replace = {
            '[jurisdiction]': f'{county} County unincorporated'
            , '[jurisdictions]': f"{county} County's unincorporated"
        }
    else:
        dt_find_replace = {
            '[jurisdiction]': jurisdiction
            , '[jurisdictions]': f"{jurisdiction}'s"
        }

    dt_find_replace['[county]'] = f'{county} County'

    if 'Year' in df_prod.columns:
        year_min = df_prod['Year'].min()
        year_max = df_prod['Year'].max()
        dt_find_replace[f'[{indicator}_year_max]'] = year_max
        dt_find_replace[f'[{indicator}_year_min]'] = year_min

    if indicator == 'POPEMP_1':  dt_find_replace = word.popemp_1(dt_find_replace, df_prod, jurisdiction, year_max, year_min)
    if indicator == 'POPEMP_2':  dt_find_replace = word.popemp_2(dt_find_replace, df_prod, df_pct, year_max, year_min)
    if indicator == 'POPEMP_4':  dt_find_replace = word.popemp_4(dt_find_replace, df_prod)
    if indicator == 'POPEMP_5':  dt_find_replace = word.popemp_5(dt_find_replace, df_prod, jurisdiction)
    if indicator == 'POPEMP_6':  dt_find_replace = word.popemp_6(dt_find_replace, df_pct, jurisdiction, county)
    if indicator == 'POPEMP_11': dt_find_replace = word.popemp_11(dt_find_replace, df_prod, year_max, year_min)
    if indicator == 'POPEMP_12': dt_find_replace = word.popemp_12(dt_find_replace, df_prod, year_max)
    if indicator == 'POPEMP_13': dt_find_replace = word.popemp_13(dt_find_replace, df_prod, jurisdiction, year_max, year_min)
    if indicator == 'POPEMP_15': dt_find_replace = word.popemp_15(dt_find_replace, df_prod, jurisdiction, year_max, year_min)
    if indicator == 'POPEMP_16': dt_find_replace = word.popemp_16(dt_find_replace, df_prod, df_pct, jurisdiction, county)
    if indicator == 'POPEMP_18': dt_find_replace = word.popemp_18(dt_find_replace, df_prod)
    if indicator == 'POPEMP_20': dt_find_replace = word.popemp_20(dt_find_replace, df_pct)
    if indicator == 'POPEMP_21': dt_find_replace = word.popemp_21(dt_find_replace, df_pct)
    if indicator == 'POPEMP_22': dt_find_replace = word.popemp_22(dt_find_replace, df_pct)
    if indicator == 'POPEMP_23': dt_find_replace = word.popemp_23(dt_find_replace, df_prod, df_pct, jurisdiction)
    if indicator == 'HSG_1':     dt_find_replace = word.hsg_1(dt_find_replace, df_prod, jurisdiction, county)
    if indicator == 'HSG_2':     dt_find_replace = word.hsg_2(dt_find_replace, df_pct, jurisdiction)
    if indicator == 'HSG_3':     dt_find_replace = word.hsg_3(dt_find_replace, df_pct, jurisdiction)
    if indicator == 'HSG_4':     dt_find_replace = word.hsg_4(dt_find_replace, df_prod, df_pct)
    if indicator == 'HSG_5':     dt_find_replace = word.hsg_5(dt_find_replace, df_prod)
    if indicator == 'HSG_6':     dt_find_replace = word.hsg_6(dt_find_replace, df_pct)
    if indicator == 'HSG_7':     dt_find_replace = word.hsg_7(dt_find_replace, df_pct, jurisdiction)
    if indicator == 'HSG_8':     dt_find_replace = word.hsg_8(dt_find_replace, df_prod, jurisdiction, county, year_max, year_min)
    if indicator == 'HSG_9':     dt_find_replace = word.hsg_9(dt_find_replace, df_pct, jurisdiction, county)
    if indicator == 'HSG_10':    dt_find_replace = word.hsg_10(dt_find_replace, df_prod, jurisdiction, county, year_max, year_min)
    if indicator == 'HSG_11':    dt_find_replace = word.hsg_11(dt_find_replace, df_prod)
    if indicator == 'OVER_1':    dt_find_replace = word.over_1(dt_find_replace, df_pct)
    if indicator == 'OVER_3':    dt_find_replace = word.over_3(dt_find_replace, df_pct, jurisdiction)
    if indicator == 'OVER_4':    dt_find_replace = word.over_4(dt_find_replace, df_pct)
    if indicator == 'OVER_5':    dt_find_replace = word.over_5(dt_find_replace, df_prod, df_pct)
    if indicator == 'OVER_6':    dt_find_replace = word.over_6(dt_find_replace, df_pct)
    if indicator == 'OVER_8':    dt_find_replace = word.over_8(dt_find_replace, df_pct)
    if indicator == 'OVER_9':    dt_find_replace = word.over_9(dt_find_replace, df_pct)
    if indicator == 'FARM_1':    dt_find_replace = word.farm_1(dt_find_replace, df_prod, jurisdiction)
    if indicator == 'FARM_2':    dt_find_replace = word.farm_2(dt_find_replace, df_prod)
    if indicator == 'LGFEM_1':   dt_find_replace = word.lgfem_1(dt_find_replace, df_pct)
    if indicator == 'LGFEM_2':   dt_find_replace = word.lgfem_2(dt_find_replace, df_pct, jurisdiction)
    if indicator == 'LGFEM_3':   dt_find_replace = word.lgfem_3(dt_find_replace, df_pct)
    if indicator == 'LGFEM_4':   dt_find_replace = word.lgfem_4(dt_find_replace, df_prod)
    if indicator == 'LGFEM_5':   dt_find_replace = word.lgfem_5(dt_find_replace, df_pct)
    if indicator == 'SEN_1':     dt_find_replace = word.sen_1(dt_find_replace, df_pct)
    if indicator == 'SEN_2':     dt_find_replace = word.sen_2(dt_find_replace, df_pct)
    if indicator == 'SEN_3':     dt_find_replace = word.sen_3(dt_find_replace, df_pct)
    if indicator == 'DISAB_2':   dt_find_replace = word.disab_2(dt_find_replace, df_pct, jurisdiction)
    if indicator == 'DISAB_4':   dt_find_replace = word.disab_4(dt_find_replace, df_prod)
    if indicator == 'DISAB_5':   dt_find_replace = word.disab_5(dt_find_replace, df_prod)
    if indicator == 'HOMELS_1':  dt_find_replace = word.homels_1(dt_find_replace, df_prod)
    if indicator == 'HOMELS_2':  dt_find_replace = word.homels_2(dt_find_replace, df_prod, df_pct)
    if indicator == 'HOMELS_3':  dt_find_replace = word.homels_3(dt_find_replace, df_prod)
    if indicator == 'HOMELS_4':  dt_find_replace = word.homels_4(dt_find_replace, df_prod, jurisdiction, county)
    if indicator == 'ELI_1':     dt_find_replace = word.eli_1(dt_find_replace, df_prod, jurisdiction)
    if indicator == 'ELI_3':     dt_find_replace = word.eli_3(dt_find_replace, df_pct)
    if indicator == 'AFFH_3':    dt_find_replace = word.affh_3(dt_find_replace, df_pct, jurisdiction)


    return dt_find_replace






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
    , 'POPEMP_15'
    , 'POPEMP_16'
    , 'POPEMP_18'
    , 'POPEMP_20'
    , 'POPEMP_21'
    , 'POPEMP_22'
    , 'POPEMP_23'
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
    , 'AFFH_3'
    ]




TEST_RUN=False
# indicators = ['HSG_1']




if __name__ == '__main__':


    word_app = win32com.client.DispatchEx('Word.Application')
    word_app.Visible = False
    word_app.DisplayAlerts = False
    wd_replace=2
    wd_find_wrap=1


    dt_errors = {}


    for folder in PATH_PROD.iterdir():
        # if folder.stem != 'Sacramento':
        #     continue
        rhna.print2()
        county = folder.stem; print(county); rhna.print2()
        dt_errors[county] = {}

        path_county = PATH_PROD / county
        for folder in path_county.iterdir():
            # if folder.stem not in ['Folsom']:
            #     continue
            jurisdiction = folder.stem; rhna.print3(); print(jurisdiction); print()
            dt_errors[county][jurisdiction] = {}

            path_juris = path_county / jurisdiction

            file_doc    = path_juris / f'RHNA_{jurisdiction}.docx'
            file_wkbk   = path_juris / f'RHNA_{jurisdiction}.xlsx'
            path_plots  = path_juris / 'plots'
            path_tables = path_juris / 'tables'


            try:

                if not TEST_RUN:
                    word_app.Documents.Open(str(FILE_WORD_TEMP))

                for indicator in tqdm(indicators):

                    try:

                        dt_errors[county][jurisdiction][indicator] = {}
                        dt_find_replace = create_find_replace_dictionary(indicator, county, jurisdiction)

                        for str_find, str_replace in dt_find_replace.items():

                            try:
                                word_app.Selection.Find.Execute(
                                    FindText=str_find,
                                    ReplaceWith=str_replace,
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
                                dt_errors[county][jurisdiction][indicator][str_find] = str_replace
                    except Exception as e:
                        print(e); traceback.print_exc(); print()
                        dt_errors[county][jurisdiction][indicator]['error'] = e


                word_app.ActiveDocument.SaveAs(str(file_doc))
                word_app.ActiveDocument.Close(SaveChanges=False)

            except Exception as e:
                print(e); traceback.print_exc(); print()
                word_app.ActiveDocument.Close(SaveChanges=False)

breakpoint()

# https://stackoverflow.com/questions/31553179/writing-a-pandas-dataframe-to-a-word-document-table-via-pywin32
# https://baysconsulting.co.uk/generating-word-documents-using-a-template-in-python/