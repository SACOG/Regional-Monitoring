

import pandas as pd
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()

PATH_SERVER = Path(r'P:\Employment Inventory\Employment_2025\Processed_Clean\EDD')
INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]

FILE_EDD = Path(r'P:\Employment Inventory\Employment_2025\Processed_Clean\EDD\QC\EDD_2025q2_QC_top_5.xlsx')

if __name__ == '__main__':

    df_edd=pd.read_excel(FILE_EDD, sheet_name='jurisdiction')
    df_edd = df_edd.groupby(['county', 'juris'], as_index=False).head(10)
    
    counties = df_edd['county'].unique()
    
    print()
    for county in counties:
        
        print('\n'*2)
        print(f'{county} County')
        df_county = df_edd[df_edd['county']==county]
        jurisdictions = df_county['juris'].unique()
        print()
        
        for jurisdiction in jurisdictions:

            print(jurisdiction)
            df_prod = df_county[df_county['juris']==jurisdiction].reset_index(drop=True)
            df_prod = df_prod[['legal_name', 'trade_name']].rename(columns={'legal_name':'Legal Name', 'trade_name':'Trade Name'})
    
            rhna.export_rhna(county, jurisdiction, INDICATOR, params, df_prod)


