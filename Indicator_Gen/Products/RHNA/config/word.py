
import pandas as pd
import numpy as np
from pathlib import Path
import re
import sys
sys.path.append(str(Path(__file__).parent))
import rhna
FILE_YAML = rhna.load_yaml()
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'

ACS_YEAR_MAX = 2023


def popemp_1(dt_find_replace, df_prod, jurisdiction, year_max, year_min):
    prod_year_min = df_prod[df_prod['Year']==year_min][jurisdiction].values[0]
    prod_year_max = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]
    prod_pct_diff = abs((prod_year_max / prod_year_min) - 1)
    if prod_pct_diff > 0:
        increased_or_decreased_pop = 'increased'
    else:
        increased_or_decreased_pop = 'decreased'
    prod_year_min_region = df_prod[df_prod['Year']==year_min]['SACOG'].values[0]
    prod_year_max_region = df_prod[df_prod['Year']==year_max]['SACOG'].values[0]
    prod_pct_diff_region = abs((prod_year_max_region / prod_year_min_region) - 1)
    if prod_pct_diff > prod_pct_diff_region:
        above_or_below_region = 'above'
    else:
        above_or_below_region = 'below'
    prod_year_max_pct_region = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]/df_prod[df_prod['Year']==year_max]['SACOG'].values[0]
    prod_pct_diff_2020 = abs((prod_year_max / df_prod[df_prod['Year']==2020][jurisdiction].values[0]) - 1)
    if prod_pct_diff_2020 > 0:
        increased_or_decreased_pop_2020 = 'increased'
    else:
        increased_or_decreased_pop_2020 = 'decreased'
    dt_find_replace['[POPEMP_1_prod_year_min]'             ] = f'{prod_year_min:,.0f}'
    dt_find_replace['[POPEMP_1_prod_year_max]'             ] = f'{prod_year_max:,.0f}'
    dt_find_replace['[POPEMP_1_prod_pct_diff]'             ] = f'{prod_pct_diff:.1%}'
    dt_find_replace['[POPEMP_1_prod_pct_diff_region]'      ] = f'{prod_pct_diff_region:.1%}'
    dt_find_replace['[POPEMP_1_increased_or_decreased_pop]'] = increased_or_decreased_pop
    dt_find_replace['[POPEMP_1_above_or_below_region]'     ] = above_or_below_region
    dt_find_replace['[POPEMP_1_prod_pct_region]'           ] = f'{prod_year_max_pct_region:.1%}'
    dt_find_replace['[POPEMP_1_prod_pct_diff_2020]'        ] = f'{prod_pct_diff_2020:.1%}'
    dt_find_replace['[POPEMP_1_increased_or_decreased_pop_2020]'] = increased_or_decreased_pop_2020
    return dt_find_replace

def popemp_2(dt_find_replace, df_prod, df_pct):
    df_prod = df_prod.set_index(df_prod.columns[0]).T.reset_index(names='Year')
    df_pct  = df_pct .set_index(df_pct .columns[0]).T.reset_index(names='Year')
    df_prod['Year'] = df_prod['Year'].str.replace('Year ', '').astype(int)
    df_pct ['Year'] = df_pct ['Year'].str.replace('Year ', '').astype(int)
    year_min = df_prod['Year'].min()
    year_max = df_prod['Year'].max()
    prod_year_min_white_pct    = df_pct[df_pct['Year']==year_min]['White (NH)'].values[0]
    prod_year_min_non_white_pct = 1-prod_year_min_white_pct
    prod_year_max_white_pct    = df_pct[df_pct['Year']==year_max]['White (NH)'                    ].values[0]
    prod_year_max_black_pct    = df_pct[df_pct['Year']==year_max]['Black or African American (NH)'].values[0]
    prod_year_max_asian_pct    = df_pct[df_pct['Year']==year_max]['Asian (NH)'                    ].values[0]
    prod_year_max_hispanic_pct = df_pct[df_pct['Year']==year_max]['Hispanic or Latino'            ].values[0]
    prod_year_max_non_white_pct = 1-prod_year_max_white_pct
    prod_non_white_pct_diff = abs(prod_year_max_non_white_pct - prod_year_min_non_white_pct)
    if prod_year_max_non_white_pct > prod_year_min_non_white_pct:
        increased_or_decreased_prod_non_white_pct = 'increased'
    else:
        increased_or_decreased_prod_non_white_pct = 'decreased'
    prod_white_pct_diff = prod_year_max_white_pct - prod_year_min_white_pct
    if prod_white_pct_diff > 0:
        increased_or_decreased_prod_white_pct = 'increased'
    else:
        increased_or_decreased_prod_white_pct = 'decreased'
    prod_year_max_non_white = df_prod[df_prod['Year'] == year_max].sum(axis=1).reset_index(drop=True)[0] - df_prod[df_prod['Year'] == year_max]['White (NH)'].sum()
    dt_find_replace['[POPEMP_2_year_min]'] = year_min
    dt_find_replace['[POPEMP_2_year_max]'] = year_max
    dt_find_replace['[POPEMP_2_prod_year_max_white_pct]'   ] = f'{prod_year_max_white_pct:.1%}'
    dt_find_replace['[POPEMP_2_prod_year_max_black_pct]'   ] = f'{prod_year_max_black_pct:.1%}'
    dt_find_replace['[POPEMP_2_prod_year_max_asian_pct]'   ] = f'{prod_year_max_asian_pct:.1%}'
    dt_find_replace['[POPEMP_2_prod_year_max_hispanic_pct]'] = f'{prod_year_max_hispanic_pct:.1%}'
    dt_find_replace['[POPEMP_2_prod_non_white_pct_diff]'] = f'{prod_non_white_pct_diff:.1f}'
    dt_find_replace['[POPEMP_2_increased_or_decreased_prod_white_pct]'    ] = increased_or_decreased_prod_white_pct
    dt_find_replace['[POPEMP_2_increased_or_decreased_prod_non_white_pct]'] = increased_or_decreased_prod_non_white_pct
    dt_find_replace['[POPEMP_2_prod_year_max_non_white]'                  ] = f'{prod_year_max_non_white:,.0f}'
    return dt_find_replace

def popemp_4(dt_find_replace, df_prod):
    prod_year_max_under_18 = df_prod[df_prod['Age Group'].isin(['Age 0-4', 'Age 5-17'])][f'Year {ACS_YEAR_MAX}'].sum()
    prod_year_max_over_65  = df_prod[df_prod['Age Group'].isin(['Age 65-74', 'Age 75-84', 'Age 85+'])][f'Year {ACS_YEAR_MAX}'].sum()
    prod_year_max_total = df_prod[f'Year {ACS_YEAR_MAX}'].sum()
    prod_year_max_under_18_pct = prod_year_max_under_18/prod_year_max_total
    prod_year_max_over_65_pct  = prod_year_max_over_65 /prod_year_max_total
    cols_years = [int(col.replace('Year ', '')) for col in df_prod.columns if 'Year' in col]
    year_min = np.min(cols_years)
    prod_year_min_under_18 = df_prod[df_prod['Age Group'].isin(['Age 0-4'  , 'Age 5-17'            ])][f'Year {year_min}'].sum()
    prod_year_min_over_65  = df_prod[df_prod['Age Group'].isin(['Age 65-74', 'Age 75-84', 'Age 85+'])][f'Year {year_min}'].sum()
    if prod_year_max_under_18 > prod_year_min_under_18:
        increased_or_decreased_under_18 = 'increased'
    else:
        increased_or_decreased_under_18 = 'decreased'
    if prod_year_max_over_65 > prod_year_min_over_65:
        increased_or_decreased_over_65 = 'increased'
    else:
        increased_or_decreased_over_65 = 'decreased'
    dt_find_replace['[POPEMP_4_year_min]'] = year_min
    dt_find_replace['[POPEMP_4_year_max]'] = ACS_YEAR_MAX
    dt_find_replace['[POPEMP_4_prod_year_max_under_18]'    ] = f'{prod_year_max_under_18:,.0f}'
    dt_find_replace['[POPEMP_4_prod_year_max_over_65]'     ] = f'{prod_year_max_over_65:,.0f}'
    dt_find_replace['[POPEMP_4_prod_year_max_under_18_pct]'] = f'{prod_year_max_under_18_pct:.1%}'
    dt_find_replace['[POPEMP_4_prod_year_max_over_65_pct]' ] = f'{prod_year_max_over_65_pct:.1%}'
    dt_find_replace['[POPEMP_4_increased_or_decreased_under_18]'] = increased_or_decreased_under_18
    dt_find_replace['[POPEMP_4_increased_or_decreased_over_65]' ] = increased_or_decreased_over_65
    return dt_find_replace

def popemp_5(dt_find_replace, df_prod, jurisdiction):
    df_prod = df_prod.set_index(df_prod.columns[0]).T.reset_index(names='Geography')
    prod_pct_moved        = (df_prod[df_prod['Geography']==jurisdiction  ].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0] - df_prod[df_prod['Geography']==jurisdiction  ]['Same house'].sum()) / df_prod[df_prod['Geography']==jurisdiction  ].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0]
    prod_pct_moved_region = (df_prod[df_prod['Geography']=='SACOG Region'].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0] - df_prod[df_prod['Geography']=='SACOG Region']['Same house'].sum()) / df_prod[df_prod['Geography']=='SACOG Region'].drop('Geography', axis=1).sum(axis=1).reset_index(drop=True)[0]
    prod_pct_moved_diff = abs(prod_pct_moved - prod_pct_moved_region)
    if prod_pct_moved > prod_pct_moved_region:
        more_or_less_region = 'more'
    else:
        more_or_less_region = 'less'
    dt_find_replace['[POPEMP_5_prod_pct_moved]'       ] = f'{prod_pct_moved:.1%}'
    dt_find_replace['[POPEMP_5_prod_pct_moved_region]'] = f'{prod_pct_moved_region:.1%}'
    dt_find_replace['[POPEMP_5_prod_pct_moved_diff]'  ] = f'{prod_pct_moved_diff:.1%}'
    dt_find_replace['[POPEMP_5_more_or_less_region]'  ] = more_or_less_region
    return dt_find_replace

