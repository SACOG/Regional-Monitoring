"""
Name: set_calendar_dates.py
Purpose: Hard codes in start_date and end_date values for calendar.txt files
    This is to ensure all operators' start and end dates are shared for regional analyses.

    NOTE - THIS WILL NOT WORK FOR YCTD. ITS DATES MUST BE UPDATED MANUALLY USING FOLLOWING PROCESS:
        1 - Use calendar_dates.txt to identify which service_ids correspond to normal weekday, normal Saturday, normal Sunday	
        2 - Create calendar.txt with following fields and apply correct values (even better, just have a template calendar.txt for YCTD and 
                just update the service_id and start/end dates when new feed comes in service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date
        3 - Update calendar_dates.txt to:	
                only have 1 unique value in date field
                remove all rows with duplicate service_id values


Author: Darren Conly
Last Updated: July 2025
Updated by: Josh
Copyright:   (c) SACOG
Python Version: 3.x
"""


# Workspace -------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import csv
import zipfile
from datetime import datetime
from IPython.display import display
import plotly.express as px


SOURCE_GTFS_PARENT_DIR = r'I:\Projects\Josh\Geospatial Data\GTFS\original_gtfs' # a folder containing only the ZIPs of GTFS feeds
DEST_GTFS_PARENT_DIR = r'I:\Projects\Josh\Geospatial Data\GTFS\datemod_versions'




# updates by josh
def check_gtfs_dates(op_dir, file_name, start_date_field, end_date_field, transit_agency_field):

    list_df_calendars = []
    for src_dir_zip in Path(op_dir).glob('*.zip'):

        try:
            with zipfile.ZipFile(src_dir_zip, 'r') as zf:
                with zf.open(file_name, 'r') as txt_file:
                    df = pd.read_csv(txt_file, sep=',')

            df = df[[start_date_field, end_date_field]].drop_duplicates()
            df[transit_agency_field] = src_dir_zip.stem
            df = df.set_index(transit_agency_field).reset_index()
            list_df_calendars.append(df)
        except:
            pass

    df = pd.concat(list_df_calendars)
    df = df.reset_index(drop=True)

    df[start_date_field] = pd.to_datetime(df[start_date_field], format='%Y%m%d')
    df[end_date_field  ] = pd.to_datetime(df[end_date_field  ], format='%Y%m%d')
    df.loc[df[end_date_field] > datetime.today().strftime("%Y-%m-%d"), end_date_field] = datetime.today().strftime("%Y-%m-%d")

    fig_starts = px.histogram(df, x=start_date_field, histfunc='count', nbins=30, 
                                color=transit_agency_field, template='plotly_white', color_discrete_sequence=px.colors.qualitative.Vivid, 
                                title='Start Date Frequency by Transit Agency')
    fig_ends   = px.histogram(df, x=end_date_field  , histfunc='count', nbins=30, 
                                color=transit_agency_field, template='plotly_white', color_discrete_sequence=px.colors.qualitative.Vivid, 
                                title='End Date Frequency by Transit Agency'  )

    fig_starts.show()
    fig_ends  .show()

    print('A sample of start/end dates:')
    display(df.head(10))
    display(df.tail(10))
    print(); print('Check histograms in browser to observe all start/end dates')




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
            



