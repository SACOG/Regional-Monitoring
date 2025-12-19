




RERUN=True
EXPORT=True



# Workspace ----------------------------------------------------------------------------------------------------------------------------------



import numpy as np
import pandas as pd
from pathlib import Path
from xlwt.Workbook import *
from IPython.display import display
import sys


PATH_GIT = Path(__file__).parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'BLS'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'

FILE_API = PATH_CONFIG / 'api_key.txt'
FILE_AREA = PATH_CONFIG0 / 'area_codes.xlsx'
FILE_CPI = PATH_CONFIG0 / 'CPI_IAF.xlsx'
FILE_INPUTS = PATH_CONFIG / 'bls.xlsx'

sys.path.append(str(PATH_CONFIG0))
import functions as func

sys.path.append(str(PATH_CONFIG))
import pre
import post



# SharePoint OneDrive paths
PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
PATH_MAIN = PATH_SP / 'Data'
PATH_PROD = PATH_SP / 'Products'
PATH_SERVER = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data')
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\BLS')

FILE_ABOUT = PATH_SP / 'Process Revamp' / 'Task 6. Process Map' / 'About Indicators.xlsx'





# Main ----------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':



    # Rerun prep work to read in census data collected in step 1
    with open(PATH_CONFIG / 'api_key.txt', 'r') as file:
        api_key = file.read()

    yaml_bls = pre.load_yaml()
    dt_params = pre.api_request_params(yaml_bls, RERUN)

    estimate    = 'BLS'
    indicator   = dt_params['Indicator'      ]
    geography   = dt_params['Geography'      ]
    survey      = dt_params['Survey'         ]
    percentages = dt_params['Percentages'    ]
    export_loc  = dt_params['Export Location']
    folder      = dt_params['SP Folder'      ]
    year_start = np.min(dt_params['Years'])
    year_end   = np.max(dt_params['Years'])

    file_in = PATH_ORIG / pre.set_download_name(indicator, geography)
    df_bls = pd.read_csv(file_in)
    display(df_bls.head())

    # Cleaning for each indicator
    df_bls, df_series_area = post.proc_bls(df_bls, dt_params, yaml_bls)

    if indicator == 'Jobs_1':
        df_bls1 = post.jobs_1(df_bls, percentages, geography)
    if indicator == 'Jobs_2':
        df_bls1, df_bls2 = post.jobs_2(df_bls, percentages, geography, df_series_area)
    if indicator == 'Jobs_3':
        df_bls1, df_bls2 = post.jobs_3(df_bls)
    if indicator == 'Labor_2':
        df_bls1 = post.labor_2(df_bls)


    # Update overall about documentations workbook
    df_about = func.write_about(sample_type  = survey
                                , indicator  = indicator
                                , year_start = year_start
                                , year_end   = year_end
                                , estimate   = estimate)
    display(df_about)
    # with pd.ExcelWriter(FILE_ABOUT, mod='a', engine='openpyxl', if_sheet_exists='replace') as writer:
    #     df_about.to_excel(writer, index=False, sheet_name=indicator, header=False)


    # Set file path for exporting
    paths = [PATH_MAIN / export_loc / f'{indicator} {folder}', Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")]
    # paths = [path_main / export_loc / f'{indicator} {folder}']

    end = ''
    # end = f'_{size_code}_{owner_code}.csv'
    workbook_name = f"{indicator} {geography} {estimate} {survey}{end}.xlsx"


    if EXPORT:
        for path_ in paths:
            path_ = path_ / workbook_name
            
            print(f"Excel files exported here:  {path_}");print()
            print(f"Name of workbook:  {workbook_name}");print()
        
            if indicator == 'Jobs_1':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name=geography            )
            if indicator == 'Jobs_2':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name=geography            )
                if geography == 'MSA':
                    workbook_name = f"{indicator} 'MPO' {estimate} {survey}.xlsx"
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                    with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                        df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                        df_bls2 .to_excel(writer, index=False, sheet_name='MPO'                )
            if indicator == 'Jobs_3':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False   )
                    df_bls1 .to_excel(writer, index=False, sheet_name='Government and Private')
                    df_bls2 .to_excel(writer, index=False, sheet_name='Goods and Services'    )
            
            if indicator == 'Labor_2':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name=geography            )
        
        print()
        print("Successfully exported")





