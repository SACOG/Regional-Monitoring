

# TODO:
# write_ABOUT functions need work on specificity - being able to adjust easily what to label the params['geo']


from pathlib import Path
import pandas as pd
import re
from datetime import date
import yaml

from time import perf_counter as perf
import pyodbc
import urllib
import sqlalchemy as sqla


PATH_GIT = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_GIT / 'Data' / 'Census' / 'config'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")



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

    if params['estimate'] is None:
        df = pd.DataFrame([yaml_about[params['sample']][params['indicator']]]).T.reset_index().rename(columns = {'index': 'Indicator', 0: params['indicator']})
    elif params['sample'] == 'LEHD':
        df = pd.DataFrame([yaml_about[params['sample']][params['estimate']][params['indicator']]]).T.reset_index().rename(columns = {'index': 'Indicator', 0: params['indicator']})
    else:
        df = pd.DataFrame.from_dict([yaml_about[params['estimate']][params['sample']][params['indicator']]]).T.reset_index().rename(columns = {'index': 'Indicator', 0: params['indicator']})


    df.loc[df['Indicator'] == 'Last Updated', params['indicator']] = date.today().strftime('%Y-%m-%d')
    df.loc[df['Indicator'] == 'Year(s)'     , params['indicator']] = f"{params['start_year']}-{params['end_year']}"
    if params['moe_thresh'] is not None:
        df.loc[df['Indicator'] == 'Margin of Error Limit', params['indicator']] = params['moe_thresh']


    # Old:
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
    def split_notes(df):
        row_notes = df[df['Indicator'] == 'Notes'].copy()
        notes = row_notes[params['indicator']].values[0]
        
        lines = notes.split('\\n')
        rows_new = [{'Indicator': 'Notes' if i == 0 else '', params['indicator']: line} for i, line in enumerate(lines) if line]
        
        df_new = pd.DataFrame(rows_new)
        df_filtered = df[df['Indicator'] != 'Notes']
       
        df_notes = pd.concat([df_filtered, df_new], ignore_index=True)
        
        return df_notes
    

    df = split_notes(df)

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



