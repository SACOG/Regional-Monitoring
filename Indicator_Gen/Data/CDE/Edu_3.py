


# Workspace ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


EXPORT=False


import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm
import random
import time
from IPython.display import display
pd.set_option('display.max_columns', None)


PATH_GIT = Path.cwd().parent.parent
PATH_CONFIG0 = PATH_GIT / 'config'

# SharePoint OneDrive paths
PATH_SP = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
PATH_MAIN = PATH_SP / 'Data'

PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\BEA')
FILE_IN = PATH_ORIG / 'CAGDP9' / 'CAGDP9_MSA_2001_2023.csv'

import sys
sys.path.append(str(PATH_CONFIG0))
import functions as func





# Main ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
        
    dt_url = {
        2024:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr24.txt",
        2023:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr23-v2.txt",
        2022:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr22-v3.txt",
        2021:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr21.txt",
        2020:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr20.txt",
        2019:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr19.txt",
        2018:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr18.txt",
        2017:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr17.txt"
    }

    list_df = []
    print(); print()
    for year, url in tqdm(dt_url.items()):
        tqdm.write(str(year))
        tqdm.write(url)
        tqdm.write('')
        df_edu = pd.read_csv(url, sep = '\t')
        df_edu['Year'] = year
        list_df.append(df_edu)

        rand_time = random.randint(1, 4)
        time.sleep(rand_time)



    df_edu = pd.concat(list_df)
    print()

    display(df_edu)

    year_start = df_edu['Year'].min()
    year_end   = df_edu['Year'].max()
    df_edu = df_edu.drop('Year', axis=1)


    print()
    print(df_edu.columns)
    print(); print()


    df_edu = df_edu[df_edu['CountyName'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba'])]
    df_edu = df_edu[df_edu['ReportingCategory'].isin(['RB', 'RA', 'RH', 'RW', 'SS', 'TA'])]

    df_edu['CohortStudents'                      ] = df_edu['CohortStudents'                      ].replace('*', '0').astype(int)
    df_edu['Regular HS Diploma Graduates (Count)'] = df_edu['Regular HS Diploma Graduates (Count)'].replace('*', '0').astype(int)
    df_edu["Met UC/CSU Grad Req's (Count)"] = df_edu["Met UC/CSU Grad Req's (Count)"].replace('*', '0').astype(int)

    dt_race_eth = {
        'RB':'Black',
        'RA':'Asian',
        'RH':'Hispanic',
        'RW':'White',
        'SS':'Socioeconomically Disadvantaged',
        'TA':'Total'
    }
    df_edu['ReportingCategory'] = df_edu['ReportingCategory'].map(dt_race_eth)

    dt_years = {
        '2016-17':'2016-2017',
        '2017-18':'2017-2018',
        '2018-19':'2018-2019',
        '2019-20':'2019-2020',
        '2020-21':'2020-2021',
        '2021-22':'2021-2022',
        '2022-23':'2022-2023',
        '2023-24':'2023-2024'
    }
    df_edu['AcademicYear']=df_edu['AcademicYear'].map(dt_years)


    # By County
    df = df_edu.copy()
    df = df[df['AggregateLevel'] == 'C']
    df1 = df.groupby(['AcademicYear', 'CountyName', 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
    df2 = df.groupby(['AcademicYear'              , 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
    df2['CountyName']='SACOG'
    df_counties = pd.concat([df1, df2])
    df_counties['Graduated_pct' ] = df_counties['Graduated' ]/df_counties['TotalStudents']
    df_counties['Met_UC_req_pct'] = df_counties['Met_UC_req']/df_counties['Graduated'    ]
    df_counties['Sort'] = pd.Categorical(df_counties['CountyName'], ['El Dorado'
                                                                        , 'Placer'
                                                                        , 'Sacramento'
                                                                        , 'Sutter'
                                                                        , 'Yolo'
                                                                        , 'Yuba'
                                                                        , 'SACOG'
                                                                    ])
    df_counties = df_counties.sort_values(['AcademicYear', 'Sort'], ascending=[False, True])
    df_counties = df_counties.drop('Sort', axis=1)
    df_counties = df_counties.reset_index(drop=True)
    print('By County:')
    display(df_counties)
    print(); print()


    # By District
    df_district = df_edu.copy()
    df_district = df_district[df_district['AggregateLevel'] == 'D']
    df_district = df_district.groupby(['AcademicYear', 'CountyName', 'DistrictName', 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
    df_district['Graduated_pct' ] = df_district['Graduated' ]/df_district['TotalStudents']
    df_district['Met_UC_req_pct'] = df_district['Met_UC_req']/df_district['Graduated'    ]
    df_district['Sort'] = pd.Categorical(df_district['CountyName'], ['El Dorado'
                                                                        , 'Placer'
                                                                        , 'Sacramento'
                                                                        , 'Sutter'
                                                                        , 'Yolo'
                                                                        , 'Yuba'
                                                                        , 'SACOG'
                                                                    ])
    df_district = df_district.sort_values(['AcademicYear', 'Sort', 'DistrictName'], ascending=[False, True, True])
    df_district = df_district.drop('Sort', axis=1)
    df_district = df_district.reset_index(drop=True)
    print('By School District:')
    display(df_district)
    print(); print()


    if EXPORT:

        indicator='Edu_3'
        sample_type='CDE'
        geography='Counties and School Districts'
        file_out = PATH_SERVER / f'{indicator} A-G v2.xlsx'

        df_about = func.write_about(sample_type  = sample_type
                                    , indicator  = indicator
                                    , year_start = year_start
                                    , year_end   = year_end
                                    , geography  = geography)
        display(df_about)


        if os.path.isfile(file_out):
            with pd.ExcelWriter(file_out,mode='a',engine='openpyxl',if_sheet_exists='replace') as writer:
                df_about   .to_excel(writer, index=False, sheet_name='About', header=False)
                df_counties.to_excel(writer, sheet_name='County'  , index=False)
                df_district.to_excel(writer, sheet_name='District', index=False)
        else:
            with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
                df_about   .to_excel(writer, index=False, sheet_name='About', header=False)
                df_counties.to_excel(writer, sheet_name='County'  , index=False)
                df_district.to_excel(writer, sheet_name='District', index=False)


