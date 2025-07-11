"""
Name: set_calendar_dates.py
Purpose: Hard codes in start_date and end_date values for calendar.txt files
    This is to ensure all operators' start and end dates are shared for regional analyses.

    NOTE - THIS WILL NOT WORK FOR YCTD. ITS DATES MUST BE UPDATED MANUALLY USING FOLLOWING PROCESS:
        1 - Use calendar_dates.txt to identify which service_ids correspond to normal weekday, normal Saturday, normal Sunday	
        2 - Create calendar.txt with following fields and apply correct values (even better, just have a template calendar.txt for YCTD and just update the service_id and start/end dates when new feed comes in	
                service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
        3 - Update calendar_dates.txt to:	
                only have 1 unique value in date field
                remove all rows with duplicate service_id values


Author: Darren Conly
Last Updated: July 2025
Updated by: Josh
Copyright:   (c) SACOG
Python Version: 3.x
"""


## Packages ---

from pathlib import Path
import shutil
import pandas as pd
import csv
import zipfile
from datetime import date
from datetime import datetime
from IPython.display import display

import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.offline import plot
import plotly.subplots as sp
from plotly.subplots import make_subplots


## User defined functions ---

def extract_zip(zfile_in, output_folder=None, overwrite_ok=True):
    if not output_folder:
        zfp = Path(zfile_in)
        output_folder = zfp.parent.joinpath(zfp.stem)
    else:
        Path(output_folder).mkdir(exist_ok=overwrite_ok)

    with zipfile.ZipFile(zfile_in, 'r') as zfo:
        zfo.extractall(path=output_folder)

    return output_folder


def update_calendar_dates_txt(op_dir, dummy_date_str):
    """hard-set all calendar_date date field vals to dummy_date_str
    and delete all rows with duplicate service_id values"""

    calendar_dates_txt = Path(op_dir).joinpath('calendar_dates.txt')

    df = pd.read_csv(calendar_dates_txt)

    df['date'] = dummy_date_str

    df = df.groupby('service_id', as_index=False).min()


    header_out = ','.join(df.columns)
    with open(calendar_dates_txt, 'w') as fo:
        fo.write(f"{header_out}\n")
        for row in df.to_records(index=False):
            row = ','.join([str(i) for i in row])
            fo.write(f"{row}\n")
            


