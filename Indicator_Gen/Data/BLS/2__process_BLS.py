

# Workspace ----------------------------------------------------------------------------------------------------------------------------------


import numpy as np
import pandas as pd
from pathlib import Path
from IPython.display import display
import sys

sys.path.append(str(Path(__file__).parent.parent.parent/'config'))
import functions as func

sys.path.append(str(Path(__file__).parent/'config'))
import pre
import post



PATH_CONFIG0 = Path(__file__).parent.parent.parent / 'config'
PATH_CONFIG  = Path(__file__).parent / 'config'

FILE_API = PATH_CONFIG / 'api_key.txt'
FILE_AREA = PATH_CONFIG0 / 'area_codes.xlsx'
FILE_CPI = PATH_CONFIG0 / 'CPI_IAF.xlsx'
FILE_INPUTS = PATH_CONFIG / 'bls.xlsx'


# SharePoint OneDrive paths
PATH_SERVER = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data')
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\BLS')





# Main ----------------------------------------------------------------------------------------------------------------------------------


RERUN=False
EXPORT=False
SERVER=False


if __name__ == '__main__':

    # Rerun prep work to read in census data collected in step 1
    with open(PATH_CONFIG / 'api_key.txt', 'r') as file:
        api_key = file.read()

    yaml_bls = pre.load_yaml()
    params = pre.api_request_params(yaml_bls, RERUN)

    sample      = 'BLS'
    project     = params['Project'        ]
    indicator   = params['Indicator'      ]
    geography   = params['Geography'      ]
    survey      = params['Survey'         ]
    percentages = params['Percentages'    ]
    export_loc  = params['Export Location']

    file_in = PATH_ORIG / pre.set_download_name(indicator, geography)
    df_bls = pd.read_csv(file_in)
    display(df_bls.head())

    # Cleaning for each indicator
    df_bls, df_series_area = post.proc_bls(df_bls, params, yaml_bls)

    if indicator == 'Jobs_1':
        if geography == 'MSA':
            df_bls1, df_bls2 = post.jobs_1(df_bls, percentages, geography)
        else:
            df_bls1 = post.jobs_1(df_bls, percentages, geography)
    if indicator == 'Jobs_2':
        if geography == 'MSA':
            df_bls1, df_bls2 = post.jobs_2(df_bls, percentages, geography, df_series_area)
        else:
            df_bls1 = post.jobs_2(df_bls, percentages, geography, df_series_area)
    if indicator == 'Jobs_3':
        if geography == 'MSA':
            df_bls1, df_bls2 = post.jobs_3(df_bls, geography)
        else:
            df_bls1 = post.jobs_3(df_bls, geography)
    if indicator == 'Labor_2':
        df_bls1 = post.labor_2(df_bls)


    # Update overall about documentations workbook
    params={
        'estimate': survey
            , 'indicator': indicator
            , 'start_year': np.min(params['Years'])
            , 'end_year': np.max(params['Years'])
            , 'sample': sample
            , 'moe_thresh': None
            , 'geo': geography
        }
    df_about = func.write_about(params)
    display(df_about)
    # with pd.ExcelWriter(FILE_ABOUT, mod='a', engine='openpyxl', if_sheet_exists='replace') as writer:
    #     df_about.to_excel(writer, index=False, sheet_name=indicator, header=False)

    export_loc = Path.home() / export_loc

    if SERVER:
        paths = [export_loc, Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")]
    else:
        paths = [export_loc]

    end = ''
    # end = f'_{size_code}_{owner_code}.csv'
    workbook_name = f"{indicator} {geography} {sample} {survey}{end}.xlsx"


    if EXPORT:
        for path_ in paths:
            path_ = path_ / workbook_name
            
            print()
            print(f"Excel files exported here:  {path_}")
            print(f"Name of workbook:  {workbook_name}")
            print()
        
            if indicator == 'Jobs_1':
                if geography == 'MSA':
                    with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                        df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                        df_bls1 .to_excel(writer, index=False, sheet_name=geography            )
                        df_bls2 .to_excel(writer, index=False, sheet_name='SACOG'              )
                else:
                    with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                        df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                        df_bls1 .to_excel(writer, index=False, sheet_name=geography            )
            if indicator == 'Jobs_2':
                with pd.ExcelWriter(path_, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df_bls1 .to_excel(writer, index=False, sheet_name=geography            )
                if geography == 'MSA':
                    workbook_name = f"{indicator} MPO {sample} {survey}.xlsx"
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                    path_ = path_.parent / workbook_name
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
breakpoint()


