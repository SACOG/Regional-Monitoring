

import pandas as pd
from pathlib import Path
from IPython.display import display


path_in = r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Products\StoryMaps\Housing\original_export'
# file_names = {
#     'Jurisdiction': ['Housing_5 Places ACS5.xlsx', 'Places'],
#     'Counties': ['Housing_5 Counties ACS5.xlsx', 'Counties'],
#     'MPO': ['Housing_5 MPO ACS5.xlsx', 'MPO']
#     }
file_names = {
    'Jurisdiction': ['Housing_6 Places ACS5.xlsx', 'Places'],
    'Counties': ['Housing_6 Counties ACS5.xlsx', 'Counties'],
    'MPO': ['Housing_6 MPO ACS5.xlsx', 'MPO']
    }



if __name__=='__main__':
    print('\n'*2)

    for geo, filenames in file_names.items():

        print(geo)
        file_in = Path(path_in) / filenames[0]
        sheet_name = filenames[1]

        df = pd.read_excel(file_in, sheet_name=sheet_name)

        if geo == 'Jurisdiction':
            geos = ['County Name', 'NAME']
        if geo == 'Counties':
            geos = ['County Name']
        if geo == 'MPO':
            geos = ['MPO']

        df[['Type', 'Burden']] = df['Cost Burden'].str.split(':', n=1, expand=True)
        
        df = df[geos+['Year', 'Type', 'Burden', 'Households']]
        df['Percent of Households'] = df['Households'] / df.groupby(geos + ['Year', 'Type'])['Households'].transform('sum')

        df_units = df.pivot_table(index=geos+['Year', 'Type'], columns='Burden', values='Households'           ).reset_index()
        df_pct   = df.pivot_table(index=geos+['Year', 'Type'], columns='Burden', values='Percent of Households').reset_index()

        df = df_units.merge(df_pct, on=geos+['Year', 'Type'], how='left')

        for col in df.columns:
            if '_x' in col:
                col_clean = col.replace('_x', ' (Households)')
                df = df.rename(columns={col:col_clean})
            if '_y' in col:
                col_clean = col.replace('_y', ' (Percent of Households)')
                df = df.rename(columns={col:col_clean})
        df = df.sort_values(geos + ['Year', 'Type'], ascending = [item in geos for item in geos] + [False, True]).reset_index(drop=True)
        display(df)

        with pd.ExcelWriter(Path(path_in).parent/'Housing Cost Burden_ACS5_V2.xlsx', mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False, sheet_name=geo)


print('\n'*2)


