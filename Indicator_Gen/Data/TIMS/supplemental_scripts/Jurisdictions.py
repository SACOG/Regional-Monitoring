
dict_cat1 = {}

for cat in categories:
    path_cat = os.path.join(path_tims, cat, 'Jurisdictions')

    dict_counties = {}
    for county in os.listdir(path_cat):
        path_county = os.path.join(path_cat, county)
    
        list_files = []
        for file in os.listdir(path_county):
            list_files.append(file)
            
        dict_counties[county] = list_files
        
    dict_cat1[cat] = dict_counties



print('Organizing raw TIMS data...')
print('')


list_df_final = []
for cat in dict_cat1.keys():
    print(cat)

    list_df_total = []
    list_df_mvmt  = []
    list_df_non1  = []
    list_df_non2  = []
    
    for county in dict_cat1[cat]:
        print(county)
        for file in tqdm(dict_cat1[cat][county]):
            path_csv = os.path.join(path_tims, cat, 'Jurisdictions', county, file)
            df_temp = pd.read_csv(path_csv)
            
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
        df_non1  = pd.concat(list_df_non1 )
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

print('')
print('Finished !!')
print('')

df_tims1.head()