


'''
This script updates the "About Indicators.xlsx" file on the main Data folder of the MnR SP page with
the working copy from the Process Map folder
'''


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


## File paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents'
path_in = path_sp  / 'Process Revamp' / 'Task 6. Process Map'
path_out = path_sp / 'Data'


## Function ---

def main():

    # Define the file paths
    file_master = path_in  / 'About Indicators.xlsx'
    file_copy   = path_out / 'About Indicators.xlsx'

    # Load the master workbook
    # Create a writer object for the copy workbook
        # Iterate through each sheet in the master workbook
            # Load the sheet into a DataFrame
            # Write the DataFrame to the copy workbook

    master_workbook = pd.ExcelFile(file_master)
    
    with pd.ExcelWriter(file_copy, engine='openpyxl') as writer:

        for sheet_name in tqdm(master_workbook.sheet_names):
            df = master_workbook.parse(sheet_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(); print()
    print(f"The copy of the excel workbook '{file_copy}' has been updated with the sheets from '{file_master}'.")
    print(); print()


## Run ---

if __name__ == '__main__':
    main()

