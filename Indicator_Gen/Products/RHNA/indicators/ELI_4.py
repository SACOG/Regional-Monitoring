

'''
Methodology:

(1) Collect the latest HCD AMI data by county and by household size (https://www.hcd.ca.gov/funding/income-limits/state-federal-income-limits/state)
(2) Collect ACS data on the number of households per household income range (U.S. Census Bureau, American Community Survey 5-Year Data, Data Profile, Table DP03)


(3) Using the HCD AMI data for each county, estimate the income ranges that equate to 0-15% of AMI, 15-30% of AMI, 30-50% of AMI, 50-80% of AMI, 80-120% of AMI, and 120%+ of AMI

For instance, Sacramento County AMI in 2024 was $113,900, so the breakout for every was:

0.15*113900 = 17085, 0.30*113900 = 34170, ..., 1.20*113900 = 136680

This results in the following income ranges for Sacramento County:

           Income Bracket                    Income Range
  Acutely low income ( 0-15% of AMI)     Less than $17,085
Extremely low income (15-30% of AMI)       $17,085-$34,170
     Very low income (30-50% of AMI)       $34,170-$56,950
        Lower income (50-80% of AMI)       $56,950-$91,120
     Moderate income (80-120% of AMI)      $91,120-$136,680
         High income (  >120% of AMI)   $136,680 or greater


(4) Estimate the number of households in each HCD income bracket, while assuming households are uniformly distributed through an income range.

For example, in Sacramento County where Folsom has the following distribution of households (ACS):

        Folsom         Households
   Less than $10,000       827.0
  $10,000 to $14,999       404.0
  $15,000 to $24,999      1118.0
  $25,000 to $34,999      1210.0
  $35,000 to $49,999      1430.0
  $50,000 to $74,999      2269.0
  $75,000 to $99,999      3235.0
$100,000 to $149,999      5300.0
$150,000 to $199,999      3818.0
    $200,000 or more     10352.0

The HCD income bracket "acutely low income (0-15% of AMI)" is "less than $17,085" for Sacramento County.

So we have 827 + 404 + 1118 *((17085-15000) / (24999-15000)) = 1464 households.

Because $17,085 is inbetween $15,000 to $24,999 we break up that household count
Continuing this formula, we get:

      Income Bracket         Income Range   Folsom  Sacramento County  SACOG Region
  Acutely low income    Less than $17,085   1464.0            49138.0       78657.0
Extremely low income      $17,085-$34,170   1995.0            50404.0       82482.0
     Very low income      $34,170-$56,950   2161.0            74675.0      117868.0
        Lower income      $56,950-$91,120   3724.0           107721.0      170781.0
     Moderate income     $91,120-$136,680   5037.0           108917.0      175472.0
         High income  $136,680 or greater  15582.0           180202.0      318556.0

'''


import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
import warnings
warnings.filterwarnings("ignore")

yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_INCOME = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data') / 'Income_1 Counties ACS5.xlsx'
FILE_HCD_AMI = Path(__file__).parent.parent.parent.parent/'config'/'CA_state_income_brackets_by_household_size.xlsx'



def clean_hcd_ami(df):

        df['County'] = df['County'].ffill()
        df['County'] = df['County'].str.replace(' County.*'         , '' , regex = True)
        df['County'] = df['County'].str.replace('\n'                , ' ', regex = True)
        df['AMI'   ] = df['County'].str.extract('\$?([0-9,]+)[.%]?')
        df['AMI'   ] = df['AMI'   ].str.replace(','                 , '' , regex = True)
        df['County'] = df['County'].str.replace(' \$?([0-9,]+)[.%]?', '' , regex = True)
        df = pd.melt(df, id_vars = ['County', 'Income Bracket', 'AMI'], var_name='NP', value_name='Income Threshold')
        df = df[df['Income Bracket'].isin(['Median Income'])]
        df = df.pivot_table(index = ['County', 'NP'], columns='Income Bracket', values='Income Threshold').reset_index().rename(columns={'County':'County Name'})

        return df



def org_ami(df):

    df = df[['Geography', 'Variable', 'Households']]

    conditions = [
        df['Variable'] == 'Less than $10,000'
        , df['Variable'] == '$10,000 to $14,999'
        , df['Variable'] == '$15,000 to $24,999'
        , df['Variable'] == '$25,000 to $34,999'
        , df['Variable'] == '$35,000 to $49,999'
        , df['Variable'] == '$50,000 to $74,999'
        , df['Variable'] == '$75,000 to $99,999'
        , df['Variable'] == '$100,000 to $149,999'
        , df['Variable'] == '$150,000 to $199,999'
        , df['Variable'] == '$200,000 or more'
    ]

    choices = ['0_9999', '10000_14999', '15000_24999', '25000_34999', '35000_49999', '50000_74999', '75000_99999', '100000_149999', '150000_199999', '200000_999999']
    df['bounds'] = np.select(conditions, choices, default='0')

    return df


