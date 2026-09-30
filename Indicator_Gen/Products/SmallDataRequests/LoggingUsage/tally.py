

import pandas as pd
from pathlib import Path
import sys
import re
from tqdm import tqdm



def clean_file_name(file_):
    try:
        file_ = re.search(r'[^/]+$', file_).group()
        file_ = file_.replace('+', ' ')
        return file_
    except Exception as e:
        e
        return None
    
def keep_str_until_num(workbook_name):
    try:
        match = re.match(r'^\D*\d', workbook_name)
        if match:
            return match.group()
    except Exception as e:
        e
        return None


# Remove anything after/before specified string, use regular expression
# # (currently set to remove everything after/before the first period)
def re_remove_post(x, exp = ' '):
    try:
        x.split(exp, 1)[0]
    except Exception as e:
        e
    return x
    
def re_remove_pre(x, exp = ' '):
    try:
        x.split(exp, 1)[1]
    except Exception as e:
        e
    return x
    


'''
User defined functions to read in log file of Monitoring and Reporting Dashboard
It reads in the organized download log file, then tallies the downloads by:
Theme, Page, Indicator, and Geography

User must define file path to import cleaned downloads log file and file path to export results
The results are exported to the user defined file location as a csv file

If the code fails, it's most likely because you don't have the file paths defined correctly (using the 'pathlib' library)
Check for updated packages and that file paths are assigned correctly if running into errors
'''


def count_log_theme(downloads_file, themes_file):
    
    try:

        # Read in txt file
        df = pd.read_csv(downloads_file, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month
        df['file_name'] = df['file_'].apply(clean_file_name)
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        # Merge themes onto workbooks
        df_map = pd.read_csv(themes_file)
        df = df.merge(df_map, on='Indicator', how='left')

        # Calculate counts by theme
        df_theme = df.copy()
        df_theme = df_theme[['year', 'month', 'Theme']].value_counts().reset_index()
        df_theme = df_theme.sort_values(['year', 'month', 'count'], ascending=[False, False, False])
        df_theme = df_theme.reset_index(drop=True)

        return df_theme

    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"Error occurred on line: {exc_tb.tb_lineno}")



def count_log_page(downloads_file, themes_file):
    
    try:

        # Read in txt file
        df = pd.read_csv(downloads_file, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month

        df['file_name'] = df['file_'    ].apply(clean_file_name   )
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        # Merge themes onto workbooks
        df_map = pd.read_csv(themes_file)
        df = df.merge(df_map, on='Indicator', how='left')

        # Counts by page
        df_page = df.copy()
        df_page = df_page[['year', 'month', 'Page']].value_counts().reset_index()
        df_page = df_page.sort_values(['year', 'month', 'count'], ascending=[False, False, False])
        df_page = df_page.reset_index(drop=True)

        return df_page

    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"Error occurred on line: {exc_tb.tb_lineno}")



def count_log_indicator(downloads_file):
    
    try:

        # Read in txt file
        df = pd.read_csv(downloads_file, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month

        df['file_name'] = df['file_'    ].apply(clean_file_name   )
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        # Counts by indicator
        df_indicator = df.copy()
        df_indicator = df_indicator[['year', 'month', 'Indicator']].value_counts().reset_index()
        df_indicator = df_indicator.sort_values(['year', 'month', 'count'], ascending=[False, False, False])
        df_indicator = df_indicator.reset_index(drop=True)

        return df_indicator

    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"Error occurred on line: {exc_tb.tb_lineno}")



def count_log_geography(downloads_file):
    
        # Read in txt file
        df = pd.read_csv(downloads_file, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month

        df['file_name'] = df['file_'    ].apply(clean_file_name   )
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        path_geo = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data')

        for file_name in tqdm(df['file_name'].unique()):
            try:
                tqdm.write(file_name)
                path_file = path_geo / file_name
                df_excel = pd.ExcelFile(path_file)
                sheet_name = df_excel.sheet_names[0]
                df_about = pd.read_excel(path_file, sheet_name=sheet_name)
                df_about.columns = ['Indicator', 'Description']
                geography = df_about[df_about['Indicator'] == 'Geography']['Description'].values[0]
                df.loc[df['file_name'] == file_name, 'Geography'] = geography
            except Exception as e:
                print(e)
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(f"Error occurred on line: {exc_tb.tb_lineno}")


        # Counts by geography
        df_geo = df.copy()
        df_geo = df_geo[['year', 'month', 'Geography']].value_counts().reset_index()
        df_geo = df_geo.sort_values(['year', 'month', 'count'], ascending=[False, False, False])
        df_geo = df_geo.reset_index(drop=True)

        return df_geo


def count_log_days(downloads_file):
    
    try:

        # Read in txt file
        df = pd.read_csv(downloads_file, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month

        df['file_name'] = df['file_'    ].apply(clean_file_name   )
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        # Counts by indicator
        df_by_date = df.copy()
        df_by_date = df_by_date[['date_', 'file_name']].value_counts().reset_index()
        df_by_date = df_by_date.sort_values(['date_', 'file_name'], ascending=[False, True])
        df_by_date = df_by_date.reset_index(drop=True)

        return df_by_date

    except Exception as e:
        print(e)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        print(f"Error occurred on line: {exc_tb.tb_lineno}")


