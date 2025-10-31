# Import queried BLS data


print()
print('Processing BLS data...')

df_bls1 = df_bls.copy()

df_bls1 = pd.melt(df_bls1, id_vars = ['year', 'periodName'], var_name='seriesID', value_name='value')    
df_bls1['date_'] = df_bls1['year'].astype('str') + '-' + df_bls1['periodName'].astype('str')
df_bls1['date_'] = pd.to_datetime(df_bls1['date_'])

if survey in ['SM', 'CE']:
    df_bls1['value'] = df_bls1['value'].astype('float32').apply(lambda x: x*1000)

if survey in ['SM', 'LA', 'CE']:
    df_bls1 = df_bls1.merge(df_series_area, on='seriesID')

    if survey in ['SM', 'CE']:
        df_bls1 = df_bls1.groupby(['date_', 'area_text', 'area_code', 'Variable'], as_index=False).agg(value=('value', 'sum'))
        df_bls1 = df_bls1.pivot_table(index = ['date_', 'area_code', 'area_text'], columns='Variable', values='value').reset_index()
        df_bls1 = pd.melt(df_bls1, id_vars = ['date_', 'area_code', 'area_text'], var_name='Variable', value_name='Value')
        df_bls1 = df_bls1.merge(df_industries[['Variable', 'industry_code']], on='Variable')
        df_bls1 = df_bls1.sort_values(['area_code', 'area_text', 'date_', 'industry_code'], ascending=[True, True, False, True])

    if survey == 'LA':
        df_bls1 = df_bls1.sort_values(['MSA_ID', 'area_text', 'date_'], ascending=[True, True, False])
        df_bls1 = df_bls1[['date_', 'MSA_ID', 'area_text', 'value']]
        df_bls1['date_'] = df_bls1['date_'].astype('str')


df_bls1 = df_bls1.reset_index(drop=True)
display(df_bls1.head())



if indicator == 'Jobs_1':
    if percentages == 'Yes':
            # Estimate proportions by groupings
            df_bls1['Percentage'] = df_bls1['Value'] / df_bls1.groupby(['area_text', 'date_'])['Value'].transform('sum')
                
            # Reshape data to wide format
            df_bls2_pct = df_bls1.pivot_table(index = ['area_text', 'date_']
                                               , columns='Variable'
                                               , values='Percentage').reset_index()
            df_bls2_pct = df_bls2_pct.sort_values(['area_text', 'date_'], ascending=[True, False])
    
    df_bls1_all = df_bls1.groupby(['date_', 'area_text'], as_index=False)['Value'].agg(sum)
    df_bls1_all['Variable'] = 'All'
    df_bls1_all['Percentage'] = np.nan
    df_bls1_all = df_bls1_all.merge(df_bls1[['area_text', 'area_code']].drop_duplicates(), on='area_text', how='left')
    
    df_bls1_all = pd.concat([df_bls1, df_bls1_all])
    df_bls1_all = df_bls1_all.sort_values(['area_code', 'date_', 'Variable'], ascending=[True, False, True])
    df_bls1 = df_bls1_all.copy()
    df_bls1 = df_bls1.reset_index(drop=True)
    df_bls1['date_'] = df_bls1['date_'].astype('str')
    df_bls1 = df_bls1.drop(['industry_code'], axis=1)
    df_bls1 = df_bls1.sort_values(['area_code', 'date_', 'Variable'], ascending=[True, False, True])
    display(df_bls1.head())
    

