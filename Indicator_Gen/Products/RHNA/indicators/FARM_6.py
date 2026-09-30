

import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import warnings

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


warnings.filterwarnings("ignore")

if __name__ == '__main__':

    df_places = pd.read_excel(PATH_DATA / f'{INDICATOR} Places ACS5.xlsx')
    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Occupation'})
    df_places = df_places[['County Name', 'Geography', 'Occupation', 'Median Annual Earnings']]


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography']==jurisdiction].drop(['County Name', 'Geography'], axis=1)
            df_plot = df_prod.copy()

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

