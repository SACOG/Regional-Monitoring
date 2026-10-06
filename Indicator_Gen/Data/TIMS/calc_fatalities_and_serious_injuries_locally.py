

# TIMS does not have an API available.  Data can be manually downloaded from here https://tims.berkeley.edu/ and stored on SharePoint
# OR even better
# Just wait for Craig to update the Collisions data on the SDE and run this script


import numpy as np
import pandas as pd
from pathlib import Path
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'config' / 'tools'))
import sde
sys.path.append(str(Path(__file__).parent.parent.parent / 'config'))
import functions as func
pd.set_option('display.max_columns', None)


def import_collisions(sql_query):

    print('\n\nImporting regional collisions file...')

    gdf_col = sde.sqlqry_to_gdf(sql_query)
    gdf_col = gdf_col[
                        (gdf_col['SACOG']=='Yes')
                    ]

    print('Collisions Table: ')
    display(gdf_col)
    print('\n'*2)

    return gdf_col


def collision_rollup(gdf_col, geos):

    if geos == ['STATEWIDE']:
        path_tims = r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\TIMS'
        df_f = pd.read_csv(Path(path_tims)/'fatalities_CA.csv')
        df_f = df_f.rename(columns={'No. of Fatalities ':'Fatalities', 'Category':'Year'})
        df_s = pd.read_csv(Path(path_tims)/'serious-injuries_CA.csv')
        df_s = df_s.rename(columns={'No. of Serious Injuries ':'Serious injuries', 'Category':'Year'})
        df = df_f[['Year', 'Fatalities']].merge(df_s[['Year', 'Serious injuries']], on='Year')
        df = df.dropna()
        df['STATEWIDE']='CA'
        df_nm_f = pd.read_csv(Path(path_tims)/'non-motorized-fatalities_CA.csv')
        df_nm_f = df_nm_f.rename(columns={'No. of  Fatalities ':'Fatalities', 'Category':'Year'})
        df_nm_s = pd.read_csv(Path(path_tims)/'non-motorized-serious-in.csv')
        df_nm_s = df_nm_s.rename(columns={'No. of  Serious Injuries ':'Serious injuries', 'Category':'Year'})
        df_nm = df_nm_f[['Year', 'Fatalities']].merge(df_nm_s[['Year', 'Serious injuries']], on='Year')
        df_nm = df_nm.dropna()
        df_nm['STATEWIDE']='CA'

    else:
            
        if geos == ['REGION']:
            gdf_col['REGION']='SACOG'
            geos=['REGION']

        gdf_col = gdf_col.rename(columns={'ACCIDENT_YEAR':'Year'})
        groupby_cols=geos+['Year']

        df = (
            gdf_col
                    .groupby(groupby_cols, as_index=False)
                    .agg(num_fatalities=('NUMBER_KILLED', 'sum'), num_serious_inj=('COUNT_SEVERE_INJ', 'sum'))
                    # .pivot_table(index=groupby_cols, columns='ColSeverity', values=[num_fatalities])
                    .reset_index()
                    .fillna(0)
                    .rename(columns={'num_fatalities':'Fatalities', 'num_serious_inj':'Serious injuries'})
            )
        breakpoint()
        df_nm = (
            gdf_col[gdf_col['BikePed'].isin(['Bike', 'Ped'])]
                    .groupby(groupby_cols, as_index=False)
                    .agg(num_fatalities=('NUMBER_KILLED', 'sum'), num_serious_inj=('COUNT_SEVERE_INJ', 'sum'))
                    # .pivot_table(index=groupby_cols, columns='ColSeverity', values=[num_fatalities])
                    .reset_index()
                    .fillna(0)
                    .rename(columns={'num_fatalities':'Fatalities', 'num_serious_inj':'Serious injuries'})
            )
        
    return df, df_nm


