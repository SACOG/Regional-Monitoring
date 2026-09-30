


'''
To update Edu_3:
Check https://www.cde.ca.gov/ds/ad/filesacgr.asp, for the latest school year
If there is another school year available, please add it to the "dt_url" and "dt_years" objects below
Switch EXPORT=False if doing a test run and EXPORT=True if ready to update the indicator
Then run the python script in the terminal
'''


# Setup ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm
import random
import time
from IPython.display import display

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'config'))
import functions as func


pd.set_option('display.max_columns', None)
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")




# Main ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


EXPORT=False


# Site to download data: https://www.cde.ca.gov/ds/ad/filesacgr.asp
# Add on latest school year to dt_url
# Add on the latest school year to dt_years

dt_url = {
    2025:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr25.txt",
    2024:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr24.txt",
    2023:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr23-v2.txt",
    2022:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr22-v3.txt",
    2021:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr21.txt",
    2020:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr20.txt",
    2019:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr19.txt",
    2018:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr18.txt",
    2017:"https://www3.cde.ca.gov/demo-downloads/acgr/acgr17.txt"
}

dt_years = {
    '2016-17':'2016-2017',
    '2017-18':'2017-2018',
    '2018-19':'2018-2019',
    '2019-20':'2019-2020',
    '2020-21':'2020-2021',
    '2021-22':'2021-2022',
    '2022-23':'2022-2023',
    '2023-24':'2023-2024',
    '2024-25':'2024-2025'
}

dt_race_eth = {
    'RB':'Black',
    'RA':'Asian',
    'RH':'Hispanic',
    'RW':'White',
    'SS':'Socioeconomically Disadvantaged',
    'TA':'Total'
}


if __name__ == '__main__':

    list_df = []
    print('\n'*2)
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
    display(df_edu)

    year_start = df_edu['Year'].min()
    year_end   = df_edu['Year'].max()
    df_edu = df_edu.drop('Year', axis=1)

    print('\nColumns: ', df_edu.columns)

    df_edu = df_edu[df_edu['CountyName'].isin(['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba'])]
    df_edu = df_edu[df_edu['ReportingCategory'].isin(['RB', 'RA', 'RH', 'RW', 'SS', 'TA'])]

    df_edu['CohortStudents'                      ] = df_edu['CohortStudents'                      ].replace('*', '0').astype(int)
    df_edu['Regular HS Diploma Graduates (Count)'] = df_edu['Regular HS Diploma Graduates (Count)'].replace('*', '0').astype(int)
    df_edu["Met UC/CSU Grad Req's (Count)"] = df_edu["Met UC/CSU Grad Req's (Count)"].replace('*', '0').astype(int)

    df_edu['AcademicYear'     ] = df_edu['AcademicYear'     ].map(dt_years   )
    df_edu['ReportingCategory'] = df_edu['ReportingCategory'].map(dt_race_eth)

    # By County
    df = df_edu.copy()
    df = df[df['AggregateLevel'] == 'C']
    df1 = df.groupby(['AcademicYear', 'CountyName', 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
    df2 = df.groupby(['AcademicYear'              , 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
    df2['CountyName']='SACOG'
    df_counties = pd.concat([df1, df2])
    df_counties['Graduated_pct' ] = df_counties['Graduated' ]/df_counties['TotalStudents']
    df_counties['Met_UC_req_pct'] = df_counties['Met_UC_req']/df_counties['Graduated'    ]
    df_counties['Sort'] = pd.Categorical(df_counties['CountyName'], ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba', 'SACOG'])
    df_counties = df_counties.sort_values(['AcademicYear', 'Sort'], ascending=[False, True]).drop('Sort', axis=1).reset_index(drop=True)
    print('\n\nBy County:')
    display(df_counties)

    # By District
    df_district = df_edu.copy()
    df_district = df_district[df_district['AggregateLevel'] == 'D']
    df_district = df_district.groupby(['AcademicYear', 'CountyName', 'DistrictName', 'ReportingCategory'], as_index=False).agg(TotalStudents=('CohortStudents', 'sum'), Graduated=('Regular HS Diploma Graduates (Count)', 'sum'), Met_UC_req=("Met UC/CSU Grad Req's (Count)", 'sum'))
    df_district['Graduated_pct' ] = df_district['Graduated' ]/df_district['TotalStudents']
    df_district['Met_UC_req_pct'] = df_district['Met_UC_req']/df_district['Graduated'    ]
    df_district['Sort'] = pd.Categorical(df_district['CountyName'], ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba', 'SACOG'])
    df_district = df_district.sort_values(['AcademicYear', 'Sort', 'DistrictName'], ascending=[False, True, True]).drop('Sort', axis=1).reset_index(drop=True)
    print('\n\nBy School District:')
    display(df_district)


    if EXPORT:

        indicator='Edu_3'
        sample_type='CDE'
        geography='Counties and School Districts'
        file_out = PATH_SERVER / f'{indicator} A-G v2.xlsx'

        params = {'sample'      : sample_type
                  , 'indicator'  : indicator
                  , 'start_year' : year_start
                  , 'end_year'   : year_end
                  , 'geo'       : geography
                  , 'estimate'  : None
                  , 'moe_thresh': None}

        df_about = func.write_about(params)
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