def update_start_end_dates(op_dir, file_name, new_start_date, new_end_date,
                           start_date_field, end_date_field, dummy_date):

    txt_file_in = Path(op_dir).joinpath(file_name)

    if txt_file_in.exists():
        dict_rows = []
        with open(txt_file_in, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for k, v in row.items():
                    row[k] = v.replace(',', '_') # prevent weird field delimiting issues by removing commas from field values
                dict_rows.append(row)

        header = ','.join(dict_rows[0].keys())
        rows_out = [header]
        for dr in dict_rows:
            dr[start_date_field] = new_start_date
            dr[end_date_field  ] = new_end_date
            rowvals = ','.join(dr.values())
            rows_out.append(rowvals)

        with open(txt_file_in, 'w') as f:
            for row in rows_out:
                f.write(f"{row}\n")
        
        update_calendar_dates_txt(op_dir, dummy_date_str=dummy_date)
    else:
        if file_name == 'calendar.txt':
            print(f"\tWARNING: {txt_file_in} not found. You may need to manually update dates in calendar_dates.txt")
        pass


def create_zip(dir_to_zip, zip_parent_dir):
    
    fp_tozip = Path(dir_to_zip)
    fp_parentdir = Path(zip_parent_dir)
    out_zip_path = fp_parentdir.joinpath(f"{fp_tozip.name}.zip")
    with zipfile.ZipFile(out_zip_path, 'w') as zo:
        for f in fp_tozip.glob('*'):
            zo.write(f, arcname=f.name)


def check_gtfs_dates(op_dir, file_name, start_date_field, end_date_field, transit_agency_field):

    list_df_calendars = []
    for src_dir_zip in Path(op_dir).glob('*.zip'):

        try:
            with zipfile.ZipFile(src_dir_zip, 'r') as zf:
                with zf.open(file_name, 'r') as txt_file:
                    df_cal = pd.read_csv(txt_file, sep=',')

            df_cal = df_cal[[start_date_field, end_date_field]].drop_duplicates()
            df_cal[transit_agency_field] = src_dir_zip.stem
            df_cal = df_cal.set_index(transit_agency_field).reset_index()
            list_df_calendars.append(df_cal)
        except:
            pass

    df_cal = pd.concat(list_df_calendars)
    df_cal = df_cal.reset_index(drop=True)

    df_cal[start_date_field] = pd.to_datetime(df_cal[start_date_field], format='%Y%m%d')
    df_cal[end_date_field  ] = pd.to_datetime(df_cal[end_date_field  ], format='%Y%m%d')
    df_cal.loc[df_cal[end_date_field] > datetime.today().strftime("%Y-%m-%d"), end_date_field] = datetime.today().strftime("%Y-%m-%d")

    fig_starts = px.histogram(df_cal, x=start_date_field, histfunc='count', nbins=30, 
                                color=transit_agency_field, template='plotly_white', color_discrete_sequence=px.colors.qualitative.Vivid, 
                                title='Start Date Frequency by Transit Agency')
    fig_ends   = px.histogram(df_cal, x=end_date_field  , histfunc='count', nbins=30, 
                                color=transit_agency_field, template='plotly_white', color_discrete_sequence=px.colors.qualitative.Vivid, 
                                title='End Date Frequency by Transit Agency'  )

    fig_starts.show()
    fig_ends  .show()

    print('A sample of start/end dates:')
    display(df_cal.head(10))
    display(df_cal.tail(10))
    print(); print('Check histograms in browser to observe all start/end dates')




## Run main ---------------------------------------------------------------------------------------------------------------------------------------------------



if __name__ == '__main__':

    print(); print()
    source_gtfs_parent_dir = r'I:\Transit\GTFS\original_gtfs' # a folder containing only the ZIPs of GTFS feeds
    dest_gtfs_parent_dir = r'I:\Projects\Josh\Geospatial Data\GTFS\datemod_versions'



    ## Check calendars ---


    print('Concatenating all start/end dates together...'); print()
    check_gtfs_dates(op_dir                  = source_gtfs_parent_dir
                      , file_name            = 'calendar.txt'
                      , start_date_field     = 'start_date'
                      , end_date_field       = 'end_date'
                      , transit_agency_field = 'transit_agency')

    print(); print()
    print('Please input a start and end date that seems appropriate (use "YYYYMMDD" format):')
    print('Start date: ')
    newstart = input() #'20240101' # How do I know which start/end dates I need to use?
    print('End date: ')
    newend = input() # '20240801'

    dummy = newend # '20240801' # set to some holiday value



    ## Adjust calendars ---


    # check = bool(input("WARNING: this script will overwrite calendar.txt. Enter 'yes' if you still wish to proceed. Otherwise leave blank and hit enter: "))
    # if not check:
    #     raise Exception("Script aborted by user.")
    # import pdb; pdb.set_trace()
    for src_dir_zip in Path(source_gtfs_parent_dir).glob('*.zip'):

        # set up destination directory; deleting if already exists
        dest_dir = Path(dest_gtfs_parent_dir).joinpath(src_dir_zip.stem)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)

        extract_zip(src_dir_zip, output_folder=dest_dir) # extract files to destination folder

        # shutil.copytree(src=src_dir, dst=dest_dir) # 1/12/24 - should be able to delete this line
        print(); print()

        print(f"updating calendar.txt in {dest_dir}...")
        update_start_end_dates(op_dir             = dest_dir
                               , file_name        = 'calendar.txt'
                               , new_start_date   = newstart
                               , new_end_date     = newend
                               , start_date_field = 'start_date'
                               , end_date_field   = 'end_date'
                               , dummy_date       = dummy)
        
        print(f"updating feed_info.txt in {dest_dir}...")
        update_start_end_dates(op_dir             = dest_dir
                               , file_name        = 'feed_info.txt'
                               , new_start_date   = newstart
                               , new_end_date     = newend
                               , start_date_field = 'feed_start_date'
                               , end_date_field   = 'feed_end_date'
                               , dummy_date       = dummy)
        
        print(); print()
        create_zip(dest_dir, dest_gtfs_parent_dir)