def tidy_vmt(path_vmt, geos):

    '''
    Function to reshape the wide format of the VMT_3 pdf report analyzer output
    '''

    def clean_vmt_tables(df_vmt, geos):

        if geos == ['STATEWIDE']:
            path_vmt = r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\HPMS'
            df_vmt = pd.read_excel(Path(path_vmt)/'VMT_3 HPMS_Statewide.xlsx', sheet_name='VMT')
            df_vmt = (
                        df_vmt[df_vmt['Jurisdiction']=='Statewide total']
                            .drop('Jurisdiction', axis=1)
                            .rename(columns={'Total AVMT (in millions)':'annual_vmt'})
                    )
            df_vmt['STATEWIDE']='CA'
            df_vmt['annual_vmt'] = df_vmt['annual_vmt'] * 1000000

        else:
            # JURIS = ['Unincorporated',
            #             'El Dorado County', 'Placerville',
            #             'Placer County', 'Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville',
            #             'Sacramento County', 'Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento',
            #             'Sutter County', 'Yuba City', 'Live Oak',
            #             'Yolo County', 'Davis', 'West Sacramento', 'Winters', 'Woodland',
            #             'Yuba County', 'Marysville', 'Wheatland',
            #             'State Highways', 'State Park Service', 'University Of California']
            # df_vmt = df_vmt[df_vmt['JURISDICTION'].isin(JURIS)]
            df_vmt['CITY'] = df_vmt['JURISDICTION'].str.upper()
            df_vmt.loc[df_vmt['CITY'].str.contains('COUNTY'), 'CITY'] = 'UNINCORPORATED'
            df_vmt['annual_vmt'] = df_vmt['Daily VMT (1000s)'] * 365 * 1000
        
            if geos == ['REGION']:
                df_vmt['REGION']='SACOG'

        return df_vmt
    

    sheet_name = "Jurisdiction (Table 6)"
    df = pd.read_excel(path_vmt, sheet_name=sheet_name, header=None, engine="openpyxl")

    year_header_row = 2
    metric_header_row = 3
    data_start_row = 4

    years = df.iloc[year_header_row].ffill()
    metrics = df.iloc[metric_header_row]

    df_cols = pd.DataFrame(data={'years': years, 'metrics': metrics})
    df_cols['new_cols'] = df_cols['years'].astype(str) + '|' + df_cols['metrics'].fillna('0').astype(str)
    df_cols['new_cols'] = df_cols['new_cols'].str.replace('|0', '')
    new_cols = df_cols['new_cols'].tolist()

    df_wide = df.iloc[data_start_row:].copy()
    df_wide.columns = new_cols
    df_wide = df_wide.loc[:, ~df_wide.columns.astype(str).str.startswith("drop_")]

    other_agencies_mask = df_wide["COUNTY"].astype(str).str.strip().eq("Other Agencies")

    if not other_agencies_mask.any():
        raise ValueError("Could not find the 'Other Agencies' marker row.")

    other_agencies_marker_idx = df_wide.index[other_agencies_mask][0]
    df_wide["Agency Type"] = np.where(df_wide.index > other_agencies_marker_idx, "Other Agency", "Main Jurisdiction")

    df_wide = df_wide.loc[~other_agencies_mask].copy()
    df_wide = df_wide.dropna(subset=["COUNTY", "JURISDICTION"], how="all")
    df_wide["COUNTY"      ] = df_wide["COUNTY"      ].astype(str).str.strip()
    df_wide["JURISDICTION"] = df_wide["JURISDICTION"].astype(str).str.strip()

    df_long = df_wide.melt(id_vars=["Agency Type", "COUNTY", "JURISDICTION"], var_name="Year_Metric", value_name="value")
    df_long[["Year", "Metric"]] = df_long["Year_Metric"].str.split("|", expand=True)
    df_long["Year"] = df_long["Year"].astype(int)

    df_tidy = (
        df_long
        .pivot_table(index=["Agency Type", "COUNTY", "JURISDICTION", "Year"], columns="Metric", values="value", aggfunc="first")
        .reset_index()
    )

    df_tidy.columns.name = None
    desired_cols = ["Agency Type", "COUNTY", "JURISDICTION", "Year", "Maintained Miles", "Daily VMT (1000s)"]
    df_tidy = df_tidy[desired_cols]

    df_tidy["Maintained Miles" ] = pd.to_numeric(df_tidy["Maintained Miles" ], errors="coerce")
    df_tidy["Daily VMT (1000s)"] = pd.to_numeric(df_tidy["Daily VMT (1000s)"], errors="coerce")

    df_tidy = df_tidy.dropna(subset=["Maintained Miles", "Daily VMT (1000s)"], how="all")
    df_tidy = df_tidy.sort_values(["Agency Type", "COUNTY", "JURISDICTION", "Year"], kind="stable").reset_index(drop=True)

    display(df_tidy.head())
    print(df_tidy.shape)
    print(df_tidy["Agency Type"].value_counts(dropna=False))

    df_vmt = clean_vmt_tables(df_tidy, geos)

    return df_vmt


