

# TODO:
# write_ABOUT functions need work on specificity - being able to adjust easily what to label the params['geo']
# Production_5, Policy_5 needs to be lined up with other descriptions/notes


from pathlib import Path
import pandas as pd
import geopandas as gpd
import re
from datetime import date
import yaml
from time import perf_counter as perf
import pyodbc
import urllib
import sqlalchemy as sqla


PATH_CONFIG0 = Path(__file__).parent



# About ----------------------------------------------------------------------------------------------------------------------------------------------------


# Writes about page for each params['indicator']
def write_about(params):

    '''
    User defined function to create/export about documentation for each params['indicator']
    Inputs: yaml file, specific params['indicator'] inputs (params['geo'], sample type, ...), data frame to export, file paths, ...
    Uses user defined inputs to organize .yaml file subset into pandas data frame then exports to excel file sheet
    '''

    # Reads in .yaml file
    # Defines initialized objects in the yaml file with objects defined in processing script

    path_yaml = PATH_CONFIG0 / 'about.yaml'
    
    try:
        with open(path_yaml, 'r') as yaml_file:
            yaml_about = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {path_yaml} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    df_source = pd.DataFrame([yaml_about[params['sample']]['Source']]).T.reset_index().rename(columns = {'index': 'Indicator', 0: params['indicator']})
    df_ind    = pd.DataFrame([yaml_about[params['sample']]['Indicators'][params['indicator']]]).T.reset_index().rename(columns = {'index': 'Indicator', 0: params['indicator']})
    # breakpoint()
    if params['sample'] in ['ACS', 'PUMS', 'BLS', 'LEHD']:
        # if params['estimate'] in ['ACS5', 'ACS1']:
        if params['sample'] not in ['PUMS', 'LEHD']:
            df_source.loc[df_source['Indicator']=='Source', params['indicator']] = df_source[df_source['Indicator']=='Source'][params['indicator']].values[0] + ': ' + df_ind[df_ind['Indicator']=='Table(s)'][params['indicator']].values[0]
            df_ind = df_ind[df_ind['Indicator']!='Table(s)']
        df_est = pd.DataFrame([yaml_about[params['sample']][params['estimate']]]).T.reset_index().rename(columns = {'index': 'Indicator', 0: params['indicator']})
        df = pd.concat([df_ind, df_source, df_est])
    elif yaml_about[params['sample']]['Sample']:
        df_samp = pd.DataFrame([yaml_about[params['sample']]['Sample']]).T.reset_index().rename(columns = {'index': 'Indicator', 0: params['indicator']})
        df = pd.concat([df_ind, df_source, df_samp])
    else:
        df = pd.concat([df_ind, df_source])

    df.loc[df['Indicator'] == 'Year(s)', params['indicator']] = f"{params['start_year']}-{params['end_year']}"
    df.loc[df['Indicator'] == 'Last Updated', params['indicator']] = date.today().strftime('%Y-%m-%d')

    ## Old:
    if params['geo']:
        df.loc[df['Indicator'] == 'Geography', params['indicator']] = params['geo']

    if params['geo'] == 'Places':
        df.loc[df['Indicator'] == 'Geography', params['indicator']] = 'Census Designated Places (Jurisdictions)'

    # ## New:
    # if params['geo'] is not None:
    #     dt_geo = {
    #         'Cost_3'      : {'MPO':'Six County Sacramento Region'},
    #         'Cost_5'      : {'MPO':'Six County Sacramento Region'},
    #         'Production_3': {'MPO':'California Regions'          },
    #         'Production_4': {'MPO':'Six County Sacramento Region'},
    #         'Location_2a' : {'MPO':'Six County Sacramento Region'},
    #         'Location_2b' : {'MPO':'Six County Sacramento Region'},
    #         'Cost_1' : {'MSA'          :'MSAs (national peer midsized regions and other CA regions)',
    #                     'Counties'     : 'Counties (in California)'                                 ,
    #                     'Jurisdictions': 'Cities (in California)'                                   }
    #     }

    #     if params['indicator'] in dt_geo.keys():
    #         df.loc[df['Indicator'] == 'Geography', params['indicator']] = dt_geo[params['indicator']][params['geo']]
    #     else:
    #         df.loc[df['Indicator'] == 'Geography', params['indicator']] = params['geo']


    # Split notes into rows, for visual clarity in about
    # Find the row with 'Notes', then use that to take the information
    # Separate based off of NewLines, make the rows with this
    # Make a blank row past the first one. This way, we don't have to see notes as a cell like 7 times.
    # Create a df from the new separated rows. Drop the old notes row
    # Combine original with new rows
    # Finally, we split the notes

    df['Indicator'] = pd.Categorical(df['Indicator'], ['Title', 'Source', 'Website', 'Last Updated', 'Estimate', 'Year(s)', 'Geography', 'Description', 'Notes'])
    df = df.sort_values('Indicator')

    def split_notes(df, col):
        row_notes = df[df['Indicator'] == col].copy()
        notes = row_notes[params['indicator']].values[0]
        
        lines = notes.split('\\n')
        rows_new = [{'Indicator': col if i == 0 else '', params['indicator']: line} for i, line in enumerate(lines) if line]
        
        df_new = pd.DataFrame(rows_new)
        df_filtered = df[df['Indicator'] != col]
       
        df_notes = pd.concat([df_filtered, df_new], ignore_index=True)
        
        return df_notes

    try:
        df = split_notes(df, 'Description')
    except Exception as e:
        e
    try:
        df = split_notes(df, 'Notes')
    except Exception as e:
        e

    return df







