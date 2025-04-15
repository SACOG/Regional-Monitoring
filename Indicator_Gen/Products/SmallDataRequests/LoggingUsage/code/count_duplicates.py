


## Preparing workspace ---

import pandas as pd
from pathlib import Path
from datetime import date
import re

path_main = Path(r'I:\Projects\Josh\Regional Monitoring')
path_log = path_main / 'LoggingUsage'


## User defined functions function ---

def clean_file_name(file_):
    try:
        file_ = re.search(r'[^/]+$', file_).group()
        file_ = file_.replace('+', ' ')
        return file_
    except:
        return None
    
def keep_str_until_num(workbook_name):
    try:
        match = re.match(r'^\D*\d', workbook_name)
        if match:
            return match.group()
    except:
        return None



def count_log_duplicates(file_in, file_out, file_theme):
    '''
    User defined function to read in log file of Monitoring and Reporting Dashboard
    It reads in the organized download log file, then counts the occurence of duplicates
    Counts the number of date/workbook download combinations
    So it gives you the number of times a workbook was downloaded each 
    
    User must define file path to import cleaned downloads log file and file path to export results
    The results are exported to the user defined file location as a csv file

    If the code fails, it's most likely because you don't have the file paths defined correctly (using the 'pathlib' library)
    Check for updated packages and that file paths are assigned correctly if running into errors
    '''

    try:

        # Read in txt file
        df = pd.read_csv(file_in, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month

        df['file_name'] = df['file_'    ].apply(clean_file_name   )
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        # Merge themes onto workbooks
        df_map = pd.read_csv(file_theme)
        df = df.merge(df_map, on='Indicator', how='left')

        ## Calculate counts by:
        # By Theme
        df_by_theme = df.copy()
        df_by_theme = df_by_theme[['year', 'month', 'Theme']].value_counts().reset_index()
        df_by_theme = df_by_theme.sort_values(['year', 'month', 'Theme'], ascending=[False, False, True])
        df_by_theme = df_by_theme.reset_index(drop=True)
        # By Topic
        df_by_topic = df.copy()
        df_by_topic = df_by_topic[['year', 'month', 'Theme', 'Topic']].value_counts().reset_index()
        df_by_topic = df_by_topic.sort_values(['year', 'month', 'Theme', 'Topic'], ascending=[False, False, True, True])
        df_by_topic = df_by_topic.reset_index(drop=True)
        # By Workbook
        df_by_workbook = df.copy()
        df_by_workbook = df_by_workbook[['year', 'month', 'Theme', 'Topic', 'file_name']].value_counts().reset_index()
        df_by_workbook = df_by_workbook.sort_values(['year', 'month', 'Theme', 'Topic', 'file_name'], ascending=[False, False, True, True, True])
        df_by_workbook = df_by_workbook.reset_index(drop=True)
        # By Date/Workbook
        df_by_date = df.copy()
        df_by_date = df_by_date[['date_', 'file_name']].value_counts().reset_index()
        df_by_date = df_by_date.sort_values(['date_', 'file_name'], ascending=[False, True])
        df_by_date = df_by_date.reset_index(drop=True)

        # Write out to excel
        with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
            df            .to_excel(writer, index=False, sheet_name='Full'    )
            df_by_theme   .to_excel(writer, index=False, sheet_name='Themes'  )
            df_by_topic   .to_excel(writer, index=False, sheet_name='Topics'  )
            df_by_workbook.to_excel(writer, index=False, sheet_name='Workbook')
            df_by_date    .to_excel(writer, index=False, sheet_name='Days'    )
        print(); print(f'Successfully exported results to {file_out}'); print()

    except Exception as e:
        print(e)


## Main ---

if __name__ == '__main__':

    file_theme = path_main / 'Indicator_Theme_Mapping.csv'
    file_in = path_log / 'download_log_files' / '_DownloadedFiles.txt'
    file_out = path_log / 'download_duplicate_counts' / f'_DownloadedFiles_duplicates_{date.today().strftime("%Y-%m-%d")}.xlsx'
    count_log_duplicates(file_in, file_out, file_theme)
    