if indicator == 'Jobs_2':

    if geography == 'MSA':
        
        df_bls_msa = df_bls1.copy()
        df_bls_msa = df_bls_msa.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
        df_bls_msa = df_bls_msa.drop_duplicates()
        df_bls_mpo = df_bls_msa[df_bls_msa['MSA'].str.contains('Sacramento|Yuba')]

        df_bls_msa = df_bls_msa.groupby(['MSA ID', 'MSA', 'date_', 'Variable', 'industry_code'], as_index=False).agg(value=('Value', 'sum'))
        df_bls_mpo = df_bls_mpo.groupby([                 'date_', 'Variable', 'industry_code'], as_index=False).agg(value=('Value', 'sum'))
        df_bls_mpo['MPO'] = 'SACOG'

        df_bls_msa = df_bls_msa.pivot_table(index = ['MSA ID', 'MSA', 'date_'], columns='Variable', values='value').reset_index()
        df_bls_mpo = df_bls_mpo.pivot_table(index = [          'MPO', 'date_'], columns='Variable', values='value').reset_index()

        df_bls_msa = pd.melt(df_bls_msa, id_vars = ['MSA ID', 'MSA', 'date_'], var_name='Variable', value_name='Value')
        df_bls_mpo = pd.melt(df_bls_mpo, id_vars = [          'MPO', 'date_'], var_name='Variable', value_name='Value')

        df_bls_msa = df_bls_msa.merge(df_series_area[['Variable', 'industry_code']], on='Variable')
        df_bls_mpo = df_bls_mpo.merge(df_series_area[['Variable', 'industry_code']], on='Variable')

        df_bls_msa = df_bls_msa.drop_duplicates(['MSA ID', 'MSA', 'date_', 'Variable', 'Value'])
        df_bls_mpo = df_bls_mpo.drop_duplicates([          'MPO', 'date_', 'Variable', 'Value'])
    
        if percentages == 'Yes':

            vars_to_exclude = ['Total Nonfarm', 'Total Private', 'State Government Educational Services', 'State Government Excluding Education', 'Local Government Educational Services', 'Local Government excluding Educational Services']
            df_bls_msa['Percentage'] = df_bls_msa['Value'] / df_bls_msa[~df_bls_msa['Variable'].isin(vars_to_exclude)].groupby(['MSA', 'date_'])['Value'].transform('sum')
            df_bls_mpo['Percentage'] = df_bls_mpo['Value'] / df_bls_mpo[~df_bls_mpo['Variable'].isin(vars_to_exclude)].groupby(['MPO', 'date_'])['Value'].transform('sum')
    
        df_bls_msa = df_bls_msa.sort_values(['MSA ID', 'MSA', 'date_', 'industry_code'], ascending=[True, True, False, True])
        df_bls_mpo = df_bls_mpo.sort_values([          'MPO', 'date_', 'industry_code'], ascending=[True,       False, True])
        
        df_bls_msa = df_bls_msa.drop(['industry_code'], axis=1)
        df_bls_mpo = df_bls_mpo.drop(['industry_code'], axis=1)
    
        df_bls_msa['date_'] = df_bls_msa['date_'].astype('str')
        df_bls_mpo['date_'] = df_bls_mpo['date_'].astype('str')
    
        df_bls_msa = df_bls_msa.reset_index(drop=True)
        df_bls_mpo = df_bls_mpo.reset_index(drop=True)

        display(df_bls_msa.head(), df_bls_mpo.head())
        
    if geography == 'National':
        df_bls1 = df_bls1.set_index(['date_']).reset_index()
        df_bls1 = df_bls1.drop(['industry_code'], axis=1) # removed "area_code"
        df_bls1 = df_bls1.drop_duplicates()
        df_bls1['date_'] = df_bls1['date_'].astype('str')

        df_bls1['Percentage'] = df_bls1['Value'] / df_bls1[~df_bls1['Variable'].isin(['Total Nonfarm', 'Total Private', 'State Government', 'Local Government'])].groupby(['area_text', 'date_'])['Value'].transform('sum')
        
        display(df_bls1.head())