def proc_ami(df, geo, hh_bracket_acs, dt_hcd_brackets, hh_bracket_hcd, list_df_sub):
    
    df_sub = df.copy()
    df_sub = df_sub[(df_sub['Geography']==geo) & (df_sub['Variable'] == hh_bracket_acs)]

    hh_sub = df_sub['Households'].values[0]

    low_acs = int(df_sub['bounds'].str.split('_').values[0][0])
    hi_acs  = int(df_sub['bounds'].str.split('_').values[0][1])

    low_hcd = dt_hcd_brackets[hh_bracket_hcd][0]
    hi_hcd  = dt_hcd_brackets[hh_bracket_hcd][1]

    if hi_hcd < hi_acs:
        if hi_hcd > low_acs:
            hh_sub = ((hi_hcd-low_acs)/(hi_acs-low_acs))*hh_sub
        else: 
            hh_sub = 0

    if low_hcd > low_acs:
        if low_hcd < hi_acs:
            hh_sub = ((hi_acs-low_hcd)/(hi_acs-low_acs))*hh_sub 
        else:
            hh_sub = 0

    if low_hcd > hi_acs:
        hh_sub = 0

    if hh_bracket_acs == '$200,000 or more' and hh_bracket_hcd == 'High income: >120 pct of AMI':
        hh_sub = df_sub['Households'].values[0]

    if hh_sub > 0:
        df_sub['HCD_var'] = hh_bracket_hcd
        df_sub['HH_adj' ] = round(hh_sub)
        df_sub['HCD_brack'] = str(dt_hcd_brackets[hh_bracket_hcd])
        list_df_sub.append(df_sub)
       
    return list_df_sub

## TODO:
# Need to figure out how to best apply HCD income scalars to each geography separately, right now all being assigned the same number of households

