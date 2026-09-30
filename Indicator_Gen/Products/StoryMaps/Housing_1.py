

import pandas as pd
from pathlib import Path
from IPython.display import display


path_in = r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Products\StoryMaps\Housing\original_export'
file_names = {
    'Jurisdiction': ['Housing_1 Places ACS5.xlsx', 'Places'],
    'Counties': ['Housing_1 Counties ACS5.xlsx', 'Counties']
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


        df_w = df.pivot_table(index=geos+['Year'], columns = 'Cost Burden', values='Households').reset_index()

        def calc_detailed_burdens(df, housing_type):
            df_w[f'{housing_type} 0-30%' ] = df_w[housing_type] - df_w[f'{housing_type} over 30 pct']
            df_w[f'{housing_type} 30-50%'] = df_w[housing_type] - df_w[f'{housing_type} 0-30%'] - df_w[f'{housing_type} over 50 pct']
            df_w[f'{housing_type} 50%+'  ] = df_w[f'{housing_type} over 50 pct'].copy()
            return df_w

        df_w = calc_detailed_burdens(df_w, 'Owned units with a mortgage')
        df_w = calc_detailed_burdens(df_w, 'Owned units without a mortgage')
        df_w = calc_detailed_burdens(df_w, 'Rented units')

        df_w = df_w[geos + ['Year',
                        'Owned units with a mortgage 0-30%',
                        'Owned units with a mortgage 30-50%',
                        'Owned units with a mortgage 50%+',
                        'Owned units with a mortgage not calculated',
                        'Owned units without a mortgage 0-30%',
                        'Owned units without a mortgage 30-50%',
                        'Owned units without a mortgage 50%+',
                        'Owned units without a mortgage not calculated',
                        'Rented units 0-30%',
                        'Rented units 30-50%',
                        'Rented units 50%+',
                        'Rented units not calculated'
                        ]]
                        
        df = df_w.melt(id_vars=geos+['Year'], var_name='Cost Burden', value_name='Households')

        df.loc[df['Cost Burden'].str.contains('with a mortgage'   ), 'Type'] = 'Owned units with a mortgage'
        df.loc[df['Cost Burden'].str.contains('without a mortgage'), 'Type'] = 'Owned units without a mortgage'
        df.loc[df['Cost Burden'].str.contains('Rented'), 'Type'] = 'Rented units'

        df['Cost Burden'] = df['Cost Burden'].str.replace('Owned units with a mortgage |Owned units without a mortgage |Rented units ', '', regex=True)

        df['Percent of Households'] = df['Households'] / df.groupby(geos + ['Year', 'Type'])['Households'].transform('sum')

        df = df[geos + ['Year', 'Type', 'Cost Burden', 'Households', 'Percent of Households']]

        df_units = df.pivot_table(index=geos+['Year', 'Type'], columns='Cost Burden', values='Households'           ).reset_index()
        df_pct   = df.pivot_table(index=geos+['Year', 'Type'], columns='Cost Burden', values='Percent of Households').reset_index()

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

        with pd.ExcelWriter(Path(path_in).parent/'Housing Cost Burden_ACS5_DRAFT.xlsx', mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df.to_excel(writer, index=False, sheet_name=geo)


print('\n'*2)