def safety_indicators_rollup(gdf_col, geos):
    
    df, df_nm = collision_rollup(gdf_col, geos)

    path_vmt = PATH_SERVER/"VMT_3 HPMS.xlsx"
    df_vmt = tidy_vmt(path_vmt, geos)

    groupby_cols = geos+['Year']

    df_vmt = df_vmt.groupby(groupby_cols, as_index=False).agg(annual_vmt=('annual_vmt', 'sum'))
    df = df.merge(df_vmt, how='left')

    df['Fatalities_100 mvmt'      ] = df['Fatalities'      ] / df['annual_vmt'] * 100000000
    df['Serious injuries_100 mvmt'] = df['Serious injuries'] / df['annual_vmt'] * 100000000
    df = df.drop('annual_vmt', axis=1)

    df    = df   .sort_values(groupby_cols, ascending=[col in groupby_cols for col in groupby_cols])
    df_nm = df_nm.sort_values(groupby_cols, ascending=[col in groupby_cols for col in groupby_cols])

    df   ['Fatalities_5 Year Rolling Average'      ] = df   .groupby(geos)['Fatalities'      ].transform(lambda x: x.rolling(window=5).mean())
    df   ['Serious injuries_5 Year Rolling Average'] = df   .groupby(geos)['Serious injuries'].transform(lambda x: x.rolling(window=5).mean())
    df_nm['Fatalities_5 Year Rolling Average'      ] = df_nm.groupby(geos)['Fatalities'      ].transform(lambda x: x.rolling(window=5).mean())
    df_nm['Serious injuries_5 Year Rolling Average'] = df_nm.groupby(geos)['Serious injuries'].transform(lambda x: x.rolling(window=5).mean())
    
    df['Fatalities_100 mvmt_5 Year Rolling Average'      ] = df.groupby(geos)['Fatalities_100 mvmt'      ].transform(lambda x: x.rolling(window=5).mean())
    df['Serious injuries_100 mvmt_5 Year Rolling Average'] = df.groupby(geos)['Serious injuries_100 mvmt'].transform(lambda x: x.rolling(window=5).mean())

    df = df[geos+['Year']+['Fatalities', 'Fatalities_5 Year Rolling Average', 'Fatalities_100 mvmt', 'Fatalities_100 mvmt_5 Year Rolling Average',
                            'Serious injuries', 'Serious injuries_5 Year Rolling Average', 'Serious injuries_100 mvmt', 'Serious injuries_100 mvmt_5 Year Rolling Average']]

    df_nm = df_nm[geos+['Year']+['Fatalities', 'Fatalities_5 Year Rolling Average', 
                                'Serious injuries', 'Serious injuries_5 Year Rolling Average']]

    df    = df   [df   ['Year']<=YEAR_CAP]
    df_nm = df_nm[df_nm['Year']<=YEAR_CAP]

    return df, df_nm


def export_safety_files(dfs, geo, sample_type, paths, categories):
    """
    Export indicator tables and metadata to Excel for each configured path and category.

    Parameters
    ----------
    df : pandas.DataFrame
        DataFrame to export. Must include a 'Year' column.
    geo : str
        Geographic label such as 'Jurisdiction', 'County', etc.
    sample_type : str
        Sample name, e.g. 'TIMS'.
    paths : list[Path]
        Output directories.
    categories : list[str]
        Categories to loop through, e.g. ['Collision Rates', 'Non-Motorized'].
    """

    created_files = []
    
    

    for path in paths:
        for category in categories:
            if category == "Collision Rates":
                indicator = "Safety_1"
                df = dfs[0]
            elif category == "Non-Motorized":
                indicator = "Safety_2"
                df = dfs[1]
            else:
                indicator = category.replace(" ", "_")

            params = {
                        "sample": sample_type,
                        "start_year": df["Year"].min(),
                        "end_year": df["Year"].max(),
                        "estimate": None,
                        "moe_thresh": None,
                        "indicator": indicator,
                        "geo": geo
                    }

            df_about = func.write_about(params)

            if path == PATH_SP:
                output_dir = path / f"{indicator} {category}"
                output_dir.mkdir(parents=True, exist_ok=True)
                file_out = output_dir / f"{indicator} {geo} {sample_type}_TEST.xlsx"
            elif path == PATH_SERVER:
                file_out = path / f"{indicator} {geo} {sample_type}_TEST.xlsx"
            else:
                file_out = path / f"{indicator} {geo} {sample_type}_TEST.xlsx"

            print("Excel files exported here: " + str(file_out))

            with pd.ExcelWriter(file_out, engine="xlsxwriter") as writer:
                df_about.to_excel(writer, index=False, sheet_name="About", header=False)
                df.to_excel(writer, index=False, sheet_name=geo)

            created_files.append(file_out)

    return created_files


YEAR_CAP = 2025
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_SP     = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents' / 'Data' / 'Safe Equitable Resilient Infrastructure' / 'Safety'

EXPORT=True


if __name__=='__main__':

    sample_type = 'TIMS'
    indicators = ['Safety_1', 'Safety_2']
    categories = ['Collision Rates', 'Non-Motorized']
    paths = [PATH_SP, PATH_SERVER]

    geos_map = {
        'Jurisdiction': ['COUNTY', 'CITY'],
        'County': ['COUNTY'],
        'Region': ['REGION'],
        'Statewide': ['STATEWIDE']
    }

    gdf_col = import_collisions(sde.sql_collisions)

    geos_map_df    = {}
    geos_map_df_nm = {}

    for geo, geos in geos_map.items():

        print(f'\n\n\n{geo}\n')
        df, df_nm = safety_indicators_rollup(gdf_col, geos)

        if EXPORT:
            export_safety_files(
                dfs=[df, df_nm],
                geo=geo,
                sample_type=sample_type,
                paths=paths,
                categories=categories,
            )


