


'''
This script updates the "About Indicators.xlsx" file on the main Data folder of the MnR SP page with
the working copy from the Process Map folder
'''
print(); print()


# update = 'About'
update = 'RHNA'


## Setup ================================================================================================


## Packages ---

import pandas as pd
import getpass
from pathlib import Path
import os
import xlwt
from xlwt.Workbook import *
from pandas import ExcelWriter
import xlsxwriter
import shutil
from tqdm import tqdm
import time

## User defined functions ---


def update_excel_copy(file_master, file_copy):

    # Load the master workbook
    # Create a writer object for the copy workbook
        # Iterate through each sheet in the master workbook
            # Load the sheet into a DataFrame
            # Write the DataFrame to the copy workbook

    workbook_master = pd.ExcelFile(file_master)
    
    with pd.ExcelWriter(file_copy, engine='openpyxl') as writer:

        for sheet_name in tqdm(workbook_master.sheet_names):
            df = workbook_master.parse(sheet_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(); print(); print()
    print(f"The copy of the excel workbook '{file_copy}' has been updated with the sheets from '{file_master}'.")
    print(); print(); print()



## Main ================================================================================================


if __name__ == '__main__':

    ## File paths
    user = getpass.getuser()
    path_users = Path.home()

    path_sp = path_users / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents'

  
    ## (1)
    if update == 'About':

        path_in = path_sp  / 'Process Revamp' / 'Task 6. Process Map'
        path_out = path_sp / 'Data'

        file_master = path_in  / 'About Indicators.xlsx'
        file_copy   = path_out / 'About Indicators.xlsx'
        update_excel_copy(file_master, file_copy)

    ## (2)
    if update == 'RHNA':
        dict_ = {
            'El Dorado' : ['Placerville', 'South Lake Tahoe', 'Unincorporated'],
            'Placer'    : ['Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville', 'Unincorporated'],
            'Sacramento': ['Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento', 'Unincorporated'],
            'Sutter'    : ['Live Oak', 'Yuba City', 'Unincorporated'],
            'Yolo'      : ['Davis', 'West Sacramento', 'Winters', 'Woodland', 'Unincorporated'],
            'Yuba'      : ['Marysville', 'Wheatland', 'Unincorporated']
        }

        for county in dict_.keys():

            print(); print(county); print()

            for jurisdiction in tqdm(dict_[county], position=0):

                tqdm.write(jurisdiction)

                path_in = Path(r'C:\Users\jfontes\Documents\Projects\General\RHNA\Final Products')
                
                file_master = path_in / county / jurisdiction / f'RHNA_{jurisdiction}.xlsx'
                file_copy   = path_sp / 'Products' / 'RHNA' / 'Cycle7' / 'Final Products' / county / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

                shutil.copy(file_master, file_copy)

                time.sleep(20)