def popemp_6(dt_find_replace, df_pct, jurisdiction, county):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    df_t        = df_pct[df_pct['Geography']==jurisdiction      ].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Industry', 0:'Pct'})
    df_t_county = df_pct[df_pct['Geography']==f'{county} County'].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Industry', 0:'Pct'})
    df_t_region = df_pct[df_pct['Geography']=='SACOG Region'    ].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Industry', 0:'Pct'})
    pct_most_common_industry        = df_t       ['Pct'].max()
    pct_most_common_industry_county = df_t_county['Pct'].max()
    pct_most_common_industry_region = df_t_region['Pct'].max()
    most_common_industry        = df_t       [df_t       ['Pct']==pct_most_common_industry       ]['Industry'].values[0].lower()
    most_common_industry_county = df_t_county[df_t_county['Pct']==pct_most_common_industry_county]['Industry'].values[0].lower()
    most_common_industry_region = df_t_region[df_t_region['Pct']==pct_most_common_industry_region]['Industry'].values[0].lower()
    dt_find_replace['[POPEMP_6_most_common_industry]'       ] = most_common_industry
    dt_find_replace['[POPEMP_6_most_common_industry_county]'] = most_common_industry_county
    dt_find_replace['[POPEMP_6_most_common_industry_region]'] = most_common_industry_region
    return dt_find_replace

def popemp_11(dt_find_replace, df_prod, year_max, year_min):
    prod_year_max_total = df_prod[df_prod['Year']==year_max].drop('Year', axis=1).sum(axis=1).values[0]
    prod_jobs_pct_diff = abs((df_prod[df_prod['Year']==year_max].drop('Year', axis=1).sum(axis=1, numeric_only=True)[df_prod.shape[0]-1]/df_prod[df_prod['Year']==year_min].drop('Year', axis=1).sum(axis=1, numeric_only=True)[0])-1)
    if prod_jobs_pct_diff > 0:
        increased_or_decreased_jobs = 'increased'
    else:
        increased_or_decreased_jobs = 'decreased'
    dt_find_replace['[POPEMP_11_prod_jobs_pct_diff]'] = f'{prod_jobs_pct_diff:.1%}'
    dt_find_replace['[POPEMP_11_increased_or_decreased_jobs]'] = increased_or_decreased_jobs
    dt_find_replace['[POPEMP_11_prod_year_max_total]'] = f'{prod_year_max_total:,.0f}'
    return dt_find_replace

def popemp_12(dt_find_replace, df_prod, year_max):
    prod_year_max_total = df_prod[df_prod['Year']==year_max].drop('Year', axis=1).sum(axis=1).values[0]
    most_common_industry = df_prod.columns[df_prod[df_prod['Year']==year_max].isin([df_prod[df_prod['Year']==year_max].drop('Year', axis=1).values.max(1)[0]]).any()][0]
    dt_find_replace['[POPEMP_12_most_common_industry]'] = most_common_industry
    dt_find_replace['[POPEMP_12_prod_year_max_total]' ] = f'{prod_year_max_total:,.0f}'
    return dt_find_replace

def popemp_13(dt_find_replace, df_prod, jurisdiction, year_max, year_min):
    prod_year_min = df_prod[df_prod['Year']==year_min][jurisdiction].values[0]
    prod_year_max = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]
    if prod_year_max > prod_year_min:
        increased_or_decreased_ratio = 'increased'
    else:
        increased_or_decreased_ratio = 'decreased'
    if prod_year_max > 1:
        importer_or_exporter = 'importer'
    else:
        importer_or_exporter = 'exporter'
    dt_find_replace['[POPEMP_13_prod_year_min]'] = f'{prod_year_min:.2f}'
    dt_find_replace['[POPEMP_13_prod_year_max]'] = f'{prod_year_max:.2f}'
    dt_find_replace['[POPEMP_13_increased_or_decreased_ratio]'] = increased_or_decreased_ratio
    dt_find_replace['[POPEMP_13_importer_or_exporter]'] = importer_or_exporter
    return dt_find_replace


def popemp_14(dt_find_replace, df_prod, year_max, county, jurisdiction):
    file_mpo = PATH_OUT / county.replace(' County', '') / jurisdiction / 'tables' / 'POPEMP_14_prod_mpo.csv'
    df_mpo = pd.read_csv(file_mpo)
    df_mpo = df_mpo.groupby(['Year'], as_index=False).agg(num_jobs_wac=('num_jobs_wac', 'sum'), num_jobs_rac=('num_jobs_rac', 'sum'))
    df_mpo['Ratio'] = df_mpo['num_jobs_wac'] / df_mpo['num_jobs_rac']   
    prod_year_max_region = df_mpo[df_mpo['Year']==year_max]['Ratio'].values[0]
    prod_year_max_low_ratio  = df_prod[(df_prod['Year']==year_max) & (df_prod['Wage Group']=='Earnings &#36;1,250/month or less'     )]['Ratio'].values[0]
    prod_year_max_high_ratio = df_prod[(df_prod['Year']==year_max) & (df_prod['Wage Group']=='Earnings greater than &#36;3,333/month')]['Ratio'].values[0]
    if prod_year_max_low_ratio > 1:
        more_or_less_low_wage_jobs = 'more'
    else:
        more_or_less_low_wage_jobs = 'less'
    if prod_year_max_high_ratio > 1:
        more_or_less_high_wage_jobs = 'more'
    else:
        more_or_less_high_wage_jobs = 'less'
    if prod_year_max_region > 1:
        import_or_export_region = 'import'
        if prod_year_max_region > 1.1:
            small_or_modest_or_large_region = 'modest'
            if prod_year_max_region > 1.25:
                small_or_modest_or_large_region = 'large'
        else:
            small_or_modest_or_large_region = 'small'
    else:
        import_or_export_region = 'export'
        if prod_year_max_region < 0.9:
            small_or_modest_or_large_region = 'modest'
            if prod_year_max_region < 0.75:
                small_or_modest_or_large_region = 'large'
        else:
            small_or_modest_or_large_region = 'small'
    dt_find_replace['[POPEMP_14_more_or_less_low_wage_jobs]' ] = more_or_less_low_wage_jobs
    dt_find_replace['[POPEMP_14_more_or_less_high_wage_jobs]'] = more_or_less_high_wage_jobs
    dt_find_replace['[POPEMP_14_prod_year_max_region]'           ] = f'{prod_year_max_region:.2f}'
    dt_find_replace['[POPEMP_14_import_or_export_region]'        ] = import_or_export_region
    dt_find_replace['[POPEMP_14_small_or_modest_or_large_region]'] = small_or_modest_or_large_region
    return dt_find_replace

def popemp_15(dt_find_replace, df_prod, jurisdiction, year_max, year_min):
    year_back1 = year_max-1
    prod_rate_diff = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]*100 - df_prod[df_prod['Year']==year_back1][jurisdiction].values[0]*100
    if prod_rate_diff > 0:
        increased_or_decreased_rate = 'increased'
    else:
        increased_or_decreased_rate = 'decreased'
    prod_rate_diff_year_min = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]*100 - df_prod[df_prod['Year']==year_min][jurisdiction].values[0]*100
    if prod_rate_diff_year_min > 0:
        increase_or_decrease_rate_year_min = 'increase'
    else:
        increase_or_decrease_rate_year_min = 'decrease'
    dt_find_replace['[POPEMP_15_year_back1]'] = year_back1
    dt_find_replace['[POPEMP_15_prod_rate_diff]'] = f'{abs(prod_rate_diff):.1f}'
    dt_find_replace['[POPEMP_15_increased_or_decreased_rate]'] = increased_or_decreased_rate
    dt_find_replace['[POPEMP_15_prod_rate_diff_year_min]'] = f'{abs(prod_rate_diff_year_min):.1f}'
    dt_find_replace['[POPEMP_15_increase_or_decrease_rate_year_min]'] = increase_or_decrease_rate_year_min
    return dt_find_replace

def popemp_16(dt_find_replace, df_prod, df_pct, jurisdiction, county):
    df_prod = df_prod.set_index(df_prod.columns[0]).T.reset_index(names='Geography')
    df_pct  = df_pct .set_index(df_pct .columns[0]).T.reset_index(names='Geography')
    prod_total = df_prod[df_prod['Geography']==jurisdiction].sum(numeric_only=True).sum()
    prod_total_rent = df_prod[df_prod['Geography']==jurisdiction]['Renter occupied'].sum()
    prod_total_own  = df_prod[df_prod['Geography']==jurisdiction]['Owner occupied' ].sum()
    if prod_total_rent > prod_total_own:
        more_or_less_renters = 'more'
    else:
        more_or_less_renters = 'less'
    pct_rent = df_pct[df_pct['Geography']==jurisdiction]['Renter occupied'].values[0]
    pct_own  = df_pct[df_pct['Geography']==jurisdiction]['Owner occupied' ].values[0]
    pct_rent_county = df_pct[df_pct['Geography']==f'{county} County']['Renter occupied'].values[0]
    pct_own_region  = df_pct[df_pct['Geography']== 'SACOG Region'   ]['Owner occupied' ].values[0]
    dt_find_replace['[POPEMP_16_prod_total]'] = f'{prod_total:,.0f}'
    dt_find_replace['[POPEMP_16_more_or_less_renters]'] = more_or_less_renters
    dt_find_replace['[POPEMP_16_pct_rent]'] = f'{pct_rent:.1%}'
    dt_find_replace['[POPEMP_16_pct_own]' ] = f'{pct_own:.1%}'
    dt_find_replace['[POPEMP_16_pct_rent_county]'] = f'{pct_rent_county:.1%}'
    dt_find_replace['[POPEMP_16_pct_own_region]' ] = f'{pct_own_region:.1%}'
    return dt_find_replace

