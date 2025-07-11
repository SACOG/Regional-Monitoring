


## Packages ---

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
import re
from datetime import date
from IPython.display import display





## Commonly used file paths ---

user = getpass.getuser()
path_users = Path.home()

# path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
# path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'Census'
# path_main = path_sp / 'Data'
# path_prod = path_sp / 'Products'
# path_dr = path_prod / 'Small Data Requests' / date.today().strftime('%Y')
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_config0 = path_git / 'config'
# path_config  = path_code / 'config'
# path_out_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
# path_gdb = Path(r"I:/Projects/Josh/Regional Monitoring/ArcPro_v2/Data")
path_cw = Path(r'I:\Projects\Josh\Geospatial Data\crosswalks')




## Set inputs and outputs ---


# Export function
def export_to_csv(path_in, workbook_in, sheet_name, path_out, workbook_out):

    file_in = path_in / workbook_in
    df = pd.read_excel(file_in, sheet_name=sheet_name)
    
    df.columns = [x.lower() for x in df.columns]
    df.columns = [re.sub('[^\\w\\s]', '_', col.strip()) for col in df.columns]
    df.columns = [re.sub('[\s+]'    , '_', col.strip()) for col in df.columns]
    df.columns = [re.sub('\\?'      , '' , col.strip()) for col in df.columns]

    file_out = path_out / workbook_out
    print(); print(); print()
    print('Exporting here: ', path_out)
    print('Name of export: ', workbook_out)
    display(df.head())
    print(); print(); print()
    if export:
        df.to_csv(file_out, index=False)



if __name__ == '__main__':

    export=True
    path_in  = path_config0
    workbook_in = 'area_codes.xlsx'
    sheet_name = 'ZIPcodes'
    workbook_out = 'zip_codes.txt'
    path_out = path_cw

    if export:
        export_to_csv(path_in, workbook_in, sheet_name, path_out, workbook_out)



