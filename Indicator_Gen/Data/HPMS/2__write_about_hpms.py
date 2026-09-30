

import pandas as pd
from pathlib import Path
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent.parent/'config'))
import functions as func


FILE_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data") / 'VMT_3 HPMS.xlsx'
FILE_SP = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Next Gen of Mobility Solutions\VMT') / 'VMT_3 HPMS.xlsx'


# Main ----------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':


    indicator = 'VMT_3'
    sample_type = 'HPMS'
    files = [FILE_SERVER, FILE_SP]

    year_start = 2001
    year_end   = 2024

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



    


