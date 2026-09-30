

import sys
from pathlib import Path

import pandas as pd
from IPython.display import display

sys.path.append(str(Path(__file__).parent.parent.parent/'config'))
import functions as func

FILE_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data") / 'Jobs_6 Tradeable Sectors.xlsx'
FILE_SP = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\Economy\Jobs\Jobs_6 Tradeable') / 'Jobs_6 Tradeable Sectors.xlsx'


# Main ----------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':


    indicator = 'Jobs_6'
    sample_type = 'EDD'
    files = [FILE_SERVER, FILE_SP]

    df= pd.read_excel(FILE_SERVER, sheet_name='Region Tradeable')

    year_start = df['Year'].min()
    year_end   = df['Year'].max()

    params = {
        'indicator': indicator
        , 'sample': sample_type
        , 'start_year': year_start
        , 'end_year': year_end
        , 'geo': 'SACOG Six-County Region'
        , 'estimate': None
        , 'moe_thresh': None
    }

    df_about = func.write_about(params)
    display(df_about)
    print()

    for file_out in files:
        with pd.ExcelWriter(file_out, mode='a',engine='openpyxl',if_sheet_exists='replace') as writer:
            df_about.to_excel(writer, index=False, sheet_name='About', header=False)
        print(f'Exported to {str(file_out)}')
    print('\n'*2)



    