def popemp_18(dt_find_replace, df_prod):
    prod_25_44_rent_pct   = df_prod[df_prod['Age Group'].isin(['Age 25-34', 'Age 35-44'])]['Renter occupied'].sum() / df_prod[df_prod['Age Group'].isin(['Age 25-34', 'Age 35-44'           ])].sum(numeric_only= True).sum()
    prod_over_65_rent_pct = df_prod[df_prod['Age Group'].isin(['Age 25-34', 'Age 35-44'])]['Renter occupied'].sum() / df_prod[df_prod['Age Group'].isin(['Age 65-74', 'Age 75-84', 'Age 85+'])].sum(numeric_only= True).sum()
    dt_find_replace['[POPEMP_18_prod_25_44_rent_pct]'  ] = f'{prod_25_44_rent_pct:.1%}'
    dt_find_replace['[POPEMP_18_prod_over_65_rent_pct]'] = f'{prod_over_65_rent_pct:.1%}'
    return dt_find_replace

def popemp_20(dt_find_replace, df_pct):
    try:
        pct_own_black = df_pct[df_pct['Race/Ethnicity']=='Black or African American']['Owner occupied'].values[0]; dt_find_replace['[POPEMP_20_pct_own_black]'] = f'{pct_own_black:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_own_black=None
    try:
        pct_own_asian = df_pct[df_pct['Race/Ethnicity']=='Asian']['Owner occupied'].values[0]; dt_find_replace['[POPEMP_20_pct_own_asian]'] = f'{pct_own_asian:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_own_asian=None
    try:
        pct_own_hispanic = df_pct[df_pct['Race/Ethnicity']=='Hispanic or Latino']['Owner occupied'].values[0]; dt_find_replace['[POPEMP_20_pct_own_hispanic]'] = f'{pct_own_hispanic:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_own_hispanic=None
    try:
        pct_own_white = df_pct[df_pct['Race/Ethnicity']=='White (NH)']['Owner occupied'].values[0]; dt_find_replace['[POPEMP_20_pct_own_white]'] = f'{pct_own_white:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_own_white=None
    return dt_find_replace

def popemp_21(dt_find_replace, df_pct):
    most_common_income_rent = df_pct[df_pct['Renter occupied'] == df_pct['Renter occupied'].max()]['Income Level'].values[0]
    most_common_income_own  = df_pct[df_pct['Owner occupied' ] == df_pct['Owner occupied' ].max()]['Income Level'].values[0]
    dt_find_replace['[POPEMP_21_most_common_income_rent]'] = most_common_income_rent
    dt_find_replace['[POPEMP_21_most_common_income_own]'] = most_common_income_own
    return dt_find_replace

def popemp_22(dt_find_replace, df_pct):
    pct_sfd_own = df_pct[df_pct['Housing Type']=='Detached single-family homes']['Owner occupied'].values[0]
    pct_mf_own  = df_pct[df_pct['Housing Type']=='Multi-family housing'        ]['Owner occupied'].values[0]
    dt_find_replace['[POPEMP_22_pct_sfd_own]'] = f'{pct_sfd_own:.1%}'
    dt_find_replace['[POPEMP_22_pct_mf_own]' ] = f'{pct_mf_own:.1%}'
    return dt_find_replace

def popemp_23(dt_find_replace, df_prod, df_pct, jurisdiction):
    df_prod = df_prod.set_index(df_prod.columns[0]).T.reset_index(names='Geography')
    df_pct  = df_pct .set_index(df_pct .columns[0]).T.reset_index(names='Geography')
    prod_most_common_household = df_prod[df_prod['Geography']==jurisdiction].max(axis=1, numeric_only=True).values[0]
    df_t = df_prod[df_prod['Geography']==jurisdiction].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Household Type', 0:'Population'})
    most_common_household = df_t[df_t['Population']==prod_most_common_household]['Household Type'].values[0]
    pct_most_common_household = df_pct[df_pct['Geography']==jurisdiction][most_common_household            ].values[0]
    pct_female_householder    = df_pct[df_pct['Geography']==jurisdiction]['Female-headed family households'].values[0]
    dt_find_replace['[POPEMP_23_most_common_household]'] = most_common_household
    dt_find_replace['[POPEMP_23_pct_most_common_household]'] = f'{pct_most_common_household:.1%}'
    dt_find_replace['[POPEMP_23_pct_female_householder]'   ] = f'{pct_female_householder:.1%}'
    return dt_find_replace

def popemp_25(dt_find_replace, df_prod):
    displacement_pct   = df_prod[df_prod['Typology'] == 'Susceptible to or Experiencing Displacement'].sum(numeric_only=True).sum() / df_prod.sum(numeric_only=True).sum()
    gentrification_pct = df_prod[df_prod['Typology'] == 'At Risk of or Experiencing Gentrification'  ].sum(numeric_only=True).sum() / df_prod.sum(numeric_only=True).sum()
    excluded_pct       = df_prod[df_prod['Typology'] == 'At Risk of or Experiencing Exclusion'       ].sum(numeric_only=True).sum() / df_prod.sum(numeric_only=True).sum()
    dt_find_replace['[POPEMP_25_displacement_pct]'  ] = f'{displacement_pct:.1%}'
    dt_find_replace['[POPEMP_25_gentrification_pct]'] = f'{gentrification_pct:.1%}'
    dt_find_replace['[POPEMP_25_excluded_pct]'      ] = f'{excluded_pct:.1%}'
    return dt_find_replace

def hsg_1(dt_find_replace, df_prod, jurisdiction, county):
    year_min = 2010
    year_max = 2024
    prod_year_min_sfd = df_prod[df_prod['Housing Type'] == 'Single Family Detached'        ][f'{jurisdiction} ({year_min})'].values[0]
    prod_year_min_sfa = df_prod[df_prod['Housing Type'] == 'Single Family Attached'        ][f'{jurisdiction} ({year_min})'].values[0]
    prod_year_min_mfs = df_prod[df_prod['Housing Type'] == 'Multifamily: Two to Four Units'][f'{jurisdiction} ({year_min})'].values[0]
    prod_year_min_mfl = df_prod[df_prod['Housing Type'] == 'Multifamily: 5+ Units'         ][f'{jurisdiction} ({year_min})'].values[0]
    df_prod['diff'] = df_prod[f'{jurisdiction} ({year_max})']-df_prod[f'{jurisdiction} ({year_min})']
    prod_diff_sf_mf = (df_prod[df_prod['Housing Type'] == 'Single Family Detached']['diff'].values[0] + df_prod[df_prod['Housing Type'] == 'Single Family Detached']['diff'].values[0]) - (df_prod[df_prod['Housing Type'] == 'Multifamily: Two to Four Units']['diff'].values[0] + df_prod[df_prod['Housing Type'] == 'Multifamily: 5+ Units']['diff'].values[0])
    if prod_diff_sf_mf > 0:
        more_or_less_units = 'more'
    else:
        more_or_less_units = 'less'
    prod_year_max_sfd = df_prod[df_prod['Housing Type'] == 'Single Family Detached'        ][f'{jurisdiction} ({year_max})'].values[0]
    prod_year_max_sfa = df_prod[df_prod['Housing Type'] == 'Single Family Attached'        ][f'{jurisdiction} ({year_max})'].values[0]
    prod_year_max_mfs = df_prod[df_prod['Housing Type'] == 'Multifamily: Two to Four Units'][f'{jurisdiction} ({year_max})'].values[0]
    prod_year_max_mfl = df_prod[df_prod['Housing Type'] == 'Multifamily: 5+ Units'         ][f'{jurisdiction} ({year_max})'].values[0]
    prod_year_max_mh  = df_prod[df_prod['Housing Type'] == 'Mobile Homes'                  ][f'{jurisdiction} ({year_max})'].values[0]
    most_growth_housing_type = df_prod[df_prod['diff']==df_prod['diff'].max()]['Housing Type'].values[0].lower()
    prod_pct_diff        = abs((df_prod[ f'{jurisdiction} ({year_max})'].sum() / df_prod[ f'{jurisdiction} ({year_min})'].sum()) - 1)
    prod_pct_diff_county = abs((df_prod[f'{county} County ({year_max})'].sum() / df_prod[f'{county} County ({year_min})'].sum()) - 1)
    prod_pct_diff_region = abs((df_prod[   f'SACOG Region ({year_max})'].sum() / df_prod[   f'SACOG Region ({year_min})'].sum()) - 1)
    if df_prod[ f'{jurisdiction} ({year_max})'].sum() > df_prod[ f'{jurisdiction} ({year_min})'].sum():
        increased_or_decreased = 'increased'
    else:
        increased_or_decreased = 'decreased'
    if increased_or_decreased == 'increased' and prod_pct_diff > prod_pct_diff_county:
        above_or_below_county = 'above'
    else:
        above_or_below_county = 'below'
    if increased_or_decreased == 'increased' and prod_pct_diff > prod_pct_diff_region:
        above_or_below_region = 'above'
    else:
        above_or_below_region = 'below'
    prod_pct_sfd = prod_year_max_sfd / df_prod[f'{jurisdiction} ({year_max})'].sum()
    prod_pct_sfd_region = df_prod[df_prod['Housing Type']=='Single Family Detached'][f'SACOG Region ({year_max})'].values[0] / df_prod[f'SACOG Region ({year_max})'].sum()
    if prod_pct_sfd > prod_pct_sfd_region:
        above_or_below_region_sfd = 'above'
    else:
        above_or_below_region_sfd = 'below'
    dt_find_replace['[HSG_1_year_min]'] = year_min
    dt_find_replace['[HSG_1_year_max]'] = year_max
    dt_find_replace['[HSG_1_prod_year_min_sfd]'] = f'{prod_year_min_sfd:,.0f}'
    dt_find_replace['[HSG_1_prod_year_min_sfa]'] = f'{prod_year_min_sfa:,.0f}'
    dt_find_replace['[HSG_1_prod_year_min_mfs]'] = f'{prod_year_min_mfs:,.0f}'
    dt_find_replace['[HSG_1_prod_year_min_mfl]'] = f'{prod_year_min_mfl:,.0f}'
    dt_find_replace['[HSG_1_more_or_less_units]'] = more_or_less_units
    dt_find_replace['[HSG_1_prod_year_max_sfd]'] = f'{prod_year_max_sfd:,.0f}'
    dt_find_replace['[HSG_1_prod_year_max_sfa]'] = f'{prod_year_max_sfa:,.0f}'
    dt_find_replace['[HSG_1_prod_year_max_mfs]'] = f'{prod_year_max_mfs:,.0f}'
    dt_find_replace['[HSG_1_prod_year_max_mfl]'] = f'{prod_year_max_mfl:,.0f}'
    dt_find_replace['[HSG_1_prod_year_max_mh]' ] = f'{prod_year_max_mh:,.0f}'
    dt_find_replace['[HSG_1_most_growth_housing_type]'] = most_growth_housing_type
    dt_find_replace['[HSG_1_prod_pct_diff]'         ] = f'{prod_pct_diff:.1%}'
    dt_find_replace['[HSG_1_prod_pct_diff_county]'  ] = f'{prod_pct_diff_county:.1%}'
    dt_find_replace['[HSG_1_increased_or_decreased]'] = increased_or_decreased
    dt_find_replace['[HSG_1_above_or_below_county]' ] = above_or_below_county
    dt_find_replace['[HSG_1_above_or_below_region]' ] = above_or_below_region
    dt_find_replace['[HSG_1_above_or_below_region_sfd]' ] = above_or_below_region_sfd
    return dt_find_replace

