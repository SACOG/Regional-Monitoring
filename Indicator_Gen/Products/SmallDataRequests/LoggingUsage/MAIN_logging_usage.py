


'''

(1) Open the "M&R Site Hits & Downloads.xlsx" workbook located on SharePoint https://sacog.sharepoint.com/:x:/r/sites/RegionalMonitoringandReporting/_layouts/15/Doc.aspx?sourcedoc=%7BA7B4C77B-60E5-44E9-9BBE-F1B86C53E34D%7D&file=M%26R%20Site%20Hits%20%26%20Downloads.xlsx&action=default&mobileredirect=true
(2) Create new tab in "M&R Site Hits & Downloads.xlsx" for the month/year being logged (i.e. "June 2026") then duplicate structure of previous tabs
(3) Run this file in terminal
(4) Open results here I:\Projects\Josh\Regional Monitoring\LoggingUsage\download_duplicate_counts for most recent month
(5) For the tables Downloaded Files, Theme, Page, Indicator, and Geography -> copy over logging data results to "M&R Site Hits & Downloads.xlsx" for the most recent month
(6) For Site visits (ESRI) -> Sign on to AGOL, click on Regional Indicators Experience Builder app (under My Content - Organization), click on Usage, select custom date range to get desired month (i.e. June 1 - June 30), then copy over the number under "Item views"
(7) Google Analytics:  Choose site, filter dates, under reports:  Engagement -> Pages and screens

'''



# Setup --------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
import time
import pandas as pd
import sys
sys.path.append(Path(__file__).parent)
import fetch
import tally


PATH_LOGS = Path(r'\\webmapping-svr\c$\inetpub\logs\LogFiles\W3SVC1')
PATH_I = Path(r'I:\Projects\Josh\Regional Monitoring\LoggingUsage\download_log_files')


PATH_MAIN = Path(r'I:\Projects\Josh\Regional Monitoring')
PATH_OUT = PATH_MAIN / 'LoggingUsage'


print('\n'*2)




# Main ----------------------------------------------------------------------------------------------------------------------



if __name__ == '__main__':


    ## 1__fetch_log_files.py ---

    log_files = fetch.fetch_log_files(PATH_LOGS)
    fetch.write_downloaded_files_to_txt(log_files)
    fetch.archive_downloads_list(PATH_I)


    ## 2__count_site_usage.py ---

    print('Tallying downloaded files for site usage tracking...')
    print()
    time.sleep(5)

    themes_file = PATH_MAIN / 'Indicator_Theme_Mapping.csv'
    downloads_file = PATH_OUT / 'download_log_files' / '_DownloadedFiles.txt'

    df_by_date   = tally.count_log_days(downloads_file)
    df_theme     = tally.count_log_theme(downloads_file, themes_file)
    df_page      = tally.count_log_page(downloads_file, themes_file)
    df_indicator = tally.count_log_indicator(downloads_file)
    df_geo       = tally.count_log_geography(downloads_file)
    

    file_out = PATH_OUT / 'download_duplicate_counts' / f'MnR_logging__20{fetch.get_prev_month()}.xlsx'
    with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
        df_by_date  .to_excel(writer, index=False, sheet_name='Days'     )
        df_theme    .to_excel(writer, index=False, sheet_name='Theme'    )
        df_page     .to_excel(writer, index=False, sheet_name='Page'     )
        df_indicator.to_excel(writer, index=False, sheet_name='Indicator')
        df_geo      .to_excel(writer, index=False, sheet_name='Geography')

    print()
    print(f'Successfully exported results to {file_out}')
    print()

    