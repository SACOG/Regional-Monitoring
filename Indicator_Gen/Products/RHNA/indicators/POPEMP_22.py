


def re_remove_post(x, exp = ':'):
    try: x = str(x.split(exp, 1)[0])
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

    df_places = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR} Places ACS5.xlsx')

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Housing Type'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True)
    df_places['Housing Tenure'] = df_places['Housing Type'].apply(re_remove_post)
    df_places['Housing Type'  ] = df_places['Housing Type'].apply(re_remove_pre )

    df_places = df_places[['County Name', 'Geography', 'Households', 'Housing Tenure', 'Housing Type', 'Percentage']]
    df_places['Percent'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography', 'Housing Type'])['Households'].transform('sum')

    df_places['Sort'] = pd.Categorical(df_places['Housing Type'], ['Detached single-family homes', 'Attached single-family homes', 'Multi-family housing', 'Mobile homes', 'Boat, RV, van, or other'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Housing Tenure', 'Sort'], ascending=[True, True, True, True]).drop(['Sort'], axis=1).reset_index(drop=True)


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Housing Type', columns='Housing Tenure', values='Households').reset_index()
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Housing Type', columns='Housing Tenure', values='Percent'   ).reset_index()

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)
            var_map = {
                 'Detached single-family homes':'Detached<br>Single-Family'
                , 'Attached single-family homes':'Attached<br>Single-Family'
                , 'Multi-family housing':'Multi-Family'
                , 'Mobile homes':'Mobile<br>Homes'
                , 'Boat, RV, van, or other':'Boat, RV,<br>Van, or Other'
            }
            df_plot['Housing Type'] = df_plot['Housing Type'].map(var_map)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)


