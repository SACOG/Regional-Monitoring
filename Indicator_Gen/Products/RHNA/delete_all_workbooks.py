
## Importing packages ----

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
import os
from tqdm import tqdm
import time

## Setting file paths ---

user = getpass.getuser()
path_users = Path.home()


# path_out = Path(r'C:\Users\jfontes\Documents\Projects\General\RHNA\Final Products')
# path_out = Path('I:\Projects\Josh\RHNA\Final Products')


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
        time.sleep(5)
        path_juris = path_county / jurisdiction
        file_to_delete = path_juris / f'RHNA_{jurisdiction}.xlsx'
        try:
            os.remove(file_to_delete)
        except:
            pass