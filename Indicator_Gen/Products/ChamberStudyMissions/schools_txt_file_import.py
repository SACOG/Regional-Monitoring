




## Packages ---
import numpy as np
import pandas as pd
import getpass
from pathlib import Path
import os
import re
from tqdm import tqdm
from datetime import date
from datetime import datetime
import time
import functools as ft
from IPython.display import display
pd.set_option('display.max_columns', None)


## File paths ---

user = getpass.getuser()
path_users = Path.home()

path_sp = path_users / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_raw = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'Census'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'
path_csm = path_prod / 'Chamber Study Missions' / date.today().strftime('%Y') / 'Hispanic Chamber of Commerce'
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_code    = path_git / 'Data' / 'Census'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'
path_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")


## User defined functions ---

path_func = path_config0 / 'Functions.py'
path_func_census = path_config / 'census_functions.py'

with path_func.open("r") as f:
    exec(f.read())

with path_func_census.open("r") as f:
    exec(f.read())


export=False


## Processing ----

table_id = '3A'


url_edu24 = "https://www3.cde.ca.gov/demo-downloads/acgr/acgr24.txt"
df_edu24 = pd.read_csv(url_edu24, sep = '\t')
# display(df_edu24)


url_edu22 = "https://www3.cde.ca.gov/demo-downloads/acgr/acgr19.txt"
df_edu22 = pd.read_csv(url_edu22, sep = '\t')
# display(df_edu22)

df_edu = pd.concat([df_edu24, df_edu22])
print(df_edu.columns)

df_edu = df_edu[df_edu['ReportingCategory'].isin(['RH', 'RW'])]
df_edu = df_edu[df_edu['AggregateLevel'] == 'C']
df_edu = df_edu[df_edu['CountyName'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba'])]
df_edu['CohortStudents'                      ] = df_edu['CohortStudents'                      ].replace('*', '0').astype(int)
df_edu['Regular HS Diploma Graduates (Count)'] = df_edu['Regular HS Diploma Graduates (Count)'].replace('*', '0').astype(int)
df_edu["Met UC/CSU Grad Req's (Count)"] = df_edu["Met UC/CSU Grad Req's (Count)"].replace('*', '0').astype(int)

df_edu1 = df_edu.groupby(['AcademicYear', 'CountyName', 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
df_edu2 = df_edu.groupby(['AcademicYear'              , 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
df_edu2['CountyName']='SACOG'

df_edu = pd.concat([df_edu1, df_edu2])

df_edu['Graduated_pct' ] = df_edu['Graduated' ]/df_edu['TotalStudents']
df_edu['Met_UC_req_pct'] = df_edu['Met_UC_req']/df_edu['Graduated'    ]

df_edu1 = df_edu.pivot_table(index=['AcademicYear', 'CountyName'], columns='ReportingCategory', values='Graduated_pct').reset_index()
df_edu1 = df_edu1.rename(columns={'RH':'Graduating Hispanic_pct', 'RW':'Graduating White_pct'})

df_edu2 = df_edu.pivot_table(index=['AcademicYear', 'CountyName'], columns='ReportingCategory', values='Met_UC_req_pct').reset_index()
df_edu2 = df_edu2.rename(columns={'RH':'Met_UC_req Hispanic_pct', 'RW':'Met_UC_req White_pct'})

df_edu = df_edu1.merge(df_edu2)


df_edu['Sort'] = pd.Categorical(df_edu['CountyName'], ['El Dorado'
                                                        , 'Placer'
                                                        , 'Sacramento'
                                                        , 'Sutter'
                                                        , 'Yolo'
                                                        , 'Yuba'
                                                        , 'SACOG'
                                                    ])
df_edu = df_edu.sort_values(['AcademicYear', 'Sort'], ascending=[False, True])
df_edu = df_edu.drop('Sort', axis=1)
df_edu = df_edu.reset_index(drop=True)

display(df_edu)


## Exporting ---

if export:
    workbook = f'post2.xlsx'
    file_out = path_csm / 'post' / workbook

    with pd.ExcelWriter(file_out,mode='a',engine='openpyxl',if_sheet_exists='replace') as writer:
        df_edu.to_excel(writer, sheet_name=table_id, index=False)


