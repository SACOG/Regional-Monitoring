


import pandas as pd
import os
from pathlib import Path
from tqdm import tqdm
import re
import functools as ft
pd.set_option('display.max_columns', None)


PATH_GIT = Path.cwd().parent.parent
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_GIT / 'Data' / 'TIMS' / 'config'

# SharePoint OneDrive paths
PATH_MAIN = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents' / 'Data'
PATH_OUT  = PATH_MAIN / 'Safe Equitable Resilient Infrastructure' / 'Safety'
PATH_TIMS = PATH_OUT / 'TIMS'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")




def jurisdiction(categories, years_to_import):

    dt_cat1 = {}

    for cat in categories:

        path_cat = PATH_TIMS / cat / 'Jurisdictions'

        dt_counties = {}
        for county in os.listdir(path_cat):
            path_county = PATH_TIMS / cat / 'Jurisdictions' / county
        
            list_files = []
            for file in os.listdir(path_county):
                list_files.append(file)
                
            dt_counties[county] = list_files
            
        dt_cat1[cat] = dt_counties

    print(dt_cat1)

    print('Organizing raw TIMS data...')
    print()

    list_df_final = []
    for cat in dt_cat1.keys():
        print(cat)

        list_df_total = []
        list_df_mvmt  = []
        list_df_non1  = []
        list_df_non2  = []
        
        for county in dt_cat1[cat]:
            print(county)
            for file in tqdm(dt_cat1[cat][county]):
                df_temp = pd.read_csv(PATH_TIMS / cat / 'Jurisdictions' / county / file)
                
                df_temp = df_temp.iloc[:,0:3]

                metric = re.sub('-', ' ', re.sub(r'-[^-]*$', '', file))
                metric = metric.capitalize()
                df_temp.columns = ['Year', metric, metric + '_5 Year Rolling Average']

                df_temp = df_temp[df_temp['Year'].isin(years_to_import)]

                jurisdiction = re.sub('.csv', '', re.sub('.*-', '', file))
                jurisdiction = jurisdiction.capitalize()
                if jurisdiction == 'Unincorporated':
                    jurisdiction = county + ' Unincorporated'
                
                df_temp['County'      ] = county
                df_temp['Jurisdiction'] = jurisdiction

                df_temp = df_temp.set_index(['County', 'Jurisdiction', 'Year']).reset_index()

                if cat == 'Non-Motorized':
                    if 'serious' in file:
                        list_df_non2.append(df_temp)
                    else:
                        list_df_non1.append(df_temp)
                else:
                    if 'mvm' in file:
                        list_df_mvmt.append(df_temp)
                    else:
                        list_df_total.append(df_temp)
        if cat == 'Non-Motorized':                
            df_non1  = pd.concat(list_df_non1)
            df_non2  = pd.concat(list_df_non2)
            list_df_cat = [df_non1, df_non2]
        else:                
            df_mvmt  = pd.concat(list_df_mvmt )
            df_total = pd.concat(list_df_total)
            list_df_cat = [df_total, df_mvmt]

        df_cat = ft.reduce(lambda left, right: pd.merge(left, right, on = ['County', 'Jurisdiction', 'Year']), list_df_cat)
        list_df_final.append(df_cat)

    df_tims1 = ft.reduce(lambda left, right: pd.merge(left, right, on = ['County', 'Jurisdiction', 'Year']), list_df_final)
    df_tims1 = df_tims1.sort_values(['County', 'Jurisdiction', 'Year'], ascending = [True, True, True])

    print()
    print('Finished !!')
    print()

    return df_tims1





def county(categories, years_to_import):
    
    dt_cat2 = {}

    for cat in categories:
        path_cat = PATH_TIMS / cat / 'Counties'

        list_files = []
        for file in os.listdir(path_cat):
            path_counties = os.path.join(path_cat, file)
            list_files.append(path_counties)
        dt_cat2[cat] = list_files

    print(dt_cat2)

    print('Organizing raw TIMS data...')
    print()


    list_df_final = []
    for cat in dt_cat2.keys():
        print(cat)

        list_df_total = []
        list_df_mvmt  = []
        list_df_non1  = []
        list_df_non2  = []
        
        for path_csv in tqdm(dt_cat2[cat]):
            df_temp = pd.read_csv(path_csv)
            file = re.sub(r'.*\\', '', path_csv)
            
            df_temp = df_temp.iloc[:,0:3]

            metric = re.sub('-', ' ', re.sub(r'-[^-]*$', '', file))
            metric = metric.capitalize()
            df_temp.columns = ['Year', metric, metric + '_5 Year Rolling Average']

            df_temp = df_temp[df_temp['Year'].isin(years_to_import)]

            county = re.sub('.csv', '', re.sub(r'.*-', '', file))
            county = county.title()
            
            df_temp['County'] = county

            df_temp = df_temp.set_index(['County', 'Year']).reset_index()

            if cat == 'Non-Motorized':
                if 'serious' in file:
                    list_df_non2.append(df_temp)
                else:
                    list_df_non1.append(df_temp)
            else:
                if 'mvm' in file:
                    list_df_mvmt.append(df_temp)
                else:
                    list_df_total.append(df_temp)
        if cat == 'Non-Motorized':                
            df_non1  = pd.concat(list_df_non1 )
            df_non2  = pd.concat(list_df_non2)
            list_df_cat = [df_non1, df_non2]
        else:                
            df_mvmt  = pd.concat(list_df_mvmt )
            df_total = pd.concat(list_df_total)
            list_df_cat = [df_total, df_mvmt]

        df_cat = ft.reduce(lambda left, right: pd.merge(left, right, on = ['County', 'Year']), list_df_cat)
        list_df_final.append(df_cat)

    df_tims2 = ft.reduce(lambda left, right: pd.merge(left, right, on = ['County', 'Year']), list_df_final)
    df_tims2 = df_tims2.sort_values(['County', 'Year'], ascending = [True, True])

    print()
    print('Finished !!')
    print()

    return df_tims2





