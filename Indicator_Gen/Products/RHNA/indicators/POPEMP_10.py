


def re_remove_post(x, exp = ':'):
    try: x = str(x.split(exp, 1)[0])
    except: pass
    return x

def re_remove_pre(x, exp = ':  '):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x



import numpy as np
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

    df_places_a = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR}a Places ACS5.xlsx')
    df_places_b = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR}b Places ACS5.xlsx')
    df_places = pd.concat([df_places_a, df_places_b])

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True).rename(columns={'NAME':'Geography', 'Variable': 'Earnings', 'Percentage':'Percent'})
    df_places['Location'] = df_places['Earnings'].apply(re_remove_post)
    df_places['Earnings'] = df_places['Earnings'].apply(re_remove_pre )

    df_places = df_places[['County Name', 'Geography', 'Earnings', 'Location', 'Population', 'Percent']]

    df_places['Sort'] = pd.Categorical(df_places['Earnings'], ['75k or more', '50k to 75k', '25k to 50k', '10k to 25k', 'Less than 10k'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Location', 'Sort'], ascending=[True, True, True, False]).drop(['Sort'], axis=1).reset_index(drop=True)

    conditions = [
          df_places['Earnings'] == 'Less than 10k'
        , df_places['Earnings'] == '10k to 25k'
        , df_places['Earnings'] == '25k to 50k'
        , df_places['Earnings'] == '50k to 75k'
        , df_places['Earnings'] == '75k or more'
    ]
    choices = ['Less than $10k', '$10k to $25k', '$25k to $50k', '$50k to $75k', '$75k or more']
    df_places['Earnings'] = np.select(conditions, choices, default='no')


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        rhna.print2()
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod, df_pct = rhna.acs_pivot(INDICATOR, df_places_sub, county, jurisdiction, 'Location', 'Population', 'Earnings')

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

