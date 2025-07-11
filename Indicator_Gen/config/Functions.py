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



def move_column_after(df, col_to_move, after_col):
    # Get a list of all column names
    cols = list(df.columns)

    # Find the index of the column to move and the index of the column to move it after
    col_idx = cols.index(col_to_move)
    after_col_idx = cols.index(after_col)

    # Remove the column to move from its current position
    cols.pop(col_idx)

    # Insert the column at the new position
    cols.insert(after_col_idx + 1, col_to_move)

    # Reorder the DataFrame columns using the updated list
    return df[cols]




# Function to write about page for each indicator
def write_about(sample_type, indicator, year_start, year_end, path_config0, geography=None, MOE_thresh=None, estimate=None):

    
    '''
    User defined function to create/export about documentation for each indicator
    Inputs: .yaml file, specific indicator inputs (geography, sample type, ...), data frame to export, file paths, ...
    Uses user defined inputs to organize .yaml file subset into pandas data frame then exports to excel file sheet
    '''

    # Reads in .yaml file
    # Defines initialized objects in the yaml file with objects defined in processing script

    path_yaml = path_config0 / 'about_indicators.yaml'
    
    try:
        with open(path_yaml, 'r') as yaml_file:
            dict_about = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {path_yaml} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

    if estimate is None:
        df = pd.DataFrame.from_dict(dict_about[sample_type][indicator]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator})
    elif sample_type == 'LEHD':
        df = pd.DataFrame.from_dict(dict_about[sample_type][estimate][indicator]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator})
    else:
        df = pd.DataFrame.from_dict(dict_about[estimate][sample_type][indicator]).T.reset_index().rename(columns = {'index': 'Indicator', 0: indicator})


    df.loc[df['Indicator'] == 'Last Updated', indicator] = date.today().strftime('%Y-%m-%d')
    df.loc[df['Indicator'] == 'Year(s)'     , indicator] = f"{year_start}-{year_end}"
    if geography is not None:
        df.loc[df['Indicator'] == 'Geography', indicator] = geography
    if MOE_thresh is not None:
        df.loc[df['Indicator'] == 'Margin of Error Limit', indicator] = MOE_thresh


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





## Plotting ====================================================================================================






font_family = 'Microsoft YaHei'
# font_family = 'Arial Black, Arial, sans-serif'
template = 'plotly_white'
config={'modeBarButtonsToRemove': ['select', 'lasso', 'toImage'], 'displaylogo': False}
# config={'modeBarButtonsToRemove': ['select', 'lasso'], 'displaylogo': False}


def plot_agol(export):
    fig.update_layout(
        legend_title=None
        , title=title
        , template=template
        , font_family=font_family
        , xaxis_title=None
        , yaxis_title=None
        , yaxis=dict(tickfont=dict(size=12))
        , xaxis=dict(tickfont=dict(size=12))
        )
    
    fig.show(config=config)
    
    if export:
        fig.write_html( file=os.path.join(path_plots, f'{indicator}_{plot_name}.html'), config=config)
        




plots_link = 'https://mapping.sacog.org/monitoring/Data/'


sort_peers = [
    'Sacramento, CA'
    , 'Yuba City, CA'
    , 'Austin, TX'
    , 'Charlotte, NC'
    , 'Cincinnati, OH'
    , 'Cleveland, OH'
    , 'Columbus, OH'
    , 'Detroit, MI'
    , 'Indianapolis, IN'
    , 'Kansas City, MO'
    , 'Miami, FL'
    , 'Orlando, FL'
    , 'Phoenix, AZ'
    , 'Pittsburgh, PA'
    , 'Portland, OR'
    , 'Riverside, CA'
    , 'Salt Lake City, UT'
    , 'San Antonio, TX'
    , 'San Diego, CA'
    , 'San Francisco, CA'
    , 'San Jose, CA'
    , 'St. Louis, MO'
    , 'Tampa, FL'
    , 'National'
]



pop_eth_labels  = {
    'All': 'All'
    , 'American Indian or Alaska Native (NH)': 'American Indian or Alaska Native'
    , 'Asian (NH)': 'Asian'
    , 'Black or African American (NH)': 'Black or African American'
    , 'Hispanic or Latino': 'Hispanic or Latino'
    , 'Native Hawaiian or other Pacific Islander (NH)': 'Native Hawaiian or other Pacific Islander'
    , 'Some other race (NH)': 'Some other race'
    , 'Two or more races (NH)': 'Two or more races'
    , 'White (NH)': 'White (NH)'
}



