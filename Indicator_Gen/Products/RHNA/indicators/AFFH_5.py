

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
    
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places  ['NAME'] = df_places  ['NAME'].str.replace(' city, California', '', regex=True)
    df_places   = df_places  .rename(columns={'NAME':'Geography'})

    df_places   = df_places  .rename(columns={'Variable':'Language Spoken at Home'})

    df_places = df_places[df_places['Year'] == df_places['Year'].max()][['County Name', 'Geography', 'Language Spoken at Home', 'Households', 'Percent']]
    df_places = df_places[df_places['Language Spoken at Home']!='English only'].reset_index(drop=True)
    df_places['Language Spoken at Home'] = df_places['Language Spoken at Home'].str.replace(' languages', '')
    
    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography']==jurisdiction].sort_values('Households', ascending=False).head(5).drop(['County Name', 'Geography', 'Percent'   ], axis=1)
            df_pct  = df_places_sub[df_places_sub['Geography']==jurisdiction].sort_values('Households', ascending=False).head(5).drop(['County Name', 'Geography', 'Households'], axis=1)

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction].sort_values('Households', ascending=False).head(5)
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