if __name__ == '__main__':

    COUNTY_AMI=False
    HCD_AMI=True

    df_places, df_counties, df_mpo = rhna.acs_import(INDICATOR)
    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)

    df_places   = df_places  [df_places  ['Year'] == df_places  ['Year'].max()]
    df_counties = df_counties[df_counties['Year'] == df_counties['Year'].max()]
    df_mpo      = df_mpo     [df_mpo     ['Year'] == df_mpo     ['Year'].max()]

    df_places = df_places.rename(columns={'NAME':'Geography', 'Race_Ethnicity':'Race/Ethnicity'})
    df_counties = df_counties.rename(columns={'County Name':'Geography', 'Race_Ethnicity':'Race/Ethnicity'})
    df_mpo      = df_mpo     .rename(columns={'MPO' :'Geography', 'Race_Ethnicity':'Race/Ethnicity'})
    df_mpo['Geography']='SACOG Region'
    df_counties['Geography'] = df_counties['Geography']+' County'
    
    df_places   = df_places  [['County Name', 'Geography', 'Variable', 'Households']].drop_duplicates()
    df_counties = df_counties[[               'Geography', 'Variable', 'Households']].drop_duplicates()
    df_mpo      = df_mpo     [[               'Geography', 'Variable', 'Households']].drop_duplicates()
    counties = list(df_counties['Geography'].unique())

    if COUNTY_AMI:
        df_counties_ami = pd.read_excel(FILE_INCOME, sheet_name='Counties')
        df_counties_ami = df_counties_ami[df_counties_ami['Race/Ethnicity'] == 'All']
        df_counties_ami = df_counties_ami[df_counties_ami['Year'] == df_counties_ami['Year'].max()]

    if HCD_AMI:
        df_counties_ami = pd.read_excel(FILE_HCD_AMI, sheet_name='Table')
        df_counties_ami = clean_hcd_ami(df_counties_ami)
        df_counties_ami = df_counties_ami[(df_counties_ami['NP']==4) & (df_counties_ami['County Name'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']))]
        df_counties_ami = df_counties_ami.drop('NP', axis=1)
        df_counties_ami = df_counties_ami.rename(columns={'Median Income':'Median Household Income'})


    for county in counties:

        df_ami = df_counties_ami[df_counties_ami['County Name'] == county.replace(' County', '')]
        ami = df_ami['Median Household Income'].values[0]

        dt_hcd_brackets = {
            'Acutely low income: 0-15 pct of AMI': [0, ami*0.15]
            , 'Extremely low income: 15-30 pct of AMI': [ami*0.15, ami*0.3]
            , 'Very low income: 30-50 pct of AMI': [ami*0.3, ami*0.5]
            , 'Lower income: 50-80 pct of AMI': [ami*0.5, ami*0.8]
            , 'Moderate income: 80 to 120 pct of AMI': [ami*0.8, ami*1.2]
            , 'High income: >120 pct of AMI': [ami*1.2, ami*10]
        }

        dt_hcd_brackets_clean = {
            'Acutely low income: 0-15 pct of AMI': f'Less than ${ami*0.15:,.0f}'
            , 'Extremely low income: 15-30 pct of AMI': f'${ami*0.15:,.0f}-${ami*0.3:,.0f}'
            , 'Very low income: 30-50 pct of AMI': f'${ami*0.3:,.0f}-${ami*0.5:,.0f}'
            , 'Lower income: 50-80 pct of AMI': f'${ami*0.5:,.0f}-${ami*0.8:,.0f}'
            , 'Moderate income: 80 to 120 pct of AMI': f'${ami*0.8:,.0f}-${ami*1.2:,.0f}'
            , 'High income: >120 pct of AMI': f'${ami*1.2:,.0f} or greater'
        }

        print('\n'*2)
        print(county)

        print('County AMI: ', ami)
        display(dt_hcd_brackets)
        time.sleep(2)

        df_counties_sub = df_counties[df_counties['Geography']==county]
        df_places_sub   = df_places  [df_places  ['County Name']==county.replace(' County', '')].drop('County Name', axis=1)
        jurisdictions = df_places_sub['Geography'].unique()

        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df = pd.concat([df_places_sub[df_places_sub['Geography'] == jurisdiction], df_counties_sub, df_mpo])
            df = org_ami(df)

            list_brackets_acs = list(df['Variable'].unique())
            list_brackets_hcd = list(dt_hcd_brackets.keys())

            geographies = df['Geography'].unique()
            list_df_var_places = []

            for geo in geographies:
                for hh_bracket_acs in list_brackets_acs:
                    list_df_sub_places = []
                    for hh_bracket_hcd in list_brackets_hcd:
                        list_df_sub_places = proc_ami(df, geo, hh_bracket_acs, dt_hcd_brackets, hh_bracket_hcd, list_df_sub_places)
                    if not list_df_sub_places:
                        print('no df_sub')
                    else:
                        df_sub_places_all = pd.concat(list_df_sub_places)
                        list_df_var_places.append(df_sub_places_all)

            df2 = pd.concat(list_df_var_places)
            df2['HCD_brack_clean'] = df2['HCD_var'].map(dt_hcd_brackets_clean)

            if round(df['Households'].sum()) != round(df2['HH_adj'].sum()):
                tqdm.write(f'Something wrong - Before: {df['Households'].sum()}, After: {df2['HH_adj'].sum()}')
            df = df2.groupby(['Geography', 'HCD_var', 'HCD_brack_clean'], as_index=False).agg(HH_adj=('HH_adj', 'sum'))

            df['Percent'] = df['HH_adj'] / df.groupby(['Geography'])['HH_adj'].transform('sum')

            conditions = [
                        df['HCD_var'] == 'Acutely low income: 0-15 pct of AMI',
                        df['HCD_var'] == 'Extremely low income: 15-30 pct of AMI',
                        df['HCD_var'] == 'Very low income: 30-50 pct of AMI',
                        df['HCD_var'] == 'Lower income: 50-80 pct of AMI',
                        df['HCD_var'] == 'Moderate income: 80 to 120 pct of AMI',
                        df['HCD_var'] == 'High income: >120 pct of AMI'
                        ]
            choices = ['Acutely low income', 'Extremely low income', 'Very low income', 'Lower income', 'Moderate income', 'High income']
            df['HCD_var'] = np.select(conditions, choices, default='no')

            df = df.rename(columns={'HCD_var':'Income Bracket', 'HCD_brack_clean':'Income Range', 'HH_adj':'Households'})

            df_prod = df.pivot_table(index=['Income Bracket', 'Income Range'], columns='Geography', values='Households').reset_index()
            df_pct  = df.pivot_table(index=['Income Bracket', 'Income Range'], columns='Geography', values='Percent'   ).reset_index()

            df_prod = df_prod[['Income Bracket', 'Income Range', jurisdiction, county, 'SACOG Region']]
            df_pct  = df_pct [['Income Bracket', 'Income Range', jurisdiction, county, 'SACOG Region']]    
            
            sort_hcd = ['Acutely low income', 'Extremely low income', 'Very low income', 'Lower income', 'Moderate income', 'High income']
            df_prod['sort'] = pd.Categorical(df_prod['Income Bracket'], sort_hcd)
            df_pct ['sort'] = pd.Categorical(df_pct ['Income Bracket'], sort_hcd)
            df_prod = df_prod.sort_values(['sort'], ascending=True).drop(['sort'], axis=1)
            df_pct  = df_pct .sort_values(['sort'], ascending=True).drop(['sort'], axis=1)
            if jurisdiction=='Folsom':
                breakpoint()
            df_plot = df.copy()
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)


