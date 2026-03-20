


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


if __name__ == '__main__':

    df_places, df_counties, df_mpo = rhna.acs_import(INDICATOR)
    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Year Built', 'Percentage':'Percent'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True)

    df_places = df_places[['County Name', 'Geography', 'Year Built', 'Households', 'Percent']].drop_duplicates()
    df_places['Sort'] = pd.Categorical(df_places['Year Built'], ['Built 2010 or later', 'Built 2000 to 2009', 'Built 1980 to 1999', 'Built 1960 to 1979', 'Built 1940 to 1959', 'Built 1939 or earlier'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Sort'], ascending=[True, True, False]).drop(['Sort'], axis=1)


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_places_sub = df_places.copy()
        df_places_sub = df_places_sub[df_places_sub['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod0 = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_prod = df_prod0[['Year Built', 'Households']].drop_duplicates()
            df_pct  = df_prod0[['Year Built', 'Percent'   ]].drop_duplicates()
            df_plot = df_prod.copy()
            df_plot['Year Built'] = df_plot['Year Built'].str.replace('Built ', '')

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

