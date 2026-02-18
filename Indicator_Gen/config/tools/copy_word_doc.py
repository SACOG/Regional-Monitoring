

'''Tool to copy word documents from one folder to another'''

print(); print()


import shutil
from pathlib import Path



FOLDER_SOURCE = Path.home()/'Documents'/'Projects'/'Local'/'RHNA'/'Final Products'
FOLDER_SP   = Path.home()/'Sacramento Area Council of Governments'/'Regional Monitoring and Reporting - Documents'/'Products'/'RHNA'/'Cycle7'/'Final Products'


if __name__=='__main__':

    for folder in FOLDER_SOURCE.iterdir():

        county = folder.stem; print(county)
        path_county = FOLDER_SOURCE / county
        print()

        for folder in path_county.iterdir():
            
            jurisdiction = folder.stem; print(jurisdiction)

            folder_source = path_county/jurisdiction
            folder_copy = FOLDER_SP/county/jurisdiction

            file_source = folder_source/f'RHNA_{jurisdiction}.docx'
            shutil.copy2(file_source, folder_copy)

            file_source_tables = folder_source/f'RHNA_{jurisdiction}_tables_and_plots.docx'
            shutil.copy2(file_source_tables, folder_copy)


        print("Files copied successfully!"); print(); print()


