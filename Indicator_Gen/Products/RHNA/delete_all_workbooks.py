
## Importing packages ----

import numpy as np
import pandas as pd
import getpass
from pathlib import Path
import os
from tqdm import tqdm


## Setting file paths ---

user = getpass.getuser()
path_users = Path.home()
path_out = Path(r'C:\Users\jfontes\Documents\Projects\General\RHNA\Final Products')
# path_out = Path('I:\Projects\Josh\RHNA\Final Products')


## Clear files out ---

counties = os.listdir(path_out)
for county in counties:
    print(county)
    path_county = path_out / county
    jurisdictions = os.listdir(path_county)
    for jurisdiction in tqdm(jurisdictions):
        path_juris = path_county / jurisdiction
        file_to_delete = path_juris / f'RHNA_{jurisdiction}.xlsx'
        try:
            os.remove(file_to_delete)
        except:
            pass