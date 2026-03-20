


from pathlib import Path
import pandas as pd
from tqdm import tqdm

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_DATA = Path(yaml_file['Path_Data'])
INDICATOR = Path(__file__).stem

FILE_HOUSING = Path.home() / r'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\Development\Housing Cost\Cost_5 Home Ownership'
PATH_OUT = Path.home() / 'Documents' / 'Projects' / 'Local' / 'RHNA' / 'Final Products'



if __name__ == '__main__':

    print('\n'*2)

    df_housing = pd.read_excel(FILE_HOUSING/'Cost_5 Places ACS5.xlsx',sheet_name='Places')

    df_housing = df_housing[
        (df_housing['Year'] == 2023)
        & (df_housing['Race/Ethnicity'] == 'All')
    ]
    df_housing = df_housing[['County Name', 'NAME', 'Year', 'Variable', 'Households']]

    counties = df_housing['County Name'].unique()

    for county in counties:

        print()
        print(county)
        df_county = df_housing[df_housing['County Name']==county]
        jurisdictions = df_county['NAME'].unique()
        print()

        for jurisdiction in tqdm(jurisdictions):

            tqdm.write(jurisdiction)

            df_juris = df_county[df_county['NAME'] == jurisdiction]
            path_tables = PATH_OUT / county.replace(' County', '') / jurisdiction / 'tables'
            file_table = path_tables / 'HSG_3_prod.csv'
            df_prod = pd.read_csv(file_table)
            df_prod = df_prod[['Vacancy Type', jurisdiction]]
            df_prod = df_prod[df_prod['Vacancy Type'].isin(['For rent', 'For sale only'])]
            df_prod['Variable'] = 'Owner occupied'
            df_prod.loc[df_prod['Vacancy Type']=='For rent', 'Variable'] = 'Renter occupied'
            df_juris = df_juris[['Variable', 'Households']]

            df_prod_sup = df_prod.merge(df_juris)

            df_prod_sup['Percent'] = df_prod_sup[jurisdiction]/df_prod_sup['Households']

            df_prod_sup.to_csv(path_tables/'HSG_3_prod_sup.csv', index=False)