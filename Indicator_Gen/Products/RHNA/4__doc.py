



'''
This script converts the RHNA housing cycle excel data product from a Microsoft Excel '.xlsx' file to a Microsoft Word '.docx' file


Good news - very organized and streamlined way of finding/replacing text in tempalte word document
Bad news - cannot insert tables/plots into template word doc, would need to have tables pre-made then use find/replace for text in tables
would need to copy/paste plots :(
'''




# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

import numpy as np
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
import rhna
FILE_YAML = rhna.load_yaml()
rhna.print2()




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

    ACS_YEAR_MAX = 2023


    if indicator == 'POPEMP_1':
        value_year_min = df_prod[df_prod['Year']==year_min][jurisdiction].values[0]
        value_year_max = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]
        value_pct_diff = abs((value_year_max / value_year_min) - 1)
        if value_pct_diff > 0: increase_or_decrease_pop = 'increased'
        else: increase_or_decrease_pop = 'decreased'
        value_year_min_region = df_prod[df_prod['Year']==year_min]['SACOG'].values[0]
        value_year_max_region = df_prod[df_prod['Year']==year_max]['SACOG'].values[0]
        value_pct_diff_region = abs((value_year_max_region / value_year_min_region) - 1)
        if value_pct_diff > value_pct_diff_region: above_or_below_region = 'above'
        else: above_or_below_region = 'below'
        value_year_max_pct_region = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]/df_prod[df_prod['Year']==year_max]['SACOG'].values[0]
        value_pct_diff_2020 = abs((value_year_max / df_prod[df_prod['Year']==2020][jurisdiction].values[0]) - 1)
        if value_pct_diff_2020 > 0: increase_or_decrease_pop_2020 = 'increased'
        else: increase_or_decrease_pop_2020 = 'decreased'
        dt_find_replace['[POPEMP_1_value_year_min]'               ] = f'{value_year_min:,.0f}'
        dt_find_replace['[POPEMP_1_value_year_max]'               ] = f'{value_year_max:,.0f}'
        dt_find_replace['[POPEMP_1_value_pct_diff]'               ] = f'{value_pct_diff:.1%}'
        dt_find_replace['[POPEMP_1_value_pct_diff_region]'        ] = f'{value_pct_diff_region:.1%}'
        dt_find_replace['[POPEMP_1_increase_or_decrease_pop]'     ] = increase_or_decrease_pop
        dt_find_replace['[POPEMP_1_above_or_below_region]'        ] = above_or_below_region
        dt_find_replace['[POPEMP_1_value_pct_region]'             ] = f'{value_year_max_pct_region:.1%}'
        dt_find_replace['[POPEMP_1_value_pct_diff_2020]'          ] = f'{value_pct_diff_2020:.1%}'
        dt_find_replace['[POPEMP_1_increase_or_decrease_pop_2020]'] = increase_or_decrease_pop_2020

    if indicator == 'POPEMP_2':
        # value_other_pct_diff = round(abs((df_prod[df_prod['Year']==year_max]['Other race or multiple races (NH)'].values[0]/df_prod[df_prod['Year']==year_min]['Other race or multiple races (NH)'].values[0])-1), 3)
        # if value_other_pct_diff > 0: increase_or_decrease_other = 'increased'
        # else: increase_or_decrease_other = 'decreased'
        # value_white_pct_diff = round(abs((df_prod[df_prod['Year']==year_max]['White (NH)'].values[0]/df_prod[df_prod['Year']==year_min]['White (NH)'].values[0])-1), 3)
        # if value_white_pct_diff > 0: increase_or_decrease_white = 'increased'
        # else: increase_or_decrease_white = 'decreased'
        # dt_find_replace['[POPEMP_2_value_other_pct_diff]'      ] = f'{value_other_pct_diff:.1%}'
        # dt_find_replace['[POPEMP_2_value_white_pct_diff]'      ] = f'{value_white_pct_diff:.1%}'
        # dt_find_replace['[POPEMP_2_increase_or_decrease_other]'] = increase_or_decrease_other
        # dt_find_replace['[POPEMP_2_increase_or_decrease_white]'] = increase_or_decrease_white
        value_year_min_white_pct    = df_pct[df_pct['Year']==year_min]['White (NH)'                    ].values[0]
        value_year_min_black_pct    = df_pct[df_pct['Year']==year_min]['Black or African American (NH)'].values[0]
        value_year_min_asian_pct    = df_pct[df_pct['Year']==year_min]['Asian (NH)'                    ].values[0]
        value_year_min_hispanic_pct = df_pct[df_pct['Year']==year_min]['Hispanic or Latino'            ].values[0]
        value_year_min_non_white_pct = 1-value_year_min_white_pct
        value_year_max_white_pct    = df_pct[df_pct['Year']==year_max]['White (NH)'                    ].values[0]
        value_year_max_black_pct    = df_pct[df_pct['Year']==year_max]['Black or African American (NH)'].values[0]
        value_year_max_asian_pct    = df_pct[df_pct['Year']==year_max]['Asian (NH)'                    ].values[0]
        value_year_max_hispanic_pct = df_pct[df_pct['Year']==year_max]['Hispanic or Latino'            ].values[0]
        value_year_max_non_white_pct = 1-value_year_max_white_pct
        value_non_white_pct_diff = abs(value_year_max_non_white_pct - value_year_min_non_white_pct)
        if value_non_white_pct_diff > 0: increased_or_decreased_value_non_white_pct = 'increased'
        else: increased_or_decreased_value_non_white_pct = 'decreased'
        value_white_pct_diff = abs(value_year_max_white_pct - value_year_min_white_pct)
        if value_white_pct_diff > 0: increased_or_decreased_value_white_pct = 'increased'
        else: increased_or_decreased_value_white_pct = 'decreased'
        value_year_max_non_white = df_prod[df_prod['Year'] == year_max].sum(axis=1).reset_index(drop=True)[0] - df_prod[df_prod['Year'] == year_max]['White (NH)'].sum()
        dt_find_replace['[POPEMP_2_year_min]'] = year_min
        dt_find_replace['[POPEMP_2_year_max]'] = year_max
        dt_find_replace['[POPEMP_2_value_year_max_white_pct]'   ] = f'{value_year_max_white_pct:.1%}'
        dt_find_replace['[POPEMP_2_value_year_max_black_pct]'   ] = f'{value_year_max_black_pct:.1%}'
        dt_find_replace['[POPEMP_2_value_year_max_asian_pct]'   ] = f'{value_year_max_asian_pct:.1%}'
        dt_find_replace['[POPEMP_2_value_year_max_hispanic_pct]'] = f'{value_year_max_hispanic_pct:.1%}'
        dt_find_replace['[POPEMP_2_value_non_white_pct_diff]'] = f'{value_non_white_pct_diff:.1f}'
        dt_find_replace['[POPEMP_2_increased_or_decreased_value_white_pct]'    ] = increased_or_decreased_value_white_pct
        dt_find_replace['[POPEMP_2_increased_or_decreased_value_non_white_pct]'] = increased_or_decreased_value_non_white_pct
        dt_find_replace['[POPEMP_2_value_year_max_non_white]'                  ] = f'{value_year_max_non_white:,.0f}'

    if indicator == 'POPEMP_4':
        value_year_max_under_18 = df_prod[df_prod['Age Group'].isin(['Age 0-4', 'Age 5-17'])][f'Year {ACS_YEAR_MAX}'].sum()
        value_year_max_over_65  = df_prod[df_prod['Age Group'].isin(['Age 65-74', 'Age 75-84', 'Age 85+'])][f'Year {ACS_YEAR_MAX}'].sum()
        value_year_max_total = df_prod[f'Year {ACS_YEAR_MAX}'].sum()
        value_year_max_under_18_pct = value_year_max_under_18/value_year_max_total
        value_year_max_over_65_pct  = value_year_max_over_65 /value_year_max_total
        cols_years = [int(col.replace('Year ', '')) for col in df_prod.columns if 'Year' in col]
        year_min = np.min(cols_years)
        value_year_min_under_18 = df_prod[df_prod['Age Group'].isin(['Age 0-4'  , 'Age 5-17'            ])][f'Year {year_min}'].sum()
        value_year_min_over_65  = df_prod[df_prod['Age Group'].isin(['Age 65-74', 'Age 75-84', 'Age 85+'])][f'Year {year_min}'].sum()
        if value_year_max_under_18 > value_year_min_under_18: increased_or_decreased_under_18 = 'increased'
        else: increased_or_decreased_under_18 = 'decreased'
        if value_year_max_over_65 > value_year_min_over_65: increased_or_decreased_over_65 = 'increased'
        else: increased_or_decreased_over_65 = 'decreased'
        dt_find_replace['[POPEMP_4_year_min]'                       ] = year_min
        dt_find_replace['[POPEMP_4_year_max]'                       ] = ACS_YEAR_MAX
        dt_find_replace['[POPEMP_4_value_year_max_under_18]'        ] = f'{value_year_max_under_18:,.0f}'
        dt_find_replace['[POPEMP_4_value_year_max_over_65]'         ] = f'{value_year_max_over_65:,.0f}'
        dt_find_replace['[POPEMP_4_value_year_max_under_18_pct]'    ] = f'{value_year_max_under_18_pct:.1%}'
        dt_find_replace['[POPEMP_4_value_year_max_over_65_pct]'     ] = f'{value_year_max_over_65_pct:.1%}'
        dt_find_replace['[POPEMP_4_increased_or_decreased_under_18]'] = increased_or_decreased_under_18
        dt_find_replace['[POPEMP_4_increased_or_decreased_over_65]' ] = increased_or_decreased_over_65
        
    if indicator == 'POPEMP_5':
        value_pct_moved        = (df_prod[df_prod['Geography']==jurisdiction  ].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0] - df_prod[df_prod['Geography']==jurisdiction  ]['Same house'].sum()) / df_prod[df_prod['Geography']==jurisdiction  ].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0]
        value_pct_moved_region = (df_prod[df_prod['Geography']=='SACOG Region'].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0] - df_prod[df_prod['Geography']=='SACOG Region']['Same house'].sum()) / df_prod[df_prod['Geography']=='SACOG Region'].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0]
        value_pct_moved_diff = abs(value_pct_moved - value_pct_moved_region)
        if value_pct_moved > value_pct_moved_region: more_or_less_region = 'more'
        else: more_or_less_region = 'less'
        dt_find_replace['[POPEMP_5_value_pct_moved]'       ] = f'{value_pct_moved:.1%}'
        dt_find_replace['[POPEMP_5_value_pct_moved_region]'] = f'{value_pct_moved_region:.1%}'
        dt_find_replace['[POPEMP_5_value_pct_moved_diff]'  ] = f'{value_pct_moved_diff:.1%}'
        dt_find_replace['[POPEMP_5_more_or_less_region]'   ] = more_or_less_region
        
    if indicator == 'POPEMP_11':
        value_jobs_pct_diff = abs((df_prod[df_prod['Year']==year_max].drop('Year', axis=1).sum(axis=1, numeric_only=True)[df_prod.shape[0]-1]/df_prod[df_prod['Year']==year_min].drop('Year', axis=1).sum(axis=1, numeric_only=True)[0])-1)
        if value_jobs_pct_diff > 0: increase_or_decrease_jobs = 'increased'
        else: increase_or_decrease_jobs = 'decreased'
        dt_find_replace['[POPEMP_11_value_jobs_pct_diff]'      ] = f'{value_jobs_pct_diff:.1%}'
        dt_find_replace['[POPEMP_11_increase_or_decrease_jobs]'] = increase_or_decrease_jobs
        
    if indicator == 'POPEMP_12':
        most_common_industry = df_prod.columns[df_prod[df_prod['Year']==year_max].isin([df_prod[df_prod['Year']==year_max].drop('Year', axis=1).values.max(1)[0]]).any()][0]
        dt_find_replace['[POPEMP_12_most_common_industry]'] = most_common_industry
        
    if indicator == 'POPEMP_13':
        value_year_min = df_prod[df_prod['Year']==year_min][jurisdiction].values[0]
        value_year_max = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]
        if value_year_max > value_year_min: increase_or_decrease_ratio = 'increased'
        else: increase_or_decrease_ratio = 'decreased'
        dt_find_replace['[POPEMP_13_value_year_min]'            ] = f'{value_year_min:.2f}'
        dt_find_replace['[POPEMP_13_value_year_max]'            ] = f'{value_year_max:.2f}'
        dt_find_replace['[POPEMP_13_increase_or_decrease_ratio]'] = increase_or_decrease_ratio
        
    if indicator == 'POPEMP_15':
        year_back1 = year_max-1
        value_rate_diff = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]*100 - df_prod[df_prod['Year']==year_back1][jurisdiction].values[0]*100
        if value_rate_diff > 0: increase_or_decrease_rate = 'increased'
        else: increase_or_decrease_rate = 'decreased'
        dt_find_replace['[POPEMP_15_year_back1]'               ] = year_back1
        dt_find_replace['[POPEMP_15_value_rate_diff]'          ] = f'{abs(value_rate_diff):.1f}'
        dt_find_replace['[POPEMP_15_increase_or_decrease_rate]'] = increase_or_decrease_rate
        
    if indicator == 'HSG_1':
        year_min = 2010
        year_max = 2024
        value_year_min_sfd = df_prod[df_prod['Housing Type'] == 'Single Family Detached'        ][f'Year {year_min}'].values[0] / df_prod[f'Year {year_min}'].sum()
        value_year_min_sfa = df_prod[df_prod['Housing Type'] == 'Single Family Attached'        ][f'Year {year_min}'].values[0] / df_prod[f'Year {year_min}'].sum()
        value_year_min_mfs = df_prod[df_prod['Housing Type'] == 'Multifamily: Two to Four Units'][f'Year {year_min}'].values[0] / df_prod[f'Year {year_min}'].sum()
        value_year_min_mfl = df_prod[df_prod['Housing Type'] == 'Multifamily: 5+ Units'         ][f'Year {year_min}'].values[0] / df_prod[f'Year {year_min}'].sum()
        df_prod['diff'] = df_prod[f'Year {year_max}']-df_prod[f'Year {year_min}']
        value_diff_sf_mf = (df_prod[df_prod['Housing Type'] == 'Single Family Detached']['diff'].values[0] + df_prod[df_prod['Housing Type'] == 'Single Family Detached']['diff'].values[0]) - (df_prod[df_prod['Housing Type'] == 'Multifamily: Two to Four Units']['diff'].values[0] + df_prod[df_prod['Housing Type'] == 'Multifamily: 5+ Units']['diff'].values[0])
        if value_diff_sf_mf > 0: more_or_less_units = 'more'
        else: more_or_less_units = 'less'
        dt_find_replace['[HSG_1_year_min]'          ] = year_min
        dt_find_replace['[HSG_1_year_max]'          ] = year_max
        dt_find_replace['[HSG_1_value_year_min_sfd]'] = f'{value_year_min_sfd:,.0f}'
        dt_find_replace['[HSG_1_value_year_min_sfa]'] = f'{value_year_min_sfa:,.0f}'
        dt_find_replace['[HSG_1_value_year_min_mfs]'] = f'{value_year_min_mfs:,.0f}'
        dt_find_replace['[HSG_1_value_year_min_mfl]'] = f'{value_year_min_mfl:,.0f}'
        dt_find_replace['[HSG_1_more_or_less_units]'] = more_or_less_units
        
    if indicator == 'HSG_8':
        value_home_price_inc = abs((df_prod[df_prod['Year']==year_max][jurisdiction].values[0]/df_prod[df_prod['Year']==year_min][jurisdiction].values[0])-1)
        dt_find_replace['[HSG_8_value_home_price_inc]'] = f'{value_home_price_inc:.1%}'
        # dt_find_replace['[HSG_8_value_home_price_inc]'] = f'${value_home_price_inc:,.2f}'
        
    if indicator == 'OVER_5':
        value_pct_less_than_30 = abs(df_prod['0%-30% of income used for housing'].sum()/df_prod.drop('Income Level', axis=1).sum().sum())
        value_pct_more_than_50 = abs(df_prod['50%+ of income used for housing'  ].sum()/df_prod.drop('Income Level', axis=1).sum().sum())
        dt_find_replace['[OVER_5_value_pct_less_than_30]'] = f'{value_pct_less_than_30:.1%}'
        dt_find_replace['[OVER_5_value_pct_more_than_50]'] = f'{value_pct_more_than_50:.1%}'

    if indicator == 'FARM_2':
        value_year_max_permanent = df_prod[df_prod['Farm Worker']=='Permanent']['Year 2022'].values[0]
        value_year_max_seasonal  = df_prod[df_prod['Farm Worker']=='Seasonal' ]['Year 2022'].values[0]
        dt_find_replace['[FARM_2_value_year_max_permanent]'] = f'{value_year_max_permanent:,.0f}'
        dt_find_replace['[FARM_2_value_year_max_seasonal]' ] = f'{value_year_max_seasonal:,.0f}'
    
    if indicator == 'LGFEM_2':
        pct_5_plus = df_pct[df_pct['Geography']==jurisdiction]['5 or more person households'].values[0]
        dt_find_replace['[LGFEM_2_pct_5_plus]'] = f'{pct_5_plus:.1%}'

    if indicator == 'LGFEM_4':
        pct_female_headed_family_household = df_prod[df_prod['Household Type']=='Female-headed family household'].sum(numeric_only=True).sum()/df_prod.sum(numeric_only=True).sum()
        dt_find_replace['[LGFEM_4_pct_female_headed_family_household]'] = f'{pct_female_headed_family_household:.1%}'

    if indicator == 'SEN_2':
        pct_non_white_under_18 = 1-df_pct[df_pct['Age Group'] == 'Age 0-17']['White (NH)'].values[0]
        pct_non_white_over_65  = 1-df_pct[df_pct['Age Group'] == 'Age 65+' ]['White (NH)'].values[0]
        dt_find_replace['[SEN_2_pct_non_white_under_18]'] = f'{pct_non_white_under_18:.1%}'
        dt_find_replace['[SEN_2_pct_non_white_over_65]' ] = f'{pct_non_white_over_65:.1%}'

    if indicator == 'DISAB_2':
        pct_disability = df_pct[df_pct['Geography']==jurisdiction]['With a disability'].values[0]
        dt_find_replace['[DISAB_2_pct_disability]'] = f'{pct_disability:.1%}'

    if indicator == 'HOMELS_2':
        value_homeless = df_prod['Homeless population'].sum()
        dt_find_replace['[HOMELS_2_value_homeless]'] = f'{value_homeless:,.0f}'


    return dt_find_replace






# Main ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------





indicators = [
    'POPEMP_1'
    , 'POPEMP_2'
    , 'POPEMP_4'
    , 'POPEMP_5'
    , 'POPEMP_11'
    , 'POPEMP_12'
    , 'POPEMP_13'
    , 'POPEMP_15'
    , 'HSG_1'
    , 'HSG_8'
    , 'OVER_5'
    , 'FARM_2'
    , 'LGFEM_2'
    , 'LGFEM_4'
    , 'SEN_2'
    , 'DISAB_2'
    , 'HOMELS_2'
    ]
# indicators = ['POPEMP_2']



TEST_RUN=False

ACS_YEAR_MAX = '2023'




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
        county = folder.stem; print(county); print()
        dt_errors[county] = {}

        path_county = PATH_PROD / county
        for folder in path_county.iterdir():
            # if folder.stem not in ['Folsom']:
            #     continue
            jurisdiction = folder.stem; print(jurisdiction)
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