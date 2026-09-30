

'''

From Copilot:
Real GDP in chained dollars is not additive across geographies, and therefore summed values should not be interpreted
as true aggregate levels. However, BEA guidance indicates that chained-dollar estimates correctly measure growth rates,
and percent changes are equivalent to quantity index growth. For this reason, county-level real GDP (chained dollars)
was aggregated to the MSA level by summing across counties for each year to construct a time series, from which average
annual growth rates were calculated. While this approach introduces minor aggregation error, BEA notes that such errors
are generally small for broad aggregates

Sources:
https://www.bea.gov/resources/methodologies/chained-dollar-indexes
https://www.bea.gov/sites/default/files/2026-02/geo-aggregator-technical-document.pdf

My interpretation:
Summing Real GDP in chained-dollars is not okay to get an "economically meaningful" result
BUT we are summing Real GDP in chained-dollars to calculate a growth rate, which is fine (or very close to fine)
I don't know if this is accurate or not, though Copilot did provide some sources
Pretty hard to validate, but my results are pretty dang similar to last years using this approach so it is probably fine

The reason I have to use this approach now is because the BEA stopped collecting Real GDP in chained-dollars estimates at the MSA level
So now, I am using county level data and rolling up to the MSA level

'''


import numpy as np
import pandas as pd
from pathlib import Path
import plotly.express as px
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'config'))
import functions as func
import plot as pt

pd.set_option('display.max_columns', None)


# SharePoint OneDrive paths
PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_BEA = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\BEA\CAGDP9')
FILE_AREA = Path(__file__).parent.parent.parent/'config'/'area_codes.xlsx'





# Main ----------------------------------------------------------------------------------------------------------------------


YEAR=2024
EXPORT=False