# SQL ------------------------------------------------------------------------------------------------------------------------------------------------------------------



def get_odbc_driver():
    # gets name of ODBC driver, with name "ODBC Driver <version> for SQL Server"
    drivers = [d for d in pyodbc.drivers() if 'ODBC Driver ' in d]
    
    if len(drivers) == 0:
        errmsg = f"ERROR. No usable ODBC Driver found for SQL Server." \
        f"drivers found include {drivers}. Check ODBC Administrator program" \
        "for more information."
        
        raise Exception (errmsg)
    else:
        d_versions = [re.findall('\d+', dv)[0] for dv in drivers] # [re.findall('\d+', dv)[0] for dv in drivers]
        latest_version = max([int(v) for v in d_versions])
        driver = f"ODBC Driver {latest_version} for SQL Server"
    
        return driver

def sqlqry_to_df(query_str, dbname, servername='SQL-SVR', trustedconn='yes'):   

    driver = get_odbc_driver()  

    conn_str = f"DRIVER={driver};" \
        f"SERVER={servername};" \
        f"DATABASE={dbname};" \
        f"Trusted_Connection={trustedconn}"
        
    conn_str = urllib.parse.quote_plus(conn_str)
    engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")
       
    start_time = perf()

    # create SQL table from the dataframe
    print("Executing query. Results loading into dataframe...")
    df = pd.read_sql_query(sql=query_str, con=engine)
    rowcnt = df.shape[0]
    
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")
    
    return df

def sqlqry_to_gdf(query_str, dbname, servername='SQL-SVR', trustedconn='yes'):

    print()
    driver = get_odbc_driver()  

    conn_str = f"DRIVER={driver};" \
        f"SERVER={servername};" \
        f"DATABASE={dbname};" \
        f"Trusted_Connection={trustedconn}"

    conn_str = urllib.parse.quote_plus(conn_str)
    engine = sqla.create_engine(f"mssql+pyodbc:///?odbc_connect={conn_str}")

    start_time = perf()

    print("Executing query. Results loading into dataframe...")
    gdf = gpd.read_postgis(query_str, engine, geom_col="geometry")
    srid = int(gdf["srid"].iloc[0])
    gdf = gdf.set_crs(epsg=srid)
    gdf = gdf.drop('srid', axis=1)

    rowcnt = gdf.shape[0]
    
    et_mins = round((perf() - start_time) / 60, 2)
    print(f"Successfully executed query in {et_mins} minutes. {rowcnt} rows loaded into dataframe.")

    return gdf
