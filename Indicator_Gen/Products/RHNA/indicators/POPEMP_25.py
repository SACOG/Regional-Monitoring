


from pathlib import Path
import pandas as pd
import numpy as np
import time
from tqdm import tqdm
import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()


PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

PATH_TYP = PATH_DATA / r'POPEMP_25\emp25_data\outputs\typologies'


if __name__ == '__main__':
    
    
    df = pd.read_csv(PATH_TYP / 'jurisdiction_typology_summary.csv')
    df = df[df['Typology']!='Totals'].reset_index(drop=True)
    df.columns = ['County', 'Jurisdiction', 'Typology', 'Owner occupied', 'Renter occupied']

    df = df.melt(id_vars=['County', 'Jurisdiction', 'Typology'], var_name='Housing Tenure', value_name='Households')
    df = df.pivot_table(index=['County', 'Jurisdiction', 'Housing Tenure'], columns='Typology', values = 'Households').reset_index()
    df = df.fillna(0)
    df = df.melt(id_vars=['County', 'Jurisdiction', 'Housing Tenure'], var_name='Typology', value_name='Households')
    df = df.pivot_table(index=['County', 'Jurisdiction', 'Typology'], columns='Housing Tenure', values = 'Households').reset_index()
    df = df.replace(0, np.nan)

    df['sort'] = pd.Categorical(df['Typology'], [
        'Susceptible to or Experiencing Displacement'
        , 'At Risk of or Experiencing Exclusion'
        , 'At Risk of or Experiencing Gentrification'
        , 'Stable Moderate/Mixed Income'
        , 'Other'
    ])
    df = df.sort_values(['County', 'Jurisdiction', 'sort'], ascending=[True, True, True]).drop('sort', axis=1).reset_index(drop=True)

    counties = df['County'].unique()

    for county in counties:
        
        print('\n'*2)
        print(county)
        time.sleep(2)

        df_sub = df[df['County'] == county]
        jurisdictions = df_sub['Jurisdiction'].unique()
        
        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_plot = df_sub[df_sub['Jurisdiction']==jurisdiction].drop(['County', 'Jurisdiction'], axis=1).melt(id_vars='Typology', var_name='Housing Tenure', value_name='Households')
            df_prod = df_sub[df_sub['Jurisdiction']==jurisdiction].drop(['County', 'Jurisdiction'], axis=1)

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)


    breakpoint()