color_map_eth  = {
    'Asian': '#9DC209'
    , 'Asian (NH)': '#9DC209'
    , 'Black or African American': '#1E90FF'
    , 'Black or African American (NH)': '#1E90FF'
    , 'Hispanic or Latino': "#FBB117"
    , 'White (NH)': "#DC381F"
}


color_map_sac_yuba_peermsa = {
         'Sacramento, CA':"#000000",
         'Yuba City, CA': "#1F45FC",
         "Peer MSA": "#9DC209"
}


color_map_nat_peermsa = {
                 "SACOG":"#9DC209",
                 "National": "#1F45FC",
                 "Peer MSA": "#1E90FF"
}



color_map_comp = {
                "SACOG": "#000000",
                 "California":"#9DC209",
                 "National": "#DC381F",
                 "Peer MSA": "#1E90FF"
}




color_map_nat_peers = {
    'Sacramento, CA': "#9DC209"
    , 'Yuba City, CA': "#9DC209"
    , 'National': "#1F45FC"
    , 'Austin, TX': "#1E90FF"
    , 'Charlotte, NC': "#1E90FF"
    , 'Cincinnati, OH': "#1E90FF"
    , 'Cleveland, OH': "#1E90FF"
    , 'Columbus, OH': "#1E90FF"
    , 'Detroit, MI': "#1E90FF"
    , 'Indianapolis, IN': "#1E90FF"
    , 'Kansas City, MO': "#1E90FF"
    , 'Miami, FL': "#1E90FF"
    , 'Orlando, FL': "#1E90FF"
    , 'Phoenix, AZ': "#1E90FF"
    , 'Pittsburgh, PA': "#1E90FF"
    , 'Portland, OR': "#1E90FF"
    , 'Riverside, CA': "#1E90FF"
    , 'Salt Lake City, UT': "#1E90FF"
    , 'San Antonio, TX': "#1E90FF"
    , 'San Diego, CA': "#1E90FF"
    , 'San Francisco, CA': "#1E90FF"
    , 'San Jose, CA': "#1E90FF"
    , 'St. Louis, MO': "#1E90FF"
    , 'Tampa, FL': "#1E90FF"
}



