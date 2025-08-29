

import pandas as pd
import re
from datetime import date
from xlwt.Workbook import *
import yaml

from time import perf_counter as perf
import pyodbc
import urllib
import sqlalchemy as sqla





# About ----------------------------------------------------------------------------------------------------------------------------------------------------



# Writes about page for each indicator
def write_about(sample_type, indicator, year_start, year_end, path_config0, geography=None, MOE_thresh=None, estimate=None):

    '''
    User defined function to create/export about documentation for each indicator
    Inputs: yaml file, specific indicator inputs (geography, sample type, ...), data frame to export, file paths, ...
    Uses user defined inputs to organize .yaml file subset into pandas data frame then exports to excel file sheet
    '''

    # Reads in .yaml file
    # Defines initialized objects in the yaml file with objects defined in processing script

    path_yaml = path_config0 / 'about.yaml'
    
    try:
        with open(path_yaml, 'r') as yaml_file:
            dt_about = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {path_yaml} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    if estimate is None:
        df = pd.DataFrame.from_dict(dt_about[sample_type][indicator]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator})
    elif sample_type == 'LEHD':
        df = pd.DataFrame.from_dict(dt_about[sample_type][estimate][indicator]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator})
    else:
        df = pd.DataFrame.from_dict(dt_about[estimate][sample_type][indicator]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator})


    df.loc[df['Indicator'] == 'Last Updated', indicator] = date.today().strftime('%Y-%m-%d')
    df.loc[df['Indicator'] == 'Year(s)'     , indicator] = f"{year_start}-{year_end}"
    if MOE_thresh is not None:
        df.loc[df['Indicator'] == 'Margin of Error Limit', indicator] = MOE_thresh


    # Old:
    if geography is not None:
        df.loc[df['Indicator'] == 'Geography', indicator] = geography

    # ## New:
    # if geography is not None:
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

    #     if indicator in dt_geo.keys():
    #         df.loc[df['Indicator'] == 'Geography', indicator] = dt_geo[indicator][geography]
    #     else:
    #         df.loc[df['Indicator'] == 'Geography', indicator] = geography


    # Split notes into rows, for visual clarity in about
    # Find the row with 'Notes', then use that to take the information
    # Separate based off of NewLines, make the rows with this
    # Make a blank row past the first one. This way, we don't have to see notes as a cell like 7 times.
    # Create a df from the new separated rows. Drop the old notes row
    # Combine original with new rows
    # Finally, we split the notes
    def split_notes(df):
        row_notes = df[df['Indicator'] == 'Notes'].copy()
        notes = row_notes[indicator].values[0]
        
        lines = notes.split('\\n')
        rows_new = [{'Indicator': 'Notes' if i == 0 else '', indicator: line} for i, line in enumerate(lines) if line]
        
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





# Miscellaneous ----------------------------------------------------------------------------------------------------------------------------------


# Unique values - a substitute for list(set(x))
def unique(list_a):
 
    # initialize a null list
    # traverse for all elements
        # check if exists in unique_list or not

    unique_list = []
    for x in list_a:
        if x not in unique_list:
            unique_list.append(x)

    return unique_list


def setdiff(list_a, list_b):
    set_a = set(list_a)
    set_b = set(list_b)
    in_list_a_but_not_in_list_b = set_a.difference(set_b)
    return in_list_a_but_not_in_list_b



# Function to create list of values inbetween range
def sequence(r1, r2, step):
    return [item for item in range(r1, r2+1, step)]



# Remove anything before/after specified string, use regular expression (currently set to remove everything after the first period)
def re_remove_post(x, exp=' '):
    try: x = x.split(exp, 1)[0]
    except: pass
    return x
def re_remove_pre(x, exp=' '):
    try: x = x.split(exp, 1)[1]
    except: pass
    return x



# Moves column to position after specified column
def move_column_after(df, col_to_move, after_col):

    # Get a list of all column names
    # Find the index of the column to move and the index of the column to move it after
    # Remove the column to move from its current position
    # Insert the column at the new position
    # Reorder the DataFrame columns using the updated list

    cols = list(df.columns)
    col_idx = cols.index(col_to_move)
    after_col_idx = cols.index(after_col)
    cols.pop(col_idx)
    cols.insert(after_col_idx + 1, col_to_move)

    return df[cols]


