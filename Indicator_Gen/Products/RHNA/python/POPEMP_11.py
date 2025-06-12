

indicator = 'RHNA_POPEMP_11'


# Set indicator
source = 'LEHD'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]
base_year = 2002
end_year = 2022


## Mappings ---

# Block Group to Census Designated Places mapping
file_map = path_geo / 'Census_2020_BG_Jurisdiction.csv'
df_map = pd.read_csv(file_map)
df_map = df_map[['Geographic_Code_Identifier', 'JURIS', 'COUNTY']]
df_map['Geographic_Code_Identifier'] = df_map['Geographic_Code_Identifier'].astype('str')


# WAC job sector code to description mapping
file_lodes = path_lodes / 'LEHD_LODESmappings.xlsx'
df_lodes = pd.read_excel(file_lodes, sheet_name='WAC')
df_lodes = df_lodes[['Variable', 'Explanation']].rename(columns={'Variable':'job_sector_code', 'Explanation':'Desc'})

job_sectors = ['CNS01', 'CNS02', 'CNS03', 'CNS04', 'CNS05', 'CNS06', 'CNS07', 'CNS08', 'CNS09', 'CNS10', 'CNS11', 'CNS12', 'CNS13', 'CNS14', 'CNS15', 'CNS16', 'CNS17', 'CNS18', 'CNS19', 'CNS20']


## Organizing ---


print(); print()
print('Importing Workplace Area Characteristic (WAC) data by year from zip files stored online found here:  https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/')
print()

years = range(base_year, end_year+1, 1)


list_df = []

for year in tqdm(years):
    url = f'https://lehd.ces.census.gov/data/lodes/LODES8/ca/wac/ca_wac_S000_JT00_{year}.csv.gz'
    data = import_gz_from_url(url)
    df = pd.read_csv(io.StringIO(data.decode('utf-8')))
    df['Year'] = year
    
    df['block_group'] = df['w_geocode'].astype('str')
    df['block_group'] = df['block_group'].str[0:11]
    df = df[df['block_group'].isin(df_map['Geographic_Code_Identifier'].unique())]
    df = df.merge(df_map, left_on='block_group', right_on='Geographic_Code_Identifier')
    df = df.drop(['w_geocode', 'createdate', 'block_group', 'Geographic_Code_Identifier'], axis=1)
    df = df.groupby(['Year', 'COUNTY', 'JURIS'], as_index=False).sum()
    df = df.melt(id_vars=['Year', 'COUNTY', 'JURIS'], var_name='job_sector_code', value_name='num_jobs')
    df = df.merge(df_lodes, on='job_sector_code', how='left')
    df = df[df['job_sector_code'].isin(job_sectors)]
    df = df.reset_index(drop=True)
    
    def re_remove_pre(x, exp = '('):
        if x == 'nan':
            return 'nan'
        else:
            return str(x.split(exp, 1)[1])
        
    df['Desc_clean'] = df['Desc'].apply(re_remove_pre)
    df['Desc_clean'] = df['Desc_clean'].str[:-1]

    conditions = [
          df['Desc_clean'].isin(['Agriculture, Forestry, Fishing and Hunting', 'Mining, Quarrying, and Oil and Gas Extraction'])
        , df['Desc_clean'].isin(['Arts, Entertainment, and Recreation', 'Accommodation and Food Services', 'Other Services [except Public Administration]'])
        , df['Desc_clean'].isin(['Construction'])
        , df['Desc_clean'].isin(['Finance and Insurance', 'Real Estate and Rental and Leasing'])
        , df['Desc_clean'].isin(['Public Administration'])
        , df['Desc_clean'].isin(['Educational Services', 'Health Care and Social Assistance'])
        , df['Desc_clean'].isin(['Information'])
        , df['Desc_clean'].isin(['Manufacturing', 'Wholesale Trade'])
        , df['Desc_clean'].isin(['Professional, Scientific, and Technical Services', 'Management of Companies and Enterprises', 'Administrative and Support and Waste Management and Remediation Services'])
        , df['Desc_clean'].isin(['Retail Trade'])
        , df['Desc_clean'].isin(['Utilities', 'Transportation and Warehousing'])
    ]

    choices = ['Agriculture & Natural Resources', 'Arts, Recreation, & Other', 'Construction', 'Financial & Leasing', 'Government', 'Health & Educational Services'
            , 'Information', 'Manufacturing & Wholesale', 'Professional & Managerial Services', 'Retail', 'Transportation & Utilities']

    df['Desc_final'] = np.select(conditions, choices, default='No')

    df = df.groupby(['Year', 'COUNTY', 'JURIS', 'Desc_final'], as_index=False)['num_jobs'].sum()

    df.loc[df['JURIS'].str.contains('County'), 'JURIS'] = 'Unincorporated'

    list_df.append(df)

df = pd.concat(list_df)
df = df.reset_index(drop=True)

print()
print('Data for all years: ')
display(df.head())

counties = df['COUNTY'].unique()


## Plotting ---

for county in counties:

    print();print()
    print(county)
    time.sleep(1)

    df_sub = df[df['COUNTY'] == county]
    jurisdictions = df_sub['JURIS'].unique()

    for jurisdiction in tqdm(jurisdictions):
        tqdm.write(jurisdiction)

        df_prod = df_sub.copy()
        df_prod = df_prod[df_prod['JURIS'] == jurisdiction]
        df_prod = df_prod.drop('COUNTY', axis=1)
        df_prod = df_prod.pivot_table(index='Year', columns='Desc_final', values='num_jobs').reset_index()

        df_plot = df_sub.copy()
        df_plot = df_plot[df_plot['JURIS'] == jurisdiction]


        color_map = {
            'Agriculture & Natural Resources': '#1E90FF'
            , 'Arts, Recreation, & Other': '#E56717'
            , 'Construction': '#1F45FC'
            , 'Financial & Leasing': '#FBB117'
            , 'Government': '#DC381F'
            , 'Health & Educational Services': '#008000'
            , 'Information': '#7E587E'
            , 'Manufacturing & Wholesale': '#9DC209'
            , 'Professional & Managerial Services': '#CC7A8B'
            , 'Retail': '#7FFFD4'
            , 'Transportation & Utilities': '#906E3E'
        }

        fig = px.bar(df_plot, x='Year', y='num_jobs'
                        , color = 'Desc_final'
                        , color_discrete_map=color_map)

        fig.update_layout(legend={'traceorder': 'reversed'})
        fig.update_traces(hovertemplate="%{y}")

        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)


        ## Exporting ---
        
        if export:
            export_rhna(df_prod)

list_indicators.append(indicator)

