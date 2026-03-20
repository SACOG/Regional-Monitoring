

import pandas as pd
from pathlib import Path


import sys
# sys.path.append(str(Path(__file__).parent.parent/'config'))
sys.path.append(str(Path.home()/'Documents'/'Projects'/'Regional-Monitoring'/'Indicator_Gen'/'Products'/'RHNA'/'config'))
import rhna
yaml_file = rhna.load_yaml()


PATH_DATA = Path(yaml_file['Path_Data'])
# INDICATOR = Path(__file__).stem
INDICATOR = 'POPEMP_26'
params = yaml_file[INDICATOR]

PATH_MNR = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')


df_sub = pd.read_excel(PATH_DATA/f'RHNA_{INDICATOR} Places SUBJECT5.xlsx', sheet_name='Places')
df_dec = pd.read_csv(PATH_MNR/f'RHNA_{INDICATOR}_Places_DEC_raw.csv')

df_dec = df_dec[df_dec['NAME'].str.contains('Folsom')]
df_dec

df_sub = df_sub[df_sub['NAME']=='Folsom']
