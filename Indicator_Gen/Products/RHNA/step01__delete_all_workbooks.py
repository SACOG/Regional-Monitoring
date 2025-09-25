




import getpass
from pathlib import Path
import os
from tqdm import tqdm
import time




if __name__ == '__main__':


    local=False
    idrive=False
    sharepoint=True



    if local:
        path_out = Path(r'C:\Users\jfontes\Documents\Projects\General\RHNA\Final Products')

    if idrive:
        path_out = Path('I:\Projects\Josh\RHNA\Final Products')

    if sharepoint:
        user = getpass.getuser()
        path_users = Path.home()
        path_sp   = path_users / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents'
        path_prod = path_sp    / 'Products' / 'RHNA'
        path_out = path_prod / 'Cycle7' / 'Final Products'


    ## Clear files out ---

    counties = os.listdir(path_out)
    for county in counties:
        print(county)
        path_county = path_out / county
        jurisdictions = os.listdir(path_county)
        for jurisdiction in tqdm(jurisdictions):
            time.sleep(4)
            path_juris = path_county / jurisdiction
            file_to_delete = path_juris / f'RHNA_{jurisdiction}.xlsx'
            try:
                os.remove(file_to_delete)
            except:
                pass