if indicator == 'Jobs_3':
    df_bls1_1 = df_bls1[df_bls1['Variable'].isin(['Total Private'  , 'Government'       ])]
    df_bls1_2 = df_bls1[df_bls1['Variable'].isin(['Goods Producing', 'Service-Providing'])]

    df_bls1_1['Percentage'] = df_bls1_1['Value'] / df_bls1_1.groupby(['area_text', 'date_'])['Value'].transform('sum')
    df_bls1_2['Percentage'] = df_bls1_2['Value'] / df_bls1_2.groupby(['area_text', 'date_'])['Value'].transform('sum')

    df_bls1_1_all = df_bls1_1.groupby(['date_', 'area_text'], as_index=False)['Value'].agg(sum)
    df_bls1_1_all['Variable'] = 'All'
    df_bls1_1_all['Percentage'] = np.nan
    df_bls1_1_all = df_bls1_1_all.merge(df_bls1[['area_text', 'area_code']].drop_duplicates(), on='area_text', how='left')
    df_bls1_1_all = pd.concat([df_bls1_1, df_bls1_1_all])
    df_bls1_1_all = df_bls1_1_all.sort_values(['area_text', 'date_', 'Variable'], ascending=[True, False, True])
    df_bls1_1 = df_bls1_1_all.copy()
    
    df_bls1_2_all = df_bls1_2.groupby(['date_', 'area_text'], as_index=False)['Value'].agg(sum)
    df_bls1_2_all['Variable'] = 'All'
    df_bls1_2_all['Percentage'] = np.nan
    df_bls1_2_all = df_bls1_2_all.merge(df_bls1[['area_text', 'area_code']].drop_duplicates(), on='area_text', how='left')
    df_bls1_2_all = pd.concat([df_bls1_2, df_bls1_2_all])
    df_bls1_2_all = df_bls1_2_all.sort_values(['area_text', 'date_', 'Variable'], ascending=[True, False, True])
    df_bls1_2 = df_bls1_2_all.copy()

    df_bls1_1 = df_bls1_1.drop(['industry_code'], axis=1)
    df_bls1_2 = df_bls1_2.drop(['industry_code'], axis=1)

    df_bls1_1 = df_bls1_1.reset_index(drop=True)
    df_bls1_2 = df_bls1_2.reset_index(drop=True)
    
    df_bls1_1['date_'] = df_bls1_1['date_'].astype('str')
    df_bls1_2['date_'] = df_bls1_2['date_'].astype('str')

    display(df_bls1_1.head(), df_bls1_2.head())

if indicator == 'Labor_2':
    df_bls1['value'] = df_bls1['value']/100



print()
print('Final renaming and reorganization of data: ')




if indicator == 'Jobs_1':
    if geography == 'MSA':
        df_bls1 = df_bls1.rename(columns={'area_text':'MSA', 'Variable':'Sector', 'Value':'Total Jobs', 'area_code':'MSA ID'})
    if geography == 'National':
        df_bls1 = df_bls1.rename(columns={'area_text':'MSA', 'Variable':'Sector', 'Value':'Total Jobs', 'area_code':'MSA ID'})
    display(df_bls1.head())

if indicator == 'Labor_2':
    df_bls1 = df_bls1.rename(columns={'area_text':'Geography', 'value':'Unemployment Rate'})
    display(df_bls1.head())

if indicator == 'Jobs_2':
    if geography == 'MSA':
        df_bls_msa = df_bls_msa.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
        df_bls_mpo = df_bls_mpo.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
        df_bls_msa['Notes'] = np.nan
        df_bls_msa.loc[df_bls_msa['Total Jobs'] == 0, 'Notes'] = 'No data collected for this specific sector'
        display(df_bls_msa.head(), df_bls_mpo.head())
    if geography == 'National':
        df_bls1 = df_bls1.rename(columns={'area_text':'Geography', 'Variable':'Sector', 'Value':'Total Jobs'})
        display(df_bls1.head())

if indicator == 'Jobs_3':
    df_bls1_1 = df_bls1_1.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
    df_bls1_2 = df_bls1_2.rename(columns={'Variable':'Sector', 'Value':'Total Jobs'})
    if geography == 'MSA':
        df_bls1_1 = df_bls1_1.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
        df_bls1_2 = df_bls1_2.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
    if geography == 'National':
        df_bls1_1 = df_bls1_1.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
        df_bls1_2 = df_bls1_2.rename(columns={'area_text':'MSA', 'area_code':'MSA ID'})
    display(df_bls1_1.head(), df_bls1_2.head())



