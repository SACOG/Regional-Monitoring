


# Workspace ----------------------------------------------------------------------------------------------------------------

import pandas as pd
from pathlib import Path
from datetime import date
import re
from tqdm import tqdm

PATH_MAIN = Path(r'I:\Projects\Josh\Regional Monitoring')
PATH_LOG = PATH_MAIN / 'LoggingUsage'


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
    
# Remove anything after specified string, use regular expression (currently set to remove everything after the first period)
def re_remove_post(x, exp = ' '):
    try: x.split(exp, 1)[0]
    except: pass
    return x
    
def re_remove_pre(x, exp = ' '):
    try: x.split(exp, 1)[1]
    except: pass
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


def count_log_theme(FILE_IN, FILE_THEME):
    
    try:

        # Read in txt file
        df = pd.read_csv(FILE_IN, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month
        df['file_name'] = df['file_'].apply(clean_file_name)
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        # Merge themes onto workbooks
        df_map = pd.read_csv(FILE_THEME)
        df = df.merge(df_map, on='Indicator', how='left')

        # Calculate counts by theme
        df_theme = df.copy()
        df_theme = df_theme[['year', 'month', 'Theme']].value_counts().reset_index()
        df_theme = df_theme.sort_values(['year', 'month', 'count'], ascending=[False, False, False])
        df_theme = df_theme.reset_index(drop=True)

        return df_theme

    except Exception as e: print(e)



def count_log_page(FILE_IN, FILE_THEME):
    
    try:

        # Read in txt file
        df = pd.read_csv(FILE_IN, sep=' ', names=['date_', 'file_'])
        
        df['date_'] = pd.to_datetime(df['date_'])
        df['year' ] = df['date_'].dt.year
        df['month'] = df['date_'].dt.month

        df['file_name'] = df['file_'    ].apply(clean_file_name   )
        df['Indicator'] = df['file_name'].apply(keep_str_until_num)

        # Merge themes onto workbooks
        df_map = pd.read_csv(FILE_THEME)
        df = df.merge(df_map, on='Indicator', how='left')

        # Counts by page
        df_page = df.copy()
        df_page = df_page[['year', 'month', 'Page']].value_counts().reset_index()
        df_page = df_page.sort_values(['year', 'month', 'count'], ascending=[False, False, False])
        df_page = df_page.reset_index(drop=True)

        return df_page

    except Exception as e: print(e)



def count_log_indicator(FILE_IN):
    
    try:

        # Read in txt file
        df = pd.read_csv(FILE_IN, sep=' ', names=['date_', 'file_'])
        
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

    except Exception as e: print(e)



def count_log_geography(FILE_IN):
    
        # Read in txt file
        df = pd.read_csv(FILE_IN, sep=' ', names=['date_', 'file_'])
        
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
            except Exception as e: print(e)


        # Counts by geography
        df_geo = df.copy()
        df_geo = df_geo[['year', 'month', 'Geography']].value_counts().reset_index()
        df_geo = df_geo.sort_values(['year', 'month', 'count'], ascending=[False, False, False])
        df_geo = df_geo.reset_index(drop=True)

        return df_geo





# Main ----------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    if '01' in date.today().strftime("%Y%m"):
        month_in_review = f'{int(date.today().strftime("%Y"))-1}12'
    else:
        month_in_review = str(int(date.today().strftime("%Y%m"))-1)

    FILE_THEME = PATH_MAIN / 'Indicator_Theme_Mapping.csv'
    FILE_IN = PATH_LOG / 'download_log_files' / '_DownloadedFiles.txt'
    FILE_OUT = PATH_LOG / 'download_duplicate_counts' / f'MnR_logging__{month_in_review}.xlsx'


    df_theme     = count_log_theme(FILE_IN, FILE_THEME)
    df_page      = count_log_page(FILE_IN, FILE_THEME)
    df_indicator = count_log_indicator(FILE_IN)
    df_geo       = count_log_geography(FILE_IN)
    

    with pd.ExcelWriter(FILE_OUT, engine='xlsxwriter') as writer:
        df_theme    .to_excel(writer, index=False, sheet_name='Theme'    )
        df_page     .to_excel(writer, index=False, sheet_name='Page'     )
        df_indicator.to_excel(writer, index=False, sheet_name='Indicator')
        df_geo      .to_excel(writer, index=False, sheet_name='Geography')
    print(); print(f'Successfully exported results to {FILE_OUT}'); print()

    