# updates by josh
def yolobus(op_dir, new_start_date, new_end_date, start_date_field, end_date_field):

    '''
    Function to convert calendar_dates.txt file to calendar.txt
    Only needed for transit agencies that do not have a calendar.txt file but do have a calendar_dates.txt file (looking at you yolobus)
    Reads in calendar_dates.txt, counts number of occurences by day of the week for each service_id, ...
    Filters to weekly occuring service_ids, removes non-recurring service_ids
    Each df is reshaped to create the calendar.txt and update the calendar_dates.txt files
    '''

    dt_dow = {
        0:'monday',
        1:'tuesday',
        2:'wednesday',
        3:'thursday',
        4:'friday',
        5:'saturday',
        6:'sunday'
    }

    txt_calendar_dates = Path(op_dir).joinpath('calendar_dates.txt')
    df_cal = pd.read_csv(txt_calendar_dates, sep=',')

    df = df_cal.copy()
    df['date_'] = pd.to_datetime(df['date'], format='%Y%m%d')

    df['dow'] = df['date_'].dt.dayofweek
    df = df.groupby(['service_id', 'dow'], as_index=False)['date'].count()
    df.columns = ['service_id', 'dow', 'count']

    df['is_weekly'] = df['count'].eq(df.groupby('dow')['count'].transform('max'))

    df_weekly  = df[df['is_weekly'] == True ]
    df_special = df[df['is_weekly'] == False]

    df_weekly['weekday'] = df_weekly['dow'].map(dt_dow)
    df_weekly = df_weekly.sort_values('dow')
    df_weekly = df_weekly.drop(['is_weekly', 'dow'], axis=1)

    df_weekly['count'] = df_weekly['count'].astype(int)
    df_weekly = df_weekly.pivot_table(index=['service_id'], columns='weekday', values='count').reset_index()

    df_weekly = df_weekly.fillna(0)
    integer_cols = df_weekly.select_dtypes(include=np.number).columns
    for col in integer_cols:
        df_weekly.loc[df_weekly[col] > 0, col] = 1

    df_weekly[start_date_field] = new_start_date
    df_weekly[end_date_field  ] = new_end_date

    for dow in dt_dow.keys():
        col = dt_dow[dow]
        df_weekly[col] = df_weekly[col].astype(int)

    col_order = ['service_id', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'start_date', 'end_date']
    df_weekly = df_weekly[col_order]

    df_special = df_cal[df_cal['service_id'].isin(df_special['service_id'].unique())]
    df_special['date'] = newstart
    df_special = df_special.drop_duplicates()

    return df_weekly, df_special




def update_start_end_dates(op_dir, file_name, new_start_date, new_end_date, start_date_field, end_date_field, dummy_date):

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
        # updates by josh
        try:
            if 'calendar' in str(txt_file_in):
                print(f"\tWARNING: {txt_file_in} not found. Creating calendar.txt file from calendar_dates.txt file...")
                df_weekly, df_special = yolobus(op_dir, new_start_date, new_end_date, start_date_field, end_date_field)
                df_weekly.to_csv(txt_file_in, index=False, sep=',')

                txt_calendar_dates = Path(op_dir).joinpath('calendar_dates.txt')
                df_special.to_csv(txt_calendar_dates, index=False, sep=',')
            else:
                pass
        except: 
            print(f"\tWARNING: Just kidding. {txt_file_in} not found and the yolobus function failed to resolve. You may need to manually update dates in calendar_dates.txt")



def create_zip(dir_to_zip, zip_parent_dir):
    
    fp_tozip = Path(dir_to_zip)
    fp_parentdir = Path(zip_parent_dir)
    out_zip_path = fp_parentdir.joinpath(f"{fp_tozip.name}.zip")
    with zipfile.ZipFile(out_zip_path, 'w') as zo:
        for f in fp_tozip.glob('*'):
            zo.write(f, arcname=f.name)





# Main ---------------------------------------------------------------------------------------------------------------------------------------------------



if __name__ == '__main__':

    print(); print()


    ## Check calendars ---

    # updates by josh
    print('Concatenating all start/end dates together...'); print()
    check_gtfs_dates(op_dir                  = SOURCE_GTFS_PARENT_DIR
                      , file_name            = 'calendar.txt'
                      , start_date_field     = 'start_date'
                      , end_date_field       = 'end_date'
                      , transit_agency_field = 'transit_agency')

    print(); print()
    print('Please input a start and end date that seems appropriate (use "YYYYMMDD" format):')
    print('Start date: ')
    newstart = input()
    print('End date: ')
    newend = input()

    dummy = newend



    ## Adjust calendars ---


    # check = bool(input("WARNING: this script will overwrite calendar.txt. Enter 'yes' if you still wish to proceed. Otherwise leave blank and hit enter: "))
    # if not check:
    #     raise Exception("Script aborted by user.")
    # import pdb; pdb.set_trace()
    for src_dir_zip in Path(SOURCE_GTFS_PARENT_DIR).glob('*.zip'):

        # if 'amtrak' in str(src_dir_zip):
        #     print('Restricting amtrak to ValleyVision bounding box...')
        #     amtrak(op_dir=src_dir_zip)
        #     print('Successfully cleaned amtrak zip file!')

        # set up destination directory; deleting if already exists
        dest_dir = Path(DEST_GTFS_PARENT_DIR).joinpath(src_dir_zip.stem)
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
        create_zip(dest_dir, DEST_GTFS_PARENT_DIR)