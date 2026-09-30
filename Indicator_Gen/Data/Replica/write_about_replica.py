

import pandas as pd
from pathlib import Path
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent.parent/'config'))
import functions as func


FILE_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data") / 'BikePed_1 Replica.xlsx'


# Main ----------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    indicator = 'BikePed_1'
    sample_type = 'Replica'

    df= pd.read_excel(FILE_SERVER, sheet_name='County_Trend_Thu',skiprows=1)

    df = df.dropna()
    df['Year'] = df['Season'].str.replace(' Fall', '')
    df['Year'] = df['Year'  ].str.replace(' Spring', '')
    df['Year'] = df['Year'].astype(int)
    year_start = df['Year'].min()
    year_end   = df['Year'].max()

    params = {
        'indicator': indicator
        , 'sample': sample_type
        , 'start_year': year_start
        , 'end_year': year_end
        , 'geo': 'Six-County Sacramento Region'
        , 'estimate': None
        , 'moe_thresh': None
    }

    df_about = func.write_about(params)
    display(df_about)
    print()

    with pd.ExcelWriter(FILE_SERVER, mode='a',engine='openpyxl',if_sheet_exists='replace') as writer:
        df_about.to_excel(writer, index=False, sheet_name='About', header=False)
    print(f'Exported to {str(FILE_SERVER)}')
    print('\n'*2)



    


