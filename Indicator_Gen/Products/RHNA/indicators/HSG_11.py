


import pandas as pd
from pathlib import Path
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()


PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_HCD = PATH_DATA / 'HCD_annualprogressreport.xlsx'


if __name__ == '__main__':

    ## Right now, using the "5th Cycle Full Summary", but will need to update to 6th or 7th I'm guessing
    df_hcd = pd.read_excel(FILE_HCD, sheet_name='5th Cycle Full Summary', skiprows=1)
    df_hcd = df_hcd[df_hcd['COUNTY'].isin(['EL DORADO', 'PLACER', 'SACRAMENTO', 'SUTTER', 'YOLO', 'YUBA'])][['COUNTY', 'JURS NAME', 'ABOVE MOD PERMITS', 'MOD PERMITS', 'LI PERMITS', 'VLI PERMITS']].reset_index(drop=True)

    df_hcd['COUNTY'   ] = df_hcd['COUNTY'   ].str.title()
    df_hcd['JURS NAME'] = df_hcd['JURS NAME'].str.title()

    df_hcd.loc[df_hcd['JURS NAME'].str.contains('County'), 'JURS NAME'] = 'Unincorporated'


    counties = list(df_hcd['COUNTY'].unique())

    for county in counties:

        print('\n'*2)
        print(county)

        df_sub = df_hcd[df_hcd['COUNTY'] == county]
        jurisdictions = list(df_sub['JURS NAME'].unique())

        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_sub_juris = df_sub[df_sub['JURS NAME'] == jurisdiction]
            df_sub_juris = df_sub_juris.drop(['COUNTY', 'JURS NAME'], axis=1)

            df_prod = df_sub_juris.copy()
            df_prod = df_prod.T.reset_index()
            df_prod.columns = ['Income Group', 'Number of Permits']
            var_map = {
                'ABOVE MOD PERMITS': 'Above Moderate',
                'MOD PERMITS': 'Moderate',
                'LI PERMITS': 'Low',
                'VLI PERMITS': 'Very Low'
            }
            df_prod['Income Group'] = df_prod['Income Group'].map(var_map)
            df_plot = df_prod.copy()

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)

