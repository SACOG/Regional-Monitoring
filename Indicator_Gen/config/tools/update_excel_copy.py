


'''
This script updates the "About Indicators.xlsx" file on the main Data folder of the MnR SP page with
the working copy from the Process Map folder
'''
print(); print()


# UPDATE = 'About'
UPDATE = 'RHNA'



# Setup ----------------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
from pathlib import Path
import shutil
from tqdm import tqdm
import time



def update_excel_copy(file_master, file_copy):

    # Load the master workbook
    # Create a writer object for the copy workbook
        # Iterate through each sheet in the master workbook
            # Load the sheet into a DataFrame
            # Write the DataFrame to the copy workbook

    workbook_master = pd.ExcelFile(file_master)
    
    with pd.ExcelWriter(file_copy, engine='openpyxl') as writer:

        for sheet_name in tqdm(workbook_master.sheet_names):
            if sheet_name == 'RISK_1':
                continue
            df = workbook_master.parse(sheet_name)
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(); print(); print()
    print(f"The copy of the excel workbook '{file_copy}' has been updated with the sheets from '{file_master}'.")
    print(); print(); print()



# Main ----------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    ## (1)
    if UPDATE == 'About':

        PATH_SP = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents'

        path_in = PATH_SP  / 'Process Revamp' / 'Task 6. Process Map'
        path_out = PATH_SP / 'Data'

        file_master = path_in  / 'About Indicators.xlsx'
        file_copy   = path_out / 'About Indicators.xlsx'
        update_excel_copy(file_master, file_copy)

    ## (2)
    if UPDATE == 'RHNA':

        PATH_LOCAL = Path(r'C:\Users\jfontes\Documents\Projects\Local\RHNA\Final Products')
        PATH_SP = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Products' / 'RHNA' / 'Cycle7' / 'Final Products' 

        dict_ = {
            # 'El Dorado' : ['Placerville', 'South Lake Tahoe', 'Unincorporated'],
            # 'Placer'    : ['Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville', 'Unincorporated'],
            # 'Sacramento': ['Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento', 'Unincorporated'],
            'Sacramento': ['Folsom'],
            # 'Sutter'    : ['Live Oak', 'Yuba City', 'Unincorporated'],
            # 'Yolo'      : ['Davis', 'West Sacramento', 'Winters', 'Woodland', 'Unincorporated'],
            # 'Yuba'      : ['Marysville', 'Wheatland', 'Unincorporated']
        }

        for county in dict_.keys():

            print(); print(county); print()

            for jurisdiction in tqdm(dict_[county], position=0):

                tqdm.write(jurisdiction)
                
                file_master = PATH_LOCAL / county / jurisdiction / f'RHNA_{jurisdiction}.xlsx'
                file_copy   = PATH_SP / county / jurisdiction / f'RHNA_{jurisdiction}.xlsx'

                shutil.copy(file_master, file_copy)

                time.sleep(20)
