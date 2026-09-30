


# Setup ----------------------------------------------------------------------------------------------------------------

import pandas as pd
from pathlib import Path
import time
import sys
sys.path.append(Path(__file__).parent)
import fetch
import tally



PATH_MAIN = Path(r'I:\Projects\Josh\Regional Monitoring')
PATH_OUT = PATH_MAIN / 'LoggingUsage'



print('\n'*2)


# Main ----------------------------------------------------------------------------------------------------------------------------




if __name__ == '__main__':

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

    

