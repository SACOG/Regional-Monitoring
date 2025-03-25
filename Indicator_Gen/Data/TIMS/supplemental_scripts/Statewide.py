dict_cat4 = {}

for cat in categories:
    path_cat = os.path.join(path_tims, cat, 'Statewide')

    list_files = []
    for file in os.listdir(path_cat):
        path_mpo = os.path.join(path_cat, file)
        list_files.append(path_mpo)        
    dict_cat4[cat] = list_files

dict_cat4


print('Organizing raw TIMS data...')
print('')


list_df_final = []
for cat in dict_cat4.keys():
    print(cat)

    list_df_total = []
    list_df_mvmt  = []
    list_df_non1  = []
    list_df_non2  = []
    
    for path_csv in tqdm(dict_cat4[cat]):
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

print('')
print('Finished !!')
print('')

df_tims4.head()