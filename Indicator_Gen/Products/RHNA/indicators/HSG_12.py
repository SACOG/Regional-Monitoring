

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_AREA = Path(__file__).parent.parent.parent.parent / 'config' / 'area_codes.xlsx'
FILE_WEIGHTS = Path.home() / 'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents' / 'Data' / 'Reference' / 'Weights' / 'Total_Households Places ACS5.xlsx'



if __name__ == '__main__':

    df_places = pd.read_excel(PATH_DATA/f'{INDICATOR} Places ACS5.xlsx', sheet_name='Places')

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable':'Unit Size'})
    df_places = df_places[['County Name', 'Geography', 'Unit Size', 'Median Gross Rent']].reset_index(drop=True)
    df_places = df_places.pivot_table(index=['County Name', 'Geography'], columns='Unit Size', values='Median Gross Rent').reset_index()
    df_places = df_places.melt(id_vars=['County Name', 'Geography'], var_name='Unit Size', value_name='Median Gross Rent')
    df_places['sort'] = pd.Categorical(df_places['Unit Size'], ['Studio'
                                                                , '1 bedroom'
                                                                , '2 bedrooms'
                                                                , '3 bedrooms'
                                                                , '4 bedrooms'
                                                                , '5 or more bedrooms'])
    df_places = df_places.sort_values('sort').reset_index(drop=True)

    counties = df_places['County Name'].unique()

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)
        df_places_sub = df_places[df_places['County Name']==county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography']==jurisdiction][['Unit Size', 'Median Gross Rent']]
            df_plot = df_places_sub[df_places_sub['Geography']==jurisdiction][['Unit Size', 'Median Gross Rent']]

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

