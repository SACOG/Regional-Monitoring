


import pandas as pd
from pathlib import Path
from tqdm import tqdm
import time
import warnings
import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()


def re_remove_post(x, exp = ':'):
    try: x = str(x.split(exp, 1)[0])
    except: pass
    return x

def re_remove_pre(x, exp = ': '):
    try: x = str(x.split(exp, 1)[1])
    except: pass
    return x

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

warnings.filterwarnings("ignore")



if __name__ == '__main__':

    df_places_a = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR}a Places ACS5.xlsx')
    df_places_b = pd.read_excel(PATH_DATA / f'RHNA_{INDICATOR}b Places ACS5.xlsx')
    df_places = pd.concat([df_places_a, df_places_b])

    df_places['NAME'] = df_places['NAME'].str.replace(' CDP, California' , '', regex=True)
    df_places['NAME'] = df_places['NAME'].str.replace(' city, California', '', regex=True)
    df_places = df_places.rename(columns={'NAME':'Geography', 'Variable': 'Year Moved to Current Residence'})
    df_places = df_places[df_places['Year'] == df_places['Year'].max()].reset_index(drop=True)
    df_places['Housing Tenure'] = df_places['Year Moved to Current Residence'].apply(re_remove_post)
    df_places['Year Moved to Current Residence'     ] = df_places['Year Moved to Current Residence'].apply(re_remove_pre )

    df_places = df_places[['County Name', 'Geography', 'Households', 'Housing Tenure', 'Year Moved to Current Residence', 'Percentage']]
    df_places['Percent'] = df_places['Households'] / df_places.groupby(['County Name', 'Geography', 'Year Moved to Current Residence'])['Households'].transform('sum')

    df_places['Sort'] = pd.Categorical(df_places['Year Moved to Current Residence'], ['Moved in 2021 or later', 'Moved in 2018 to 2020', 'Moved in 2010 to 2017', 'Moved in 2000 to 2009', 'Moved in 1999 or earlier'])
    df_places = df_places.sort_values(['County Name', 'Geography', 'Housing Tenure', 'Sort'], ascending=[True, True, True, False]).drop(['Sort'], axis=1).reset_index(drop=True)


    counties = list(df_places['County Name'].unique())

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_places_sub = df_places[df_places['County Name'] == county]
        jurisdictions = df_places_sub['Geography'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_prod = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Year Moved to Current Residence', columns='Housing Tenure', values='Households').reset_index()
            df_pct  = df_places_sub[df_places_sub['Geography'] == jurisdiction].pivot_table(index='Year Moved to Current Residence', columns='Housing Tenure', values='Percent'   ).reset_index()

            df_plot = df_places_sub[df_places_sub['Geography'] == jurisdiction]
            df_plot['Year Moved to Current Residence'] = df_plot['Year Moved to Current Residence'].str.replace('Moved in ', '')
            df_plot['Percent of Households'] = round(df_plot['Percent']*100, 1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod, df_pct)