def mpo(categories, years_to_import):

    dt_cat3 = {}

    for cat in categories:
        path_cat = PATH_TIMS / cat / 'MPO'

        list_files = []
        for file in os.listdir(path_cat):
            path_mpo = os.path.join(path_cat, file)
            list_files.append(path_mpo)
        dt_cat3[cat] = list_files

    print(dt_cat3)


    print('Organizing raw TIMS data...')
    print()


    list_df_final = []
    for cat in dt_cat3.keys():
        print(cat)

        list_df_total = []
        list_df_mvmt  = []
        list_df_non1  = []
        list_df_non2  = []
        
        for path_csv in tqdm(dt_cat3[cat]):
            df_temp = pd.read_csv(path_csv)
            file = re.sub(r'.*\\', '', path_csv)
            
            df_temp = df_temp.iloc[:,0:3]

            metric = re.sub('-', ' ', re.sub(r'-[^-]*$', '', file))
            metric = metric.capitalize()
            df_temp.columns = ['Year', metric, metric + '_5 Year Rolling Average']

            df_temp = df_temp[df_temp['Year'].isin(years_to_import)]

            mpo = re.sub('.csv', '', re.sub(r'.*-', '', file))
            
            df_temp['MPO'] = mpo

            df_temp = df_temp.set_index(['MPO', 'Year']).reset_index()

            if cat == 'Non-Motorized':
                if 'serious' in file:
                    list_df_non2.append(df_temp)
                else:
                    list_df_non1.append(df_temp)
            else:
                if 'mvm' in file:
                    list_df_mvmt.append(df_temp)
                else:
                    list_df_total.append(df_temp)
        if cat == 'Non-Motorized':                
            df_non1  = pd.concat(list_df_non1 )
            df_non2  = pd.concat(list_df_non2)
            list_df_cat = [df_non1, df_non2]
        else:                
            df_mvmt  = pd.concat(list_df_mvmt )
            df_total = pd.concat(list_df_total)
            list_df_cat = [df_total, df_mvmt]

        df_cat = ft.reduce(lambda left, right: pd.merge(left, right, on = ['MPO', 'Year']), list_df_cat)
        list_df_final.append(df_cat)

    df_tims3 = ft.reduce(lambda left, right: pd.merge(left, right, on = ['MPO', 'Year']), list_df_final)
    df_tims3 = df_tims3.sort_values(['MPO', 'Year'], ascending = [True, True])

    print()
    print('Finished !!')
    print()


    return df_tims3



def statewide(categories, years_to_import):


    dt_cat4 = {}

    for cat in categories:
        path_cat = PATH_TIMS / cat / 'Statewide'

        list_files = []
        for file in os.listdir(path_cat):
            path_mpo = os.path.join(path_cat, file)
            list_files.append(path_mpo)        
        dt_cat4[cat] = list_files

    print(dt_cat4)


    print('Organizing raw TIMS data...')
    print('')


    list_df_final = []
    for cat in dt_cat4.keys():
        print(cat)

        list_df_total = []
        list_df_mvmt  = []
        list_df_non1  = []
        list_df_non2  = []
        
        for path_csv in tqdm(dt_cat4[cat]):
            df_temp = pd.read_csv(path_csv)
            file = re.sub(r'.*\\', '', path_csv)
            
            df_temp = df_temp.iloc[:,0:3]

            metric = re.sub('-', ' ', re.sub(r'-[^-]*$', '', file))
            metric = metric.capitalize()
            df_temp.columns = ['Year', metric, metric + '_5 Year Rolling Average']

            df_temp = df_temp[df_temp['Year'].isin(years_to_import)]

            state = re.sub('.csv', '', re.sub(r'.*-', '', file))
            
            df_temp['State'] = state

            df_temp = df_temp.set_index(['State', 'Year']).reset_index()

            if cat == 'Non-Motorized':
                if 'serious' in file:
                    list_df_non2.append(df_temp)
                else:
                    list_df_non1.append(df_temp)
            else:
                if 'mvm' in file:
                    list_df_mvmt.append(df_temp)
                else:
                    list_df_total.append(df_temp)
        if cat == 'Non-Motorized':                
            df_non1  = pd.concat(list_df_non1 )
            df_non2  = pd.concat(list_df_non2)
            list_df_cat = [df_non1, df_non2]
        else:                
            df_mvmt  = pd.concat(list_df_mvmt )
            df_total = pd.concat(list_df_total)
            list_df_cat = [df_total, df_mvmt]

        df_cat = ft.reduce(lambda left, right: pd.merge(left, right, on = ['State', 'Year']), list_df_cat)
        list_df_final.append(df_cat)

    df_tims4 = ft.reduce(lambda left, right: pd.merge(left, right, on = ['State', 'Year']), list_df_final)
    df_tims4 = df_tims4.sort_values(['State', 'Year'], ascending = [True, True])

    print()
    print('Finished !!')
    print()

    return df_tims4


