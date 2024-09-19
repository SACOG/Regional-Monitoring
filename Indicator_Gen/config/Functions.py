### Packages -----------------------------------------------------------------------------------------------------------------

import numpy as np
import pandas as pd
import os
import json
from tqdm import tqdm
import re
from datetime import date
import requests
import ast
import xlwt
from xlwt.Workbook import *
from pandas import ExcelWriter
import xlsxwriter
import yaml

# Plotting
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio







### GENERAL FUNCTIONS ----------------------------------------------------------------------------------------------------------------- 


# function to get unique values
def unique(list1):
 
    # initialize a null list
    unique_list = []
 
    # traverse for all elements
    for x in list1:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list




# Function to create list of values inbetween range
def sequence(r1, r2, step):
    return [item for item in range(r1, r2+1, step)]





# Remove anything after specified string, use regular expression (currently set to remove everything after the first period)
def re_remove_post(x, exp = ' '):
    if x == 'nan':
        return 'nan'
    else:
        return x.split(exp, 1)[0]
    
def re_remove_pre(x, exp = ' '):
    if x == 'nan':
        return 'nan'
    else:
        return x.split(exp, 1)[1]







   
# Function to write about page for each indicator
def write_about(sample_type, indicator_name, geography, year_start, year_end, path_config0, MOE_thresh=None, estimate=None):

    
    '''
    User defined function to create/export about documentation for each indicator
    Inputs: .yaml file, specific indicator inputs (geography, sample type, ...), data frame to export, file paths, ...
    Uses user defined inputs to organize .yaml file subset into pandas data frame then exports to excel file sheet
    '''

    # Reads in .yaml file
    # Defines initialized objects in the yaml file with objects defined in processing script

    path_yaml = os.path.join(path_config0, 'about_indicators.yaml')
    
    try:
        with open(path_yaml, 'r') as yaml_file:
            dict_about = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {path_yaml} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    if estimate is None:
        df = pd.DataFrame.from_dict(dict_about[sample_type][indicator_name]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator_name})
    else:
        df = pd.DataFrame.from_dict(dict_about[estimate][sample_type][indicator_name]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator_name})

    df.loc[df['Indicator'] == 'Last Updated', indicator_name] = date.today().strftime('%Y-%m-%d')
    df.loc[df['Indicator'] == 'Year(s)'     , indicator_name] = f"{year_start}-{year_end}"
    df.loc[df['Indicator'] == 'Geography'   , indicator_name] = geography
    if MOE_thresh is not None:
        df.loc[df['Indicator'] == 'Margin of Error Limit', indicator_name] = MOE_thresh


    # Split notes into rows, for visual clarity in about
    # Find the row with 'Notes', then use that to take the information
    # Separate based off of NewLines, make the rows with this
    # Make a blank row past the first one. This way, we don't have to see notes as a cell like 7 times.
    # Create a df from the new separated rows. Drop the old notes row
    # Combine original with new rows
    # Finally, we split the notes
    def split_notes(df):
        row_notes = df[df['Indicator'] == 'Notes'].copy()
        notes = row_notes[indicator_name].values[0]
        
        lines = notes.split('\\n')
        rows_new = [{'Indicator': 'Notes' if i == 0 else '', indicator_name: line} for i, line in enumerate(lines) if line]
        
        df_new = pd.DataFrame(rows_new)
        df_filtered = df[df['Indicator'] != 'Notes']
       
        df_notes = pd.concat([df_filtered, df_new], ignore_index=True)
        
        return df_notes
    
   
    df = split_notes(df)

    return df









### SQL FUNCTIONS =======================================================================================================================



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