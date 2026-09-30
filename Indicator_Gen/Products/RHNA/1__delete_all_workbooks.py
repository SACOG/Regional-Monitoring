

from pathlib import Path
import os
from tqdm import tqdm
import time


LOCAL=True
IDRIVE=False
SHAREPOINT=False


if __name__ == '__main__':

    
    if LOCAL:
        path_out = Path(r'C:\Users\jfontes\Documents\Projects\Local\RHNA\Final Products')

    if IDRIVE:
        path_out = Path('I:\Projects\Josh\RHNA\Final Products')

    if SHAREPOINT:
        path_out = Path.home()/'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents'/'Products'/'RHNA'/'Cycle7'/'Final Products'

    print('\n'*2)
    counties = os.listdir(path_out)
    for county in counties:
        print('\n'*2)
        print(county)
        print()
        path_county = path_out / county
        jurisdictions = os.listdir(path_county)
        for jurisdiction in tqdm(jurisdictions):
            time.sleep(5)
            path_juris = path_county / jurisdiction
            file_to_delete = path_juris / f'RHNA_{jurisdiction}.xlsx'
            try:
                os.remove(file_to_delete)
            except Exception as e:
                print('How exceptional!', e)