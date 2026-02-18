

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

    df_places, df_counties, df_mpo = rhna.acs_import(INDICATOR)
    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Disability Type'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True)

    df_places['Overall Disability Topic'] = df_places['Disability Type'].copy()
    df_places['Overall Disability Topic'] = df_places['Overall Disability Topic'].str.replace('With a ', '')
    df_places['Overall Disability Topic'] = df_places['Overall Disability Topic'].str.replace('With an ', '')
    df_places['Overall Disability Topic'] = df_places['Overall Disability Topic'].str.replace('No ', '')
    df_places['Overall Disability Topic'] = df_places['Overall Disability Topic'].str.replace(' difficulty', '')
    df_places['Percent'] = df_places['Population'] / df_places.groupby(['County Name', 'Geography', 'Overall Disability Topic'])['Population'].transform('sum')

    df_places = df_places[~df_places['Disability Type'].str.contains('No')]
    df_places = df_places[['County Name', 'Geography', 'Disability Type',  'Population', 'Percent']].drop_duplicates()
    df_places = df_places.sort_values(['County Name', 'Geography', 'Percent'], ascending=[True, True, False]).reset_index(drop=True)


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod0 = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_prod = df_prod0[['Disability Type', 'Population']].drop_duplicates()
            df_pct  = df_prod0[['Disability Type', 'Percent'   ]].drop_duplicates()
            df_plot = df_pct.copy()
            df_plot['Percent of Population'] = round(df_plot['Percent'] * 100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)


