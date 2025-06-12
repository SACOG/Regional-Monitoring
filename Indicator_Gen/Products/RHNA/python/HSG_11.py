

## Right now, using the "5th Cycle Full Summary", but will need to update to 6th or 7th I'm guessing


indicator = 'RHNA_HSG_11'


# Set indicator
source = 'HCD'
with path_func.open("r") as f: exec(f.read())
title = dict_about[source][indicator.replace('RHNA_', '')]['Indicator Title'][0]



file_in = path_raw / 'HCD_annualprogressreport.xlsx'
sheet_name='5th Cycle Full Summary'
df_hcd = pd.read_excel(file_in, sheet_name=sheet_name, skiprows=1)

df_hcd = df_hcd[['COUNTY', 'JURS NAME', 'ABOVE MOD PERMITS', 'MOD PERMITS', 'LI PERMITS', 'VLI PERMITS']]
df_hcd = df_hcd[df_hcd['COUNTY'].isin(['EL DORADO', 'PLACER', 'SACRAMENTO', 'SUTTER', 'YOLO', 'YUBA'])]
df_hcd = df_hcd.reset_index(drop=True)

df_hcd['COUNTY'   ] = df_hcd['COUNTY'   ].str.title()
df_hcd['JURS NAME'] = df_hcd['JURS NAME'].str.title()

df_hcd.loc[df_hcd['JURS NAME'].str.contains('County'), 'JURS NAME'] = 'Unincorporated'



counties = list(df_hcd['COUNTY'].unique())

for county in counties:

    print(); print()
    print(county)

    path_county = path_out / county
    df_sub = df_hcd[df_hcd['COUNTY'] == county]
    jurisdictions = list(df_sub['JURS NAME'].unique())

    for jurisdiction in tqdm(jurisdictions, position=0):

        tqdm.write(jurisdiction)

        df_sub_juris = df_sub[df_sub['JURS NAME'] == jurisdiction]
        df_sub_juris = df_sub_juris.drop(['COUNTY', 'JURS NAME'], axis=1)

        ## Plotting ---

        df_prod = df_sub_juris.copy()
        df_prod = df_prod.T.reset_index()
        df_prod.columns = ['Income Group', 'Number of Permits']

        df_plot = df_prod.copy()

        fig = px.bar(df_plot, x='Income Group', y='Number of Permits')
        fig.update_traces(marker_color='#1E90FF')
        fig.update_traces(hovertemplate="%{y}")
    
        path_plots = path_out / county.replace(' County', '') / jurisdiction / 'Supplemental'
        plot_rhna(export=export)

        ## Exporting ---
        if export:
            export_rhna(df_prod)

list_indicators.append(indicator)

