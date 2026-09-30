


'''
This script copies the EDD tradeable Sectors file from the I drive over to the monitoring site
'''



# Setup --------------------------------------------------------------------------------------------------------------------


from pathlib import Path

import pandas as pd
from tqdm import tqdm

print('\n'*2)


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

    print()
    print(f"The copy of the excel workbook '{file_copy}' has been updated with the sheets from '{file_master}'.")
    print('\n'*2)




# Main ----------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    file_master = Path(r'I:\Projects\Josh\Regional Monitoring\Employment Inventory\Data')  / 'Jobs_6 Tradeable Sectors.xlsx'
    file_copy1   = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data') / 'Jobs_6 Tradeable Sectors.xlsx'
    file_copy2   = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\Economy\Jobs\Jobs_6 Tradeable') / 'Jobs_6 Tradeable Sectors.xlsx'

    update_excel_copy(file_master, file_copy1)
    update_excel_copy(file_master, file_copy2)