peer_msa_labels = {
    'Sacramento'                                                               : 'Sacramento, CA' 
    , 'Sacramento-Roseville-Folsom'                                            : 'Sacramento, CA'
    , 'Sacramento-Roseville-Folsom, CA'                                        : 'Sacramento, CA'
    , 'Sacramento--Roseville--Arden-Arcade, CA'                                : 'Sacramento, CA'
    , 'Sacramento-Roseville-Folsom, CA Metro Area'                             : 'Sacramento, CA'
    , 'Sacramento--Roseville--Arden-Arcade, CA Metro Area'                     : 'Sacramento, CA'
    , 'Sacramento--Arden-Arcade--Roseville, CA Metro Area'                     : 'Sacramento, CA'
    , 'Sacramento--Roseville--Arden-Arcade, CA Metropolitan Statistical Area'  : 'Sacramento, CA'
    , 'Yuba City'                                                              : 'Yuba City, CA'
    , 'Yuba City, CA'                                                          : 'Yuba City, CA'
    , 'Yuba City, CA Metro Area'                                               : 'Yuba City, CA'
    , 'Yuba City, CA Metropolitan Statistical Area'                            : 'Yuba City, CA'
    , 'Austin'                                                                 : 'Austin, TX'
    , 'Austin-Round Rock, TX'                                                  : 'Austin, TX'
    , 'Austin-Round Rock-Georgetown'                                           : 'Austin, TX'
    , 'Austin-Round Rock-Georgetown, TX'                                       : 'Austin, TX'
    , 'Austin-Round Rock, TX Metro Area'                                       : 'Austin, TX'
    , 'Austin-Round Rock-Georgetown, TX Metro Area'                            : 'Austin, TX'
    , 'Austin-Round Rock-San Marcos, TX Metro Area'                            : 'Austin, TX'
    , 'Austin-Round Rock, TX Metropolitan Statistical Area'                    : 'Austin, TX'
    , 'Charlotte'                                                              : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia'                                             : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia, NC-SC'                                      : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia, NC-SC Metro Area'                           : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia, NC-SC Metropolitan Statistical Area'        : 'Charlotte, NC'
    , 'Cincinnati'                                                             : 'Cincinnati, OH'
    , 'Cincinnati, OH-KY-IN'                                                   : 'Cincinnati, OH'
    , 'Cincinnati, OH-KY-IN Metro Area'                                        : 'Cincinnati, OH'
    , 'Cincinnati, OH-KY-IN Metropolitan Statistical Area'                     : 'Cincinnati, OH'
    , 'Cleveland-Elyria'                                                       : 'Cleveland, OH'
    , 'Cleveland-Elyria, OH'                                                   : 'Cleveland, OH'
    , 'Cleveland, OH Metro Area'                                               : 'Cleveland, OH'
    , 'Cleveland-Elyria, OH Metro Area'                                        : 'Cleveland, OH'
    , 'Cleveland-Elyria-Mentor, OH Metro Area'                                 : 'Cleveland, OH'
    , 'Cleveland-Elyria, OH Metropolitan Statistical Area'                     : 'Cleveland, OH'
    , 'Columbus'                                                               : 'Columbus, OH'
    , 'Columbus, OH'                                                           : 'Columbus, OH'
    , 'Columbus, OH Metro Area'                                                : 'Columbus, OH'
    , 'Columbus, OH Metropolitan Statistical Area'                             : 'Columbus, OH'
    , 'Detroit'                                                                : 'Detroit, MI'
    , 'Detroit-Warren-Dearborn'                                                : 'Detroit, MI'
    , 'Detroit-Warren-Dearborn, MI'                                            : 'Detroit, MI'
    , 'Detroit-Warren-Dearborn, MI Metropolitan Statistical Area'              : 'Detroit, MI'
    , 'Indianapolis'                                                           : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson'                                           : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson, IN'                                       : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson, IN Metro Area'                            : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Greenwood, IN Metro Area'                           : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson, IN Metropolitan Statistical Area'         : 'Indianapolis, IN'
    , 'Kansas City'                                                            : 'Kansas City, MO'
    , 'Kansas City, MO-KS'                                                     : 'Kansas City, MO'
    , 'Kansas City, MO-KS Metro Area'                                          : 'Kansas City, MO'
    , 'Kansas City, MO-KS Metropolitan Statistical Area'                       : 'Kansas City, MO'
    , 'Kansas City, MO-KS (Metropolitan Statistical Area)'                     : 'Kansas City, MO'
    , 'Miami'                                                                  : 'Miami, FL'
    , 'Miami-Fort Lauderdale-Pompano Beach'                                    : 'Miami, FL'
    , 'Miami-Fort Lauderdale-Pompano Beach, FL'                                : 'Miami, FL'
    , 'Miami-Fort Lauderdale-West Palm Beach, FL'                              : 'Miami, FL'
    , 'Miami-Fort Lauderdale-Pompano Beach, FL Metro Area'                     : 'Miami, FL'
    , 'Miami-Fort Lauderdale-West Palm Beach, FL Metro Area'                   : 'Miami, FL'
    , 'Miami-Fort Lauderdale-West Palm Beach, FL Metropolitan Statistical Area': 'Miami, FL'
    , 'Orlando'                                                                : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford'                                              : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford, FL'                                          : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford, FL Metro Area'                               : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford, FL Metropolitan Statistical Area'            : 'Orlando, FL'
    , 'Phoenix'                                                                : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Chandler'                                                  : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Chandler, AZ'                                              : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Scottsdale, AZ'                                            : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Chandler, AZ Metro Area'                                   : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Scottsdale, AZ Metropolitan Statistical Area'              : 'Phoenix, AZ'
    , 'Pittsburgh'                                                             : 'Pittsburgh, PA'
    , 'Pittsburgh, PA'                                                         : 'Pittsburgh, PA'
    , 'Pittsburgh, PA Metro Area'                                              : 'Pittsburgh, PA'
    , 'Pittsburgh, PA Metropolitan Statistical Area'                           : 'Pittsburgh, PA'
    , 'Portland'                                                               : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro'                                           : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro, OR-WA'                                    : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro, OR-WA Metro Area'                         : 'Portland, OR'
    , 'Portland-Vancouver-Beaverton, OR-WA Metro Area'                         : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro, OR-WA Metropolitan Statistical Area'      : 'Portland, OR'
    , 'Riverside'                                                              : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario'                                       : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario, CA'                                   : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario, CA Metro Area'                        : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario, CA Metropolitan Statistical Area'     : 'Riverside, CA'
    , 'Salt Lake City'                                                         : 'Salt Lake City, UT'
    , 'Salt Lake City, UT'                                                     : 'Salt Lake City, UT'
    , 'Salt Lake City, UT Metro Area'                                          : 'Salt Lake City, UT'
    , 'Salt Lake City-Murray, UT Metro Area'                                   : 'Salt Lake City, UT'
    , 'Salt Lake City, UT Metropolitan Statistical Area'                       : 'Salt Lake City, UT'
    , 'San Antonio'                                                            : 'San Antonio, TX'
    , 'San Antonio-New Braunfels'                                              : 'San Antonio, TX'
    , 'San Antonio-New Braunfels, TX'                                          : 'San Antonio, TX'
    , 'San Antonio-New Braunfels, TX Metro Area'                               : 'San Antonio, TX'
    , 'San Antonio-New Braunfels, TX Metropolitan Statistical Area'            : 'San Antonio, TX'
    , 'San Diego'                                                              : 'San Diego, CA'
    , 'San Diego-Chula Vista-Carlsbad'                                         : 'San Diego, CA'
    , 'San Diego-Chula Vista-Carlsbad, CA'                                     : 'San Diego, CA'
    , 'San Diego-Carlsbad, CA'                                                 : 'San Diego, CA'
    , 'San Diego-Chula Vista-Carlsbad, CA Metro Area'                          : 'San Diego, CA'
    , 'San Diego-Carlsbad, CA Metropolitan Statistical Area'                   : 'San Diego, CA'
    , 'San Francisco'                                                          : 'San Francisco, CA'
    , 'San Francisco-Oakland-Berkeley'                                         : 'San Francisco, CA'
    , 'San Francisco-Oakland-Berkeley, CA'                                     : 'San Francisco, CA'
    , 'San Francisco-Oakland-Hayward, CA'                                      : 'San Francisco, CA'
    , 'San Francisco-Oakland-Berkeley, CA Metro Area'                          : 'San Francisco, CA'
    , 'San Francisco-Oakland-Fremont, CA Metro Area'                           : 'San Francisco, CA'
    , 'San Francisco-Oakland-Hayward, CA Metropolitan Statistical Area'        : 'San Francisco, CA'
    , 'San Jose'                                                               : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara'                                         : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara, CA'                                     : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara, CA Metro Area'                          : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara, CA Metropolitan Statistical Area'       : 'San Jose, CA'
    , 'St. Louis'                                                              : 'St. Louis, MO'
    , 'St. Louis, MO-IL'                                                       : 'St. Louis, MO'
    , 'St. Louis, MO-IL Metro Area'                                            : 'St. Louis, MO'
    , 'St. Louis, MO-IL Metropolitan Statistical Area'                         : 'St. Louis, MO'
    , 'Tampa'                                                                  : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater'                                        : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater, FL'                                    : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater, FL Metro Area'                         : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater, FL Metropolitan Statistical Area'      : 'Tampa, FL'

    ## Other comparisons
    , 'Atlanta-Sandy Springs-Alpharetta, GA'                                   : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Roswell, GA Metro Area'                           : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Marietta, GA Metro Area'                          : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Alpharetta, GA Metro Area'                        : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Alpharetta, GA (Metropolitan Statistical Area)'   : 'Atlanta, GA'
    , 'Minneapolis-St. Paul-Bloomington, MN-WI'                                : 'Minneapolis, MN'
    , 'Minneapolis-St. Paul-Bloomington, MN-WI Metro Area'                     : 'Minneapolis, MN'
    , 'Minneapolis-St. Paul-Bloomington, MN-WI (Metropolitan Statistical Area)': 'Minneapolis, MN'
    , 'Seattle-Tacoma-Bellevue, WA'                                            : 'Seattle, WA'
    , 'Seattle-Tacoma-Bellevue, WA Metro Area'                                 : 'Seattle, WA'
    , 'Seattle-Tacoma-Bellevue, WA (Metropolitan Statistical Area)'            : 'Seattle, WA'

}
