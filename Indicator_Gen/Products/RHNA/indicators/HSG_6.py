

def re_remove_post(x, exp = ':'):
    try: x = x.split(exp, 1)[0]
    except: pass
    return x

def re_remove_pre(x, exp = ':  '):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x


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

    df_places_a = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR}a Places ACS5.xlsx')
    df_places_b = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR}b Places ACS5.xlsx')
    df_places_a['Type'] = 'Kitchen'
    df_places_b['Type'] = 'Plumbing'
    df_places = pd.concat([df_places_a, df_places_b])

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Housing Issue'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True)
    df_places['Percent'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography'])['Households'].transform('sum')
    df_places['Housing Tenure'] = df_places['Housing Issue'].apply(re_remove_post)
    df_places['Housing Issue' ] = df_places['Housing Issue'].apply(re_remove_pre )

    df_places = df_places[['County Name', 'Geography', 'Housing Tenure', 'Housing Issue', 'Households', 'Percent']]
    df_places['Sort'] = pd.Categorical(df_places['Housing Issue'], ['Lacking kitchen facilities', 'Lacking plumbing facilities'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Housing Tenure', 'Sort'], ascending=[True, True, True, True]).drop(['Sort'], axis=1)
    df_places = df_places[df_places['Housing Issue'].isin(['Lacking kitchen facilities', 'Lacking plumbing facilities'])].reset_index(drop=True)


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Housing Issue', columns='Housing Tenure', values='Households').reset_index()
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Housing Issue', columns='Housing Tenure', values='Percent'   ).reset_index()
            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]

            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)


