

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

PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'
FILE_FARMWORKERS = PATH_DATA / 'USDA' / 'USDA_FarmWorkers_Summarized.xlsx'


if __name__ == '__main__':

    df_usda = pd.read_excel(FILE_FARMWORKERS)
    counties = list(df_usda['County'].unique())

    for county in counties:

        print(county)

        path_county = PATH_OUT / county
        jurisdictions = [str(f.stem) for f in path_county.iterdir()]

        for jurisdiction in tqdm(jurisdictions, position=0):

            tqdm.write(jurisdiction)

            df_prod = df_usda[df_usda['County'] == county].drop('County', axis=1)
            df_plot = df_prod.melt(id_vars='Farm Worker', var_name='Year', value_name='Number of Farm Workers')
            df_plot['Year'] = df_plot['Year'].str.replace('Year ', '')

            fig = rhna.make_fig(INDICATOR, params, df_plot, county, jurisdiction)
            rhna.plot_rhna(fig, county, jurisdiction, INDICATOR, params)
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)


