

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


def re_remove_post(x, exp = ':'):
    try: x = x.split(exp, 1)[0]
    except: pass
    return x

def re_remove_pre(x, exp = ':  '):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x



if __name__ == '__main__':

    df_places = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR} Places ACS5.xlsx')

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Disability Status'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True)
    df_places['Employment Status'] = df_places['Disability Status'].apply(re_remove_post)
    df_places['Disability Status'] = df_places['Disability Status'].apply(re_remove_pre )
    df_places['Percent'] = df_places['Population'] / df_places.groupby(['County Name', 'Geography', 'Disability Status'])['Population'].transform('sum')

    df_places = df_places[['County Name', 'Geography', 'Employment Status', 'Disability Status', 'Population', 'Percent']]
    df_places = df_places.sort_values(['County Name', 'Geography', 'Employment Status', 'Percent'], ascending=[True, True, True, False]).reset_index(drop=True)


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Employment Status', columns='Disability Status', values='Population').reset_index()
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Employment Status', columns='Disability Status', values='Percent'   ).reset_index()

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_plot['Percent of Population'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