def hsg_2(dt_find_replace, df_pct, jurisdiction):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    pct_vacant        = df_pct[df_pct['Geography']==jurisdiction  ]['Vacant housing units'].values[0]
    pct_vacant_region = df_pct[df_pct['Geography']=='SACOG Region']['Vacant housing units'].values[0]
    dt_find_replace['[HSG_2_pct_vacant]'       ] = f'{pct_vacant:.1%}'
    dt_find_replace['[HSG_2_pct_vacant_region]'] = f'{pct_vacant_region:.1%}'
    return dt_find_replace

def hsg_3(dt_find_replace, df_pct, county, jurisdiction):
    file_sup = PATH_OUT / county.replace(' County', '') / jurisdiction / 'tables' / 'HSG_3_prod_sup.csv'
    df_prod_sup = pd.read_csv(file_sup)
    sup_vacant_for_sale_pct = df_prod_sup[df_prod_sup['Variable']== 'Owner occupied']['Percent'].values[0]
    sup_vacant_for_rent_pct = df_prod_sup[df_prod_sup['Variable']=='Renter occupied']['Percent'].values[0]
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    df_t = df_pct[df_pct['Geography']==jurisdiction].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Vacancy Type', 0:'Pct'})
    pct_most_common_vacancy_type = df_t['Pct'].max()
    most_common_vacancy_type = df_t[df_t['Pct']==pct_most_common_vacancy_type]['Vacancy Type'].values[0].lower()
    df_t_region = df_pct[df_pct['Geography']=='SACOG Region'].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Vacancy Type', 0:'Pct'})
    pct_most_common_vacancy_type_region_1 = df_t_region['Pct'].max()
    pct_most_common_vacancy_type_region_2 = df_t_region[df_t_region['Pct']<pct_most_common_vacancy_type_region_1]['Pct'].max()
    pct_most_common_vacancy_type_region_3 = df_t_region[df_t_region['Pct']<pct_most_common_vacancy_type_region_2]['Pct'].max()
    most_common_vacancy_type_region_1 = df_t_region[df_t_region['Pct']==pct_most_common_vacancy_type_region_1]['Vacancy Type'].values[0].lower()
    most_common_vacancy_type_region_2 = df_t_region[df_t_region['Pct']==pct_most_common_vacancy_type_region_2]['Vacancy Type'].values[0].lower()
    most_common_vacancy_type_region_3 = df_t_region[df_t_region['Pct']==pct_most_common_vacancy_type_region_3]['Vacancy Type'].values[0].lower()
    dt_find_replace['[HSG_3_pct_most_common_vacancy_type]'] = f'{pct_most_common_vacancy_type:.1%}'
    dt_find_replace['[HSG_3_most_common_vacancy_type]'    ] = most_common_vacancy_type
    dt_find_replace['[HSG_3_most_common_vacancy_type_region_1]'] = most_common_vacancy_type_region_1
    dt_find_replace['[HSG_3_most_common_vacancy_type_region_2]'] = most_common_vacancy_type_region_2
    dt_find_replace['[HSG_3_most_common_vacancy_type_region_3]'] = most_common_vacancy_type_region_3
    dt_find_replace['[HSG_3_sup_vacant_for_sale_pct]'] = f'{sup_vacant_for_sale_pct:.1%}'
    dt_find_replace['[HSG_3_sup_vacant_for_rent_pct]'] = f'{sup_vacant_for_rent_pct:.1%}'
    return dt_find_replace

def hsg_4(dt_find_replace, df_prod, df_pct):
    pct_most_common_year_built = df_pct['Percent'].max()
    most_common_year_built = df_pct[df_pct['Percent']==pct_most_common_year_built]['Year Built'].values[0].replace('Built ', '')
    pct_year_built_2010_or_later  = df_pct [df_pct ['Year Built']=='Built 2010 or later']['Percent'   ].values[0]
    prod_year_built_2010_or_later = df_prod[df_prod['Year Built']=='Built 2010 or later']['Households'].values[0]
    dt_find_replace['[HSG_4_pct_most_common_year_built]'  ] = f'{pct_most_common_year_built:.1%}'
    dt_find_replace['[HSG_4_most_common_year_built]'      ] = most_common_year_built
    dt_find_replace['[HSG_4_pct_year_built_2010_or_later]'] = f'{pct_year_built_2010_or_later:.1%}'
    dt_find_replace['[HSG_4_prod_year_built_2010_or_later]'] = f'{prod_year_built_2010_or_later:,.0f}'
    return dt_find_replace

def hsg_5(dt_find_replace, df_prod):
    prod_3_plus_bedrooms = df_prod[df_prod['Number of Bedrooms'].isin(['3-4 bedrooms', '5 or more bedrooms'])].sum(numeric_only= True).sum()
    prod_3_plus_bedrooms_own_pct  = df_prod[df_prod['Number of Bedrooms'].isin(['3-4 bedrooms', '5 or more bedrooms'])]['Owner occupied' ].sum() / prod_3_plus_bedrooms
    prod_3_plus_bedrooms_rent_pct = df_prod[df_prod['Number of Bedrooms'].isin(['3-4 bedrooms', '5 or more bedrooms'])]['Renter occupied'].sum() / prod_3_plus_bedrooms
    dt_find_replace['[HSG_5_prod_3_plus_bedrooms]'] = f'{prod_3_plus_bedrooms:,.0f}'
    dt_find_replace['[HSG_5_prod_3_plus_bedrooms_own_pct]' ] = f'{prod_3_plus_bedrooms_own_pct:.1%}'
    dt_find_replace['[HSG_5_prod_3_plus_bedrooms_rent_pct]'] = f'{prod_3_plus_bedrooms_rent_pct:.1%}'
    return dt_find_replace

def hsg_6(dt_find_replace, df_pct):
    try:
        pct_kitchen_rent  = df_pct[df_pct['Housing Issue']=='Lacking kitchen facilities' ]['Renter occupied'].values[0]; dt_find_replace['[HSG_6_pct_kitchen_rent]'  ] = f'{pct_kitchen_rent:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_kitchen_rent=None
    try:
        pct_kitchen_own = df_pct[df_pct['Housing Issue']=='Lacking kitchen facilities' ]['Owner occupied' ].values[0]; dt_find_replace['[HSG_6_pct_kitchen_own]'   ] = f'{pct_kitchen_own:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_kitchen_own=None
    try:
        pct_plumbing_rent = df_pct[df_pct['Housing Issue']=='Lacking plumbing facilities']['Renter occupied'].values[0]; dt_find_replace['[HSG_6_pct_plumbing_rent]' ] = f'{pct_plumbing_rent:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_plumbing_rent=None
    try: pct_plumbing_own = df_pct[df_pct['Housing Issue']=='Lacking plumbing facilities']['Owner occupied' ].values[0]; dt_find_replace['[HSG_6_pct_plumbing_own]'  ] = f'{pct_plumbing_own:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_plumbing_own=None
    return dt_find_replace

