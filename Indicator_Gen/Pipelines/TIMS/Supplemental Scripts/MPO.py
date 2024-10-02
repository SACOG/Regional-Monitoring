
dict_cat3 = {}

for cat in categories:
    path_cat = os.path.join(path_tims, cat, 'MPO')

    list_files = []
    for file in os.listdir(path_cat):
        path_mpo = os.path.join(path_cat, file)
        list_files.append(path_mpo)
    dict_cat3[cat] = list_files


print('Organizing raw TIMS data...')
print('')


list_df_final = []
for cat in dict_cat3.keys():
    print(cat)

    list_df_total = []
    list_df_mvmt  = []
    list_df_non1  = []
    list_df_non2  = []
    
    for path_csv in tqdm(dict_cat3[cat]):
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

print('')
print('Finished !!')
print('')