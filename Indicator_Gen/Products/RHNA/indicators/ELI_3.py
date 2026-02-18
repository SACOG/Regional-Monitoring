

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import warnings; warnings.filterwarnings("ignore")

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


if __name__ == '__main__':

    df_places = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR} Places ACS5.xlsx')
    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Poverty Status', 'Percentage':'Percent', 'Race_Ethnicity':'Race/Ethnicity'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True)
    df_places = df_places[['County Name', 'Geography', 'Poverty Status', 'Race/Ethnicity', 'Population', 'Percent']]


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography']==jurisdiction].pivot_table(index='Race/Ethnicity', columns='Poverty Status', values='Population').reset_index()
            df_pct  = df_places_sub[df_places_sub['Geography']==jurisdiction].pivot_table(index='Race/Ethnicity', columns='Poverty Status', values='Percent'   ).reset_index()

            df_plot = df_places_sub[(df_places_sub['Geography'] == jurisdiction) & (df_places_sub['Poverty Status']=='Below poverty level')]
            df_plot['Percent of Population'] = round(df_plot['Percent']*100, 1)
            df_plot = df_plot.sort_values('Percent of Population', ascending=False)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