def hsg_7(dt_find_replace, df_pct, jurisdiction):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    df_t = df_pct[df_pct['Geography']==jurisdiction].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Home Value', 0:'Pct'})
    pct_most_common_home_value = df_t['Pct'].max()
    most_common_home_value = df_t[df_t['Pct']==pct_most_common_home_value]['Home Value'].values[0].replace('Units valued ', '')
    df_t_region = df_pct[df_pct['Geography']=='SACOG Region'].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Home Value', 0:'Pct'})
    pct_most_common_home_prod_region_1 = df_t_region['Pct'].max()
    pct_most_common_home_prod_region_2 = df_t_region[df_t_region['Pct']<df_t_region['Pct'].max()]['Pct'].max()
    most_common_home_prod_region_1 = df_t_region[df_t_region['Pct']==pct_most_common_home_prod_region_1]['Home Value'].values[0].replace('Units valued ', '')
    most_common_home_prod_region_2 = df_t_region[df_t_region['Pct']==pct_most_common_home_prod_region_2]['Home Value'].values[0].replace('Units valued ', '')
    dt_find_replace['[HSG_7_year_max]'] = ACS_YEAR_MAX
    dt_find_replace['[HSG_7_pct_most_common_home_value]'] = f'{pct_most_common_home_value:.1%}'
    dt_find_replace['[HSG_7_most_common_home_value]'        ] = most_common_home_value
    dt_find_replace['[HSG_7_most_common_home_prod_region_1]'] = most_common_home_prod_region_1
    dt_find_replace['[HSG_7_most_common_home_prod_region_2]'] = most_common_home_prod_region_2
    return dt_find_replace

def hsg_8(dt_find_replace, df_prod, jurisdiction, county, year_max, year_min):
    year_min = 2010
    prod_year_min = df_prod[df_prod['Year']==year_min][jurisdiction].values[0]
    prod_year_max = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]
    prod_home_price_inc = abs((prod_year_max/prod_year_min)-1)
    if prod_year_max > prod_year_min:
        increased_or_decreased = 'increased'
    else:
        increased_or_decreased = 'decreased'
    prod_year_min_county = df_prod[df_prod['Year']==year_min][f'{county} County'].values[0]
    prod_year_max_county = df_prod[df_prod['Year']==year_max][f'{county} County'].values[0]
    prod_home_price_inc_county = abs((prod_year_max_county/prod_year_min_county)-1)
    if prod_home_price_inc > prod_home_price_inc_county:
        above_or_below_county = 'above'
    else:
        above_or_below_county = 'below'
    prod_year_min_region = df_prod[df_prod['Year']==year_min]['SACOG Region'].values[0]
    prod_year_max_region = df_prod[df_prod['Year']==year_max]['SACOG Region'].values[0]
    prod_home_price_inc_region = abs((prod_year_max_region/prod_year_min_region)-1)
    if prod_home_price_inc > prod_home_price_inc_region:
        above_or_below_region = 'above'
    else:
        above_or_below_region = 'below'
    breakpoint()
    dt_find_replace['[HSG_8_year_min]'] = year_min
    dt_find_replace['[HSG_8_year_max]'] = year_max
    dt_find_replace['[HSG_8_prod_year_min]'] = f'${prod_year_min:,.0f}'
    dt_find_replace['[HSG_8_prod_year_max]'] = f'${prod_year_max:,.0f}'
    dt_find_replace['[HSG_8_prod_home_price_inc]'] = f'{prod_home_price_inc:.1%}'
    dt_find_replace['[HSG_8_prod_year_min_county]'] = f'${prod_year_min_county:,.0f}'
    dt_find_replace['[HSG_8_prod_year_max_county]'] = f'${prod_year_max_county:,.0f}'
    dt_find_replace['[HSG_8_prod_year_min_region]'] = f'${prod_year_min_region:,.0f}'
    dt_find_replace['[HSG_8_prod_year_max_region]'] = f'${prod_year_max_region:,.0f}'
    dt_find_replace['[HSG_8_increased_or_decreased]'] = increased_or_decreased
    dt_find_replace['[HSG_8_above_or_below_county]' ] = above_or_below_county
    dt_find_replace['[HSG_8_above_or_below_region]' ] = above_or_below_region
    return dt_find_replace

def hsg_9(dt_find_replace, df_pct, jurisdiction, county):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    df_t = df_pct[df_pct['Geography']==jurisdiction].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Rent Price', 0:'Pct'})
    pct_most_common_rent_price   = df_t['Pct'].max()
    pct_most_common_rent_price_2 = df_t[df_t['Pct']<df_t['Pct'].max()]['Pct'].max()
    most_common_rent_price   = df_t[df_t['Pct']==pct_most_common_rent_price  ]['Rent Price'].values[0].replace('Rent ', '')
    most_common_rent_price_2 = df_t[df_t['Pct']==pct_most_common_rent_price_2]['Rent Price'].values[0].replace('Rent ', '')
    df_t_county = df_pct[df_pct['Geography']==f'{county} County'].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Rent Price', 0:'Pct'})
    pct_most_common_rent_price_county = df_t_county['Pct'].max()
    most_common_rent_price_county   = df_t_county[df_t_county['Pct']==pct_most_common_rent_price_county]['Rent Price'].values[0].replace('Rent ', '')
    dt_find_replace['[HSG_9_pct_most_common_rent_price]'       ] = f'{pct_most_common_rent_price:.1%}'
    dt_find_replace['[HSG_9_pct_most_common_rent_price_2]'     ] = f'{pct_most_common_rent_price_2:.1%}'
    dt_find_replace['[HSG_9_pct_most_common_rent_price_county]'] = f'{pct_most_common_rent_price_county:.1%}'
    dt_find_replace['[HSG_9_most_common_rent_price]'       ] = most_common_rent_price
    dt_find_replace['[HSG_9_most_common_rent_price_2]'     ] = most_common_rent_price_2
    dt_find_replace['[HSG_9_most_common_rent_price_county]'] = most_common_rent_price_county
    return dt_find_replace

def hsg_10(dt_find_replace, df_prod, jurisdiction, county, year_max, year_min):
    prod_year_min        = df_prod[df_prod['Year']==year_min][jurisdiction].values[0]
    prod_year_max        = df_prod[df_prod['Year']==year_max][jurisdiction].values[0]
    prod_rent_pct_diff   = abs((prod_year_max/prod_year_min)-1)
    if prod_year_max > prod_year_min:
        increased_or_decreased_rent = 'increased'
    else:
        increased_or_decreased_rent = 'decreased'
    prod_year_min_county      = df_prod[df_prod['Year']==year_min][f'{county} County'].values[0]
    prod_year_max_county      = df_prod[df_prod['Year']==year_max][f'{county} County'].values[0]
    prod_rent_pct_diff_county = abs((prod_year_max_county/prod_year_min_county)-1)
    if prod_year_max_county > prod_year_min_county:
        increased_or_decreased_rent_county = 'increased'
    else:
        increased_or_decreased_rent_county = 'decreased'
    prod_year_min_region      = df_prod[df_prod['Year']==year_min]['SACOG Region'].values[0]
    prod_year_max_region      = df_prod[df_prod['Year']==year_max]['SACOG Region'].values[0]
    prod_rent_pct_diff_region = abs((prod_year_max_region/prod_year_min_region)-1)
    if prod_year_max_region > prod_year_min_region:
        increased_or_decreased_rent_region = 'increased'
    else:
        increased_or_decreased_rent_region = 'decreased'
    prod_year_max_income = prod_year_max/0.3*12
    dt_find_replace['[HSG_10_year_min]'] = year_min
    dt_find_replace['[HSG_10_year_max]'] = year_max
    dt_find_replace['[HSG_10_prod_year_min]'] = f'${prod_year_min:,.0f}'
    dt_find_replace['[HSG_10_prod_year_max]'] = f'${prod_year_max:,.0f}'
    dt_find_replace['[HSG_10_prod_year_min_county]'] = f'${prod_year_min_county:,.0f}'
    dt_find_replace['[HSG_10_prod_year_max_county]'] = f'${prod_year_max_county:,.0f}'
    dt_find_replace['[HSG_10_prod_year_min_region]'] = f'${prod_year_min_region:,.0f}'
    dt_find_replace['[HSG_10_prod_year_max_region]'] = f'${prod_year_max_region:,.0f}'
    dt_find_replace['[HSG_10_prod_rent_pct_diff]'       ] = f'{prod_rent_pct_diff:.1%}'
    dt_find_replace['[HSG_10_prod_rent_pct_diff_county]'] = f'{prod_rent_pct_diff_county:.1%}'
    dt_find_replace['[HSG_10_prod_rent_pct_diff_region]'] = f'{prod_rent_pct_diff_region:.1%}'
    dt_find_replace['[HSG_10_increased_or_decreased_rent]'     ] = increased_or_decreased_rent
    dt_find_replace['[HSG_10_increased_or_decreased_rent_county]'] = increased_or_decreased_rent_county
    dt_find_replace['[HSG_10_increased_or_decreased_rent_region]'] = increased_or_decreased_rent_region
    dt_find_replace['[HSG_10_increase_or_decrease_rent_region]'] = increased_or_decreased_rent_region[:-1]
    dt_find_replace['[HSG_10_prod_year_max_income]'] = f'${prod_year_max_income:,.0f}'
    return dt_find_replace

def hsg_11(dt_find_replace, df_prod):
    try:
        prod_total = df_prod['Number of Permits'].sum(); dt_find_replace['[HSG_11_prod_total]'] = f'{prod_total:,.0f}'
    except Exception as e:
        print(f"How exceptional! {e}")
        prod_total=None
    try:
        prod_above_mod_pct = df_prod[df_prod['Income Group']=='ABOVE MOD PERMITS']['Number of Permits'].values[0] / prod_total; dt_find_replace['[HSG_11_prod_above_mod_pct]'] = f'{prod_above_mod_pct:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        prod_above_mod_pct=None
    try:
        prod_mod_pct = df_prod[df_prod['Income Group']=='MOD PERMITS']['Number of Permits'].values[0] / prod_total; dt_find_replace['[HSG_11_prod_mod_pct]'] = f'{prod_mod_pct:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        prod_mod_pct=None
    try:
        prod_low_pct = df_prod[df_prod['Income Group'].isin(['LI PERMITS', 'VLI PERMITS'])]['Number of Permits'].sum() / prod_total; dt_find_replace['[HSG_11_prod_low_pct]'] = f'{prod_low_pct:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        prod_low_pct=None
    return dt_find_replace