if __name__=='__main__':

    df_county = pd.read_excel(FILE_AREA, sheet_name='CountyFIPS', dtype={'STATEFP':str, 'COUNTYFP':str, 'MSA_ID':str})
    df_msa    = pd.read_excel(FILE_AREA, sheet_name='MSAcodes'  , dtype={'MSA_ID':str})
    df_msa = df_msa[df_msa['Year']==YEAR][['MSA_ID', 'Abbrv']].drop_duplicates()
    df_area = df_county.merge(df_msa, on='MSA_ID', how='left')
    df_area = df_area[df_area['Peer MSA']=='Yes'].reset_index(drop=True)
    df_area = df_area[['STATEFP', 'STATE', 'COUNTYFP', 'COUNTYNAME', 'Abbrv', 'MSA_ID']].rename(columns={'MSA_ID':'MSA ID', 'Abbrv':'MSA'})
    df_area['STATEFP'] = df_area['STATEFP'].astype(str)
    df_area['COUNTYFP'] = df_area['COUNTYFP'].astype(str)
    states = df_area['STATE'].unique()

    list_df_states=[]
    for state in states:
        file_in = PATH_BEA / f'CAGDP9_{state}_2001_{YEAR}.csv'
        df_rdp = pd.read_csv(file_in, na_values="(D)")
        df_rdp.columns = df_rdp.columns.str.strip()
        list_df_states.append(df_rdp)
    df_rdp = pd.concat(list_df_states).reset_index(drop=True)

    # Filtering and selecting columns
    df_rdp = df_rdp[df_rdp['LineCode'] < 87]
    df_rdp = df_rdp.dropna(subset=['GeoName'])
    df_rdp = df_rdp[df_rdp['Description'] != 'Addenda:']

    # Replacing parts of GeoName
    df_rdp['GeoFIPS'] = df_rdp['GeoFIPS'].str.replace('"', '')
    df_rdp['GeoName'] = df_rdp['GeoName'].str.strip()
    df_rdp['GeoName'] = df_rdp['GeoName'].str.replace(r"\(.*", "", regex=True)
    df_rdp['GeoFIPS'] = df_rdp['GeoFIPS'].str.strip()
    df_rdp['Description'] = df_rdp['Description'].str.strip()

    df_rdp['STATEFP' ] = df_rdp['GeoFIPS'].str[:2].astype(str)
    df_rdp['COUNTYFP'] = df_rdp['GeoFIPS'].str[2:].astype(str)

    df_rdp = df_rdp.merge(df_area, on=['STATEFP', 'COUNTYFP'], how='left')
    df_rdp = df_rdp.dropna(subset=['COUNTYNAME'])

    msa_peers = [
        'Sacramento, CA'
        , 'Yuba City, CA'
        , 'Austin, TX'
        , 'Charlotte, NC'
        , 'Cincinnati, OH'
        , 'Cleveland, OH'
        , 'Columbus, OH'
        , 'Detroit, MI'
        , 'Indianapolis, IN'
        , 'Miami, FL'
        , 'Orlando, FL'
        , 'Phoenix, AZ'
        , 'Portland, OR'
        , 'Riverside, CA'
        , 'Salt Lake City, UT'
        , 'San Antonio, TX'
        , 'St. Louis, MO'
        , 'Tampa, FL'
    ]

    # df_rdp['GeoName'] = df_rdp['GeoName'].map(pt.peer_msa_labels)
    df_rdp = df_rdp[df_rdp['Description'] == 'All industry total']
    df_rdp = df_rdp[df_rdp['MSA'].isin(msa_peers)].reset_index(drop=True)
    df_rdp = df_rdp.drop(['Region', 'GeoFIPS', 'IndustryClassification', 'TableName', 'LineCode', 'Unit', 'GeoName', 'STATEFP', 'COUNTYFP', 'STATE', 'COUNTYNAME', 'Description'], axis=1)

    df_rdp = pd.melt(df_rdp, id_vars=['MSA ID', 'MSA'], var_name='Year', value_name='GRP (Thousands of Dollars)')

    df_rdp['Year'  ] = df_rdp['Year'  ].astype(int)
    df_rdp['MSA ID'] = df_rdp['MSA ID'].astype(int)

    df_rdp = df_rdp.groupby(['MSA ID', 'MSA', 'Year'], as_index=False)['GRP (Thousands of Dollars)'].sum()
    df_rdp = df_rdp.sort_values(['MSA ID', 'Year'], ascending=[True, True]).reset_index(drop=True)

    df_rdp['AnnualPctDiff'] = df_rdp['GRP (Thousands of Dollars)'].pct_change()
    df_rdp.loc[df_rdp['Year'] == 2001, 'AnnualPctDiff'] = np.nan
    df_rdp.loc[df_rdp['AnnualPctDiff'] == np.inf, 'AnnualPctDiff'] = np.nan

    year_max = np.max(df_rdp['Year'].unique())
    year_min = np.min(df_rdp['Year'].unique())

    col_pct_change = f'PctChange_{year_min}_{year_max}'
    col_annual_pct_change = f'AnnualPctDiff_{year_min}_{year_max}'

    df_rdp2 = df_rdp.copy()
    df_rdp2 = df_rdp2[(df_rdp2['Year'] == year_max) | (df_rdp2['Year'] == year_min)]
    df_rdp2 = df_rdp2.drop('AnnualPctDiff', axis = 1)
    df_rdp2[col_pct_change] = df_rdp2['GRP (Thousands of Dollars)'].pct_change()
    df_rdp2.loc[df_rdp2['Year'] == year_min, col_pct_change] = np.nan
    df_rdp2.loc[df_rdp2[col_pct_change] == np.inf, col_pct_change] = np.nan
    df_rdp2 = df_rdp2[df_rdp2['Year'] == year_max]
    df_rdp2 = df_rdp2.drop(['Year', 'GRP (Thousands of Dollars)'], axis=1)

    df_rdp3 = df_rdp.copy()
    df_rdp3 = df_rdp3.groupby(['MSA'], as_index=False).agg(weighted_mean_grp = ('AnnualPctDiff', 'mean'))
    df_rdp3 = df_rdp3.rename(columns={'weighted_mean_grp':col_annual_pct_change})

    df_rdp2 = df_rdp2.merge(df_rdp3, on='MSA')

    df_rdp   = df_rdp.sort_values(['MSA', 'Year'], ascending=[True, False]).reset_index(drop=True)
    df_rdp2 = df_rdp2.sort_values([col_annual_pct_change], ascending=[False]).reset_index(drop=True)
    df_rdp = df_rdp.drop('GRP (Thousands of Dollars)', axis=1)

    display(df_rdp.head())
    display(df_rdp2.head())

    fig = px.line(df_rdp, x = 'Year', y = 'AnnualPctDiff', color = 'MSA', markers=True)
    fig.update_xaxes(tick0=0, dtick=1, range=[year_min-0.5, year_max+0.5])
    fig.update_traces(hovertemplate='%{y}')
    fig.show()


    if EXPORT:

        sample_type = 'BEA'
        indicator = 'Output_1'
        year_start = int(year_min)
        year_end = int(year_max)
        geography = 'MSA'

        params = {
            'sample':sample_type
            , 'indicator': indicator
            , 'start_year': year_start
            , 'end_year': year_end
            , 'geo': geography
            , 'estimate': None
            , 'moe_thresh': None
        }

        # Create about documentation page for export
        df_about = func.write_about(params)

        print("Visual representation of the output for:", indicator)
        display(df_about)

        path_out = PATH_SP / 'Data' / 'Vibrant and Inclusive Places' / 'Economy' / 'Jobs' / 'Output_1 GRP'
        path_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
        paths = [path_out, path_server]

        for path_ in paths:

            file_ = path_ / 'Output_1 MSA BEA.xlsx'
            with pd.ExcelWriter(file_, engine='openpyxl') as writer:
                df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                df_rdp  .to_excel(writer, index=False, sheet_name='Annual' )
                df_rdp2 .to_excel(writer, index=False, sheet_name='Average')

        print()
        print("Successfully exported!")
        print()