## TODO: RISK_1
def risk_1(dt_find_replace, df_prod):
    pass

def over_1(dt_find_replace, df_pct):
    pct_rent_more_than_15 = df_pct[df_pct['Housing Tenure']=='Renter occupied']['More than 1.5 occupants per room'].values[0]
    pct_own_more_than_15  = df_pct[df_pct['Housing Tenure']=='Owner occupied' ]['More than 1.5 occupants per room'].values[0]
    pct_rent_1_to_15      = df_pct[df_pct['Housing Tenure']=='Renter occupied']['1.01 to 1.5 occupants per room'  ].values[0]
    pct_own_1_to_15       = df_pct[df_pct['Housing Tenure']=='Owner occupied' ]['1.01 to 1.5 occupants per room'  ].values[0]
    dt_find_replace['[OVER_1_pct_rent_more_than_15]'] = f'{pct_rent_more_than_15:.1%}'
    dt_find_replace['[OVER_1_pct_own_more_than_15]' ] = f'{pct_own_more_than_15:.1%}'
    dt_find_replace['[OVER_1_pct_rent_1_to_15]'] = f'{pct_rent_1_to_15:.1%}'
    dt_find_replace['[OVER_1_pct_own_1_to_15]' ] = f'{pct_own_1_to_15:.1%}'
    return dt_find_replace

def over_3(dt_find_replace, df_pct, jurisdiction):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    prod_most_overcrowded_ethnicity = df_pct[df_pct['Geography']==jurisdiction].max(axis=1, numeric_only=True).values[0]
    df_t = df_pct[df_pct['Geography']==jurisdiction].sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Race/Ethnicity', 0:'Population'})
    most_overcrowded_ethnicity = df_t[df_t['Population']==prod_most_overcrowded_ethnicity]['Race/Ethnicity'].values[0]
    dt_find_replace['[OVER_3_most_overcrowded_ethnicity]'] = most_overcrowded_ethnicity
    return dt_find_replace

def over_4(dt_find_replace, df_pct):
    pct_below_50_ami_15_plus = df_pct[df_pct['Income Level'].isin(['0%-30% of AMI', '31%-50% of AMI'])]['More than 1.5 occupants per room'].sum()
    pct_over_100_ami_15_plus = df_pct[df_pct['Income Level'].isin(['Greater than 100% of AMI'       ])]['More than 1.5 occupants per room'].sum()
    dt_find_replace['[OVER_4_pct_below_50_ami_15_plus]' ] = f'{pct_below_50_ami_15_plus:.1%}'
    dt_find_replace['[OVER_4_pct_over_100_ami_15_plus]' ] = f'{pct_over_100_ami_15_plus:.1%}'
    return dt_find_replace

def over_5(dt_find_replace, df_prod, df_pct):
    prod_less_than_30_pct = df_prod['0%-30% of income used for housing' ].sum()/df_prod.drop('Income Level', axis=1).sum().sum()
    prod_30_50_pct        = df_prod['30%-50% of income used for housing'].sum()/df_prod.drop('Income Level', axis=1).sum().sum()
    prod_50_plus_pct      = df_prod['50%+ of income used for housing'   ].sum()/df_prod.drop('Income Level', axis=1).sum().sum()
    pct_less_than_30_ami_50_plus  = df_pct[df_pct['Income Level']=='0%-30% of AMI'           ]['50%+ of income used for housing'  ].values[0]
    pct_100_plus_ami_50_plus      = df_pct[df_pct['Income Level']=='Greater than 100% of AMI']['50%+ of income used for housing'  ].values[0]
    pct_100_plus_ami_less_than_30 = df_pct[df_pct['Income Level']=='Greater than 100% of AMI']['0%-30% of income used for housing'].values[0]
    dt_find_replace['[OVER_5_prod_less_than_30_pct]'] = f'{prod_less_than_30_pct:.1%}'
    dt_find_replace['[OVER_5_prod_30_50_pct]'       ] = f'{prod_30_50_pct:.1%}'
    dt_find_replace['[OVER_5_prod_50_plus_pct]'     ] = f'{prod_50_plus_pct:.1%}'
    dt_find_replace['[OVER_5_pct_less_than_30_ami_50_plus]' ] = f'{pct_less_than_30_ami_50_plus:.1%}'
    dt_find_replace['[OVER_5_pct_100_plus_ami_50_plus]'     ] = f'{pct_100_plus_ami_50_plus:.1%}'
    dt_find_replace['[OVER_5_pct_100_plus_ami_less_than_30]'] = f'{pct_100_plus_ami_less_than_30:.1%}'
    return dt_find_replace

def over_6(dt_find_replace, df_pct):
    df_pct = df_pct.set_index(df_pct .columns[0]).T.reset_index(names='Housing Tenure')
    pct_30_50_rent   = df_pct[df_pct['Housing Tenure'] == 'Renter']['30%-50% of income used for housing'].values[0]
    pct_30_50_own    = df_pct[df_pct['Housing Tenure'] == 'Owner' ]['30%-50% of income used for housing'].values[0]
    pct_50_plus_rent = df_pct[df_pct['Housing Tenure'] == 'Renter']['50%+ of income used for housing'   ].values[0]
    pct_50_plus_own  = df_pct[df_pct['Housing Tenure'] == 'Owner' ]['50%+ of income used for housing'   ].values[0]
    dt_find_replace['[OVER_6_pct_30_50_rent]'  ] = f'{pct_30_50_rent:.1%}'
    dt_find_replace['[OVER_6_pct_30_50_own]'   ] = f'{pct_30_50_own:.1%}'
    dt_find_replace['[OVER_6_pct_50_plus_rent]'] = f'{pct_50_plus_rent:.1%}'
    dt_find_replace['[OVER_6_pct_50_plus_own]' ] = f'{pct_50_plus_own:.1%}'
    return dt_find_replace

def over_8(dt_find_replace, df_pct):
    df_pct['30%+ of income used for housing'] = df_pct['30%-50% of income used for housing'] + df_pct['50%+ of income used for housing']
    most_cost_burdened_ethnicity = df_pct[df_pct['30%+ of income used for housing'] == df_pct['30%+ of income used for housing'].max()]['Race/Ethnicity'].values[0]
    pct_most_cost_burdened_ethnicity_30_50   = df_pct[df_pct['Race/Ethnicity']==most_cost_burdened_ethnicity]['30%-50% of income used for housing'].values[0]
    pct_most_cost_burdened_ethnicity_50_plus = df_pct[df_pct['Race/Ethnicity']==most_cost_burdened_ethnicity]['50%+ of income used for housing'   ].values[0]
    dt_find_replace['[OVER_8_most_cost_burdened_ethnicity]'] = most_cost_burdened_ethnicity
    dt_find_replace['[OVER_8_pct_most_cost_burdened_ethnicity_30_50]'  ] = f'{pct_most_cost_burdened_ethnicity_30_50:.1%}'
    dt_find_replace['[OVER_8_pct_most_cost_burdened_ethnicity_50_plus]'] = f'{pct_most_cost_burdened_ethnicity_50_plus:.1%}'
    return dt_find_replace

def over_9(dt_find_replace, df_pct):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Household Size')
    try:
        pct_large_family_30_50 = df_pct[df_pct['Household Size']=='Large family with 5+ persons']['30%-50% of income used for housing'].values[0]; dt_find_replace['[OVER_9_pct_large_family_30_50]'  ] = f'{pct_large_family_30_50:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_large_family_30_50=None
    try: pct_large_family_50_plus = df_pct[df_pct['Household Size']=='Large family with 5+ persons']['50%+ of income used for housing'   ].values[0]; dt_find_replace['[OVER_9_pct_large_family_50_plus]'] = f'{pct_large_family_50_plus:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_large_family_50_plus=None
    try: pct_other_30_50 = df_pct[df_pct['Household Size']=='All other household types']['30%-50% of income used for housing'].values[0]; dt_find_replace['[OVER_9_pct_other_30_50]'] = f'{pct_other_30_50:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_other_30_50=None
    try: pct_other_50_plus = df_pct[df_pct['Household Size']=='All other household types']['50%+ of income used for housing'   ].values[0]; dt_find_replace['[OVER_9_pct_other_50_plus]'] = f'{pct_other_50_plus:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_other_50_plus=None
    return dt_find_replace

def farm_1(dt_find_replace, df_prod, jurisdiction):
    year_min = '2020-2021'
    year_max = '2023-2024'
    prod_year_min = df_prod[df_prod['Geography']==jurisdiction]['2020-21'].values[0]
    prod_year_max = df_prod[df_prod['Geography']==jurisdiction]['2023-24'].values[0]
    try:
        prod_pct_diff = prod_year_max/prod_year_min-1
        dt_find_replace['[FARM_1_prod_pct_diff]'] = f'{abs(prod_pct_diff):.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        prod_pct_diff=None
    if prod_pct_diff > 1:
        increase_or_decrease = 'increase'
    else:
        increase_or_decrease = 'decrease'
    if prod_pct_diff is None:
        increase_or_decrease=None
    prod_year_min_region = df_prod[df_prod['Geography']=='SACOG Region']['2020-21'].values[0]
    prod_year_max_region = df_prod[df_prod['Geography']=='SACOG Region']['2023-24'].values[0]
    prod_pct_diff_region = prod_year_max_region/prod_year_min_region-1
    if prod_pct_diff_region > 1:
        increase_or_decrease_region = 'increase'
    else:
        increase_or_decrease_region = 'decrease'
    dt_find_replace['[FARM_1_year_min]'] = year_min
    dt_find_replace['[FARM_1_year_max]'] = year_max
    dt_find_replace['[FARM_1_prod_year_min]'] = f'{prod_year_min:.0f}'
    dt_find_replace['[FARM_1_prod_year_max]'] = f'{prod_year_max:.0f}'
    dt_find_replace['[FARM_1_increase_or_decrease]'       ] = increase_or_decrease
    dt_find_replace['[FARM_1_increase_or_decrease_region]'] = increase_or_decrease_region
    return dt_find_replace

def farm_2(dt_find_replace, df_prod):
    year_min = 2002
    year_max = 2022
    prod_year_min_permanent = df_prod[df_prod['Farm Worker']=='Permanent'][f'Year {year_min}'].values[0]
    prod_year_min_seasonal  = df_prod[df_prod['Farm Worker']=='Seasonal' ][f'Year {year_min}'].values[0]
    prod_year_max_permanent = df_prod[df_prod['Farm Worker']=='Permanent'][f'Year {year_max}'].values[0]
    prod_year_max_seasonal  = df_prod[df_prod['Farm Worker']=='Seasonal' ][f'Year {year_max}'].values[0]
    if prod_year_max_permanent > prod_year_min_permanent:
        increased_or_decreased_permanent = 'increased'
    else:
        increased_or_decreased_permanent = 'decreased'
    if prod_year_max_seasonal > prod_year_min_seasonal:
        increased_or_decreased_seasonal = 'increased'
    else:
        increased_or_decreased_seasonal = 'decreased'
    dt_find_replace['[FARM_2_year_min]'] = year_min
    dt_find_replace['[FARM_2_year_max]'] = year_max
    dt_find_replace['[FARM_2_prod_year_min_permanent]'] = f'{prod_year_min_permanent:,.0f}'
    dt_find_replace['[FARM_2_prod_year_min_seasonal]' ] = f'{prod_year_min_seasonal:,.0f}'
    dt_find_replace['[FARM_2_prod_year_max_permanent]'] = f'{prod_year_max_permanent:,.0f}'
    dt_find_replace['[FARM_2_prod_year_max_seasonal]' ] = f'{prod_year_max_seasonal:,.0f}'
    dt_find_replace['[FARM_2_increased_or_decreased_permanent]'] = increased_or_decreased_permanent
    dt_find_replace['[FARM_2_increased_or_decreased_seasonal]' ] = increased_or_decreased_seasonal
    return dt_find_replace

def lgfem_1(dt_find_replace, df_pct):
    pct_5_plus_rent = df_pct[df_pct['Household Size']=='5 or more person household']['Renter occupied'].values[0]
    pct_5_plus_own  = df_pct[df_pct['Household Size']=='5 or more person household']['Owner occupied' ].values[0]
    dt_find_replace['[LGFEM_1_pct_5_plus_rent]'] = f'{pct_5_plus_rent:.1%}'
    dt_find_replace['[LGFEM_1_pct_5_plus_own]' ] = f'{pct_5_plus_own:.1%}'
    return dt_find_replace

def lgfem_2(dt_find_replace, df_pct, jurisdiction):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    pct_5_plus = df_pct[df_pct['Geography']==jurisdiction]['5 or more person households'].values[0]
    dt_find_replace['[LGFEM_2_pct_5_plus]'] = f'{pct_5_plus:.1%}'
    return dt_find_replace

def lgfem_3(dt_find_replace, df_pct):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Household Size')
    try:
        pct_large_family_below_50_ami = df_pct[df_pct['Household Size']=='Large family with 5+ persons']['0%-30% of AMI'].values[0] + df_pct[df_pct['Household Size']=='Large family with 5+ persons']['31%-50% of AMI'].values[0]; dt_find_replace['[LGFEM_3_pct_large_family_below_50_ami]'] = f'{pct_large_family_below_50_ami:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_large_family_below_50_ami=None
    return dt_find_replace

def lgfem_4(dt_find_replace, df_prod):
    pct_female_headed_family_household = df_prod[df_prod['Household Type']=='Female-headed family household'].sum(numeric_only=True).sum()/df_prod.sum(numeric_only=True).sum()
    dt_find_replace['[LGFEM_4_pct_female_headed_family_household]'] = f'{pct_female_headed_family_household:.1%}'
    return dt_find_replace

def lgfem_5(dt_find_replace, df_pct):
    try:
        pct_w_children_below_fpl = df_pct[df_pct['Family Status']=='Female-headed households with children']['Below poverty level'].values[0]; dt_find_replace['[LGFEM_5_pct_w_children_below_fpl]' ] = f'{pct_w_children_below_fpl:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_w_children_below_fpl=None
    try:
        pct_no_children_below_fpl = df_pct[df_pct['Family Status']=='Female-headed households without children']['Below poverty level'].values[0]; dt_find_replace['[LGFEM_5_pct_no_children_below_fpl]'] = f'{pct_no_children_below_fpl:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_no_children_below_fpl=None
    return dt_find_replace

def sen_1(dt_find_replace, df_pct):
    most_common_income_rent = df_pct[df_pct['Renter occupied'] == df_pct['Renter occupied'].max()]['Income Level'].values[0].replace('G', 'g')
    most_common_income_own  = df_pct[df_pct['Owner occupied' ] == df_pct['Owner occupied' ].max()]['Income Level'].values[0].replace('G', 'g')
    dt_find_replace['[SEN_1_most_common_income_rent]'] = most_common_income_rent
    dt_find_replace['[SEN_1_most_common_income_own]' ] = most_common_income_own
    return dt_find_replace

def sen_2(dt_find_replace, df_pct):
    df_pct  = df_pct .set_index(df_pct .columns[0]).T.reset_index(names='Age Group')
    pct_non_white_under_18 = 1-df_pct[df_pct['Age Group'] == 'Age 0-17']['White (NH)'].values[0]
    pct_non_white_over_65  = 1-df_pct[df_pct['Age Group'] == 'Age 65+' ]['White (NH)'].values[0]
    dt_find_replace['[SEN_2_pct_non_white_under_18]'] = f'{pct_non_white_under_18:.1%}'
    dt_find_replace['[SEN_2_pct_non_white_over_65]' ] = f'{pct_non_white_over_65:.1%}'
    return dt_find_replace

def sen_3(dt_find_replace, df_pct):
    try:
        pct_below_30_ami_50_plus = df_pct[df_pct['Income Level']=='0%-30% of AMI']['50%+ of income used for housing'  ].values[0]; dt_find_replace['[SEN_3_pct_below_30_ami_50_plus]'] = f'{pct_below_30_ami_50_plus:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_below_30_ami_50_plus=None
    try:
        pct_over_100_ami_less_than_30 = df_pct[df_pct['Income Level']=='Greater than 100% of AMI']['0%-30% of income used for housing'].values[0]; dt_find_replace['[SEN_3_pct_over_100_ami_less_than_30]'] = f'{pct_over_100_ami_less_than_30:.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        pct_over_100_ami_less_than_30=None
    return dt_find_replace

def disab_2(dt_find_replace, df_pct, jurisdiction):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    pct_disability = df_pct[df_pct['Geography']==jurisdiction]['With a disability'].values[0]
    dt_find_replace['[DISAB_2_pct_disability]'] = f'{pct_disability:.1%}'
    return dt_find_replace

def disab_4(dt_find_replace, df_prod):
    prod_under_18_pct = df_prod[df_prod['Age Group']=='Under 18']['Population'].values[0] / df_prod['Population'].sum()
    prod_over_18_pct  = df_prod[df_prod['Age Group']=='Over 18' ]['Population'].values[0] / df_prod['Population'].sum()
    dt_find_replace['[DISAB_4_prod_under_18_pct]'] = f'{prod_under_18_pct:.1%}'
    dt_find_replace['[DISAB_4_prod_over_18_pct]' ] = f'{prod_over_18_pct:.1%}'
    return dt_find_replace

def disab_5(dt_find_replace, df_prod):
    most_common_residence_type = df_prod[df_prod['Population'] == df_prod['Population'].max()]['Residence Type'].values[0]
    dt_find_replace['[DISAB_5_most_common_residence_type]'] = most_common_residence_type
    return dt_find_replace

def homels_1(dt_find_replace, df_prod):
    prod_most_common_household_type = df_prod.set_index('Household Type').sum(axis=1).reset_index().sort_values(0, ascending=False)['Household Type'].values[0]
    prod_most_common_shelter_w_children = df_prod[df_prod['Household Type']!='Persons in households without children'].drop('Unsheltered', axis=1).set_index('Household Type').sum().reset_index().sort_values(0, ascending=False)['index'].values[0]
    prod_most_common_shelter_w_children = prod_most_common_shelter_w_children.replace('Sheltered - ', '')
    df_prod = df_prod.set_index(df_prod.columns[0]).T.reset_index(names='Shelter Status')
    prod_no_children_unsheltered_pct = df_prod[df_prod['Shelter Status']=='Unsheltered']['Persons in households without children'].values[0]/df_prod['Persons in households without children'].sum()
    dt_find_replace['[HOMELS_1_prod_most_common_household_type]'] = prod_most_common_household_type
    dt_find_replace['[HOMELS_1_prod_most_common_shelter_w_children]'] = prod_most_common_shelter_w_children
    dt_find_replace['[HOMELS_1_prod_no_children_unsheltered_pct]'] = f'{prod_no_children_unsheltered_pct:.1%}'
    return dt_find_replace

def homels_2(dt_find_replace, df_prod, df_pct):
    prod_homeless = df_prod['Homeless Population'].sum()
    most_common_ethnicity_homeless = df_pct[df_pct['Homeless Population (%)'] == df_pct['Homeless Population (%)'].max()]['Race/Ethnicity'].values[0]
    pct_most_common_ethnicity_homeless = df_pct[df_pct['Race/Ethnicity']==most_common_ethnicity_homeless]['Homeless Population (%)'].values[0]
    pct_most_common_ethnicity_overall  = df_pct[df_pct['Race/Ethnicity']==most_common_ethnicity_homeless]['Overall Population (%)' ].values[0]
    dt_find_replace['[HOMELS_2_prod_homeless]'] = f'{prod_homeless:,.0f}'
    dt_find_replace['[HOMELS_2_most_common_ethnicity_homeless]'] = most_common_ethnicity_homeless
    dt_find_replace['[HOMELS_2_pct_most_common_ethnicity_homeless]'] = f'{pct_most_common_ethnicity_homeless:.1%}'
    dt_find_replace['[HOMELS_2_pct_most_common_ethnicity_overall]' ] = f'{pct_most_common_ethnicity_overall:.1%}'
    return dt_find_replace

def homels_3(dt_find_replace, df_prod):
    df_prod = df_prod.set_index(df_prod.columns[0]).T.reset_index(names='Shelter Status')
    prod_most_common_characteristic = df_prod.sum(axis=0, numeric_only=True).max()
    df_t = df_prod.sum(axis=0, numeric_only=True).reset_index().rename(columns={'index':'Characteristic', 0:'Population'})
    most_common_characteristic = df_t[df_t['Population']==prod_most_common_characteristic]['Characteristic'].values[0]
    prod_most_common_characteristic_unsheltered = df_prod[df_prod['Shelter Status'] == 'Unsheltered'][most_common_characteristic].values[0]
    prod_most_common_characteristic_unsheltered_pct = prod_most_common_characteristic_unsheltered/df_prod[[most_common_characteristic]].sum()[most_common_characteristic]
    dt_find_replace['[HOMELS_3_most_common_characteristic]'] = most_common_characteristic   
    dt_find_replace['[HOMELS_3_prod_most_common_characteristic]'] = f'{prod_most_common_characteristic:,.0f}'
    dt_find_replace['[HOMELS_3_prod_most_common_characteristic_unsheltered_pct]'] = f'{prod_most_common_characteristic_unsheltered_pct:.1%}'
    return dt_find_replace

def homels_4(dt_find_replace, df_prod, jurisdiction, county):
    year_min = '2020-2021'
    year_max = '2023-2024'
    prod_year_min = df_prod[df_prod['Geography']==jurisdiction]['2020-21'].values[0]
    prod_year_max = df_prod[df_prod['Geography']==jurisdiction]['2023-24'].values[0]
    try:
        prod_pct_diff = prod_year_max/prod_year_min-1
        dt_find_replace['[HOMELS_4_prod_pct_diff]'] = f'{abs(prod_pct_diff):.1%}'
    except Exception as e:
        print(f"How exceptional! {e}")
        prod_pct_diff=None
    if prod_pct_diff > 1:
        increased_or_decreased = 'increased'
    else:
        increased_or_decreased = 'decreased'
    if prod_pct_diff is None:
        increased_or_decreased=None
    prod_year_min_county = df_prod[df_prod['Geography']==f'{county} County']['2020-21'].values[0]
    prod_year_max_county = df_prod[df_prod['Geography']==f'{county} County']['2023-24'].values[0]
    prod_pct_diff_county = abs(prod_year_max_county/prod_year_min_county-1)
    if prod_pct_diff_county > 1:
        increase_or_decrease_county = 'increase'
    else:
        increase_or_decrease_county = 'decrease'
    prod_year_min_region = df_prod[df_prod['Geography']=='SACOG Region']['2020-21'].values[0]
    prod_year_max_region = df_prod[df_prod['Geography']=='SACOG Region']['2023-24'].values[0]
    prod_pct_diff_region = prod_year_max_region/prod_year_min_region-1
    if prod_pct_diff_region > 1:
        increased_or_decreased_region = 'increased'
    else:
        increased_or_decreased_region = 'decreased'
    prod_year_max_pct_of_county = prod_year_max/prod_year_max_county
    prod_year_max_pct_of_region = prod_year_max/prod_year_max_region
    dt_find_replace['[HOMELS_4_year_min]'] = year_min
    dt_find_replace['[HOMELS_4_year_max]'] = year_max
    dt_find_replace['[HOMELS_4_prod_year_min]'] = f'{prod_year_min:,.0f}'
    dt_find_replace['[HOMELS_4_prod_year_max]'] = f'{prod_year_max:,.0f}'
    dt_find_replace['[HOMELS_4_prod_year_max_region]'] = f'{prod_year_max_region:,.0f}'
    dt_find_replace['[HOMELS_4_prod_pct_diff_county]'] = f'{prod_pct_diff_county:.1%}'
    dt_find_replace['[HOMELS_4_prod_pct_diff_region]'] = f'{prod_pct_diff_region:.1%}'
    dt_find_replace['[HOMELS_4_increased_or_decreased]'       ] = increased_or_decreased
    dt_find_replace['[HOMELS_4_increase_or_decrease_county]'  ] = increase_or_decrease_county
    dt_find_replace['[HOMELS_4_increased_or_decreased_region]'] = increased_or_decreased_region
    dt_find_replace['[HOMELS_4_prod_year_max_pct_of_county]'] = f'{prod_year_max_pct_of_county:.1%}'
    dt_find_replace['[HOMELS_4_prod_year_max_pct_of_region]'] = f'{prod_year_max_pct_of_region:.1%}'
    return dt_find_replace

def eli_1(dt_find_replace, df_prod, df_pct, jurisdiction):
    df_prod = df_prod.set_index(df_prod.columns[0]).T.reset_index(names='Geography')
    df_pct  = df_pct .set_index(df_pct .columns[0]).T.reset_index(names='Geography')
    prod_more_than_100 = df_prod[df_prod['Geography']==jurisdiction]['Greater than 100% of AMI'].values[0]
    prod_less_than_30  = df_prod[df_prod['Geography']==jurisdiction]['0%-30% of AMI'           ].values[0]
    pct_more_than_100 = df_pct[df_pct['Geography']==jurisdiction]['Greater than 100% of AMI'].values[0]    
    dt_find_replace['[ELI_1_prod_more_than_100]'] = f'{prod_more_than_100:,.0f}'
    dt_find_replace['[ELI_1_prod_less_than_30]' ] = f'{prod_less_than_30:,.0f}'
    dt_find_replace['[ELI_1_pct_more_than_100]' ] = f'{pct_more_than_100:.1%}'
    return dt_find_replace

def eli_3(dt_find_replace, df_pct):
    most_common_ethnicity_below_fpl_1 = df_pct[df_pct['Below poverty level'] == df_pct['Below poverty level'].max()]['Race/Ethnicity'].values[0]
    df_pct_2 = df_pct[df_pct['Below poverty level'] != df_pct['Below poverty level'].max()]
    most_common_ethnicity_below_fpl_2 = df_pct_2[df_pct_2['Below poverty level'] == df_pct_2['Below poverty level'].max()]['Race/Ethnicity'].values[0]
    dt_find_replace['[ELI_3_most_common_ethnicity_below_fpl_1]'] = most_common_ethnicity_below_fpl_1
    dt_find_replace['[ELI_3_most_common_ethnicity_below_fpl_2]'] = most_common_ethnicity_below_fpl_2
    return dt_find_replace

def eli_4(dt_find_replace, df_pct):
    pct_less_than_15 = df_pct[df_pct['Income Bracket'] == 'Acutely low income']['Percent'].values[0]
    ami_county = int(''.join(re.findall(r'\d+', df_pct[df_pct['Income Bracket']=='High income']['Income Range'].values[0])))/1.2
    ami_county_30_pct = ami_county*0.3
    dt_find_replace['[ELI_4_pct_less_than_15]'] = f'{pct_less_than_15:.1%}'
    dt_find_replace['[ELI_4_ami_county]'       ] = f'${ami_county:,.0f}'
    dt_find_replace['[ELI_4_ami_county_30_pct]'] = f'${ami_county_30_pct:,.0f}'
    return dt_find_replace

def affh_2(dt_find_replace, df_prod):
    prod_high_pct = df_prod['High/Highest Resource'].sum() / df_prod.sum(numeric_only=True).sum()
    prod_low_pct  = df_prod['Low Resource'         ].sum() / df_prod.sum(numeric_only=True).sum()
    dt_find_replace['[AFFH_2_prod_high_pct]'] = f'{prod_high_pct:.1%}'
    dt_find_replace['[AFFH_2_prod_low_pct]' ] = f'{prod_low_pct:.1%}'
    return dt_find_replace

def affh_3(dt_find_replace, df_pct, jurisdiction):
    df_pct = df_pct.set_index(df_pct.columns[0]).T.reset_index(names='Geography')
    pct_limited_english        = df_pct[df_pct['Geography']==jurisdiction  ]['Population 5 years and over who speak english "not well" or "not at all"'].values[0]
    pct_limited_english_region = df_pct[df_pct['Geography']=='SACOG Region']['Population 5 years and over who speak english "not well" or "not at all"'].values[0]
    if pct_limited_english > pct_limited_english_region:
        above_or_below = 'above'
    else:
        above_or_below = 'below'
    dt_find_replace['[AFFH_3_pct_limited_english]'       ] = f'{pct_limited_english:.1%}'
    dt_find_replace['[AFFH_3_pct_limited_english_region]'] = f'{pct_limited_english_region:.1%}'
    dt_find_replace['[AFFH_3_above_or_below]'] = above_or_below
    return dt_find_replace




