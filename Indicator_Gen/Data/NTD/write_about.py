
print(); print(); print()

import pandas as pd
from pathlib import Path
from IPython.display import display
import sys


PATH_GIT = Path(__file__).parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")

sys.path.append(str(PATH_CONFIG0))
import functions as func



export=False



# Main ----------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':


    # indicators = ['Transit_1', 'Transit_2', 'Transit_4', 'Transit_5', 'Transit_6']
    indicators = ['Transit_1', 'Transit_2']

    dt_ntd = {
            'Transit_1' : 'Service Hours SACOG',
            'Transit_2' : 'Ridership SACOG'#,
            # 'Transit_4' : 'Fares',
            # 'Transit_5' : 'Operating Expenses',
            # 'Transit_6' : 'Revenue Sources'
    }

    sample_type = 'NTD'
  

    for indicator in indicators:
        print(indicator); print()
        wkbook = f'{indicator} {dt_ntd[indicator]}.xlsx'
        file_in = PATH_SERVER / wkbook
        df = pd.read_excel(file_in, sheet_name='Data')
        display(df)

        year_start = df['Year'].min()
        year_end   = df['Year'].max()

        df_about = func.write_about(sample_type     = sample_type
                                    , indicator    = indicator
                                    , year_start   = year_start
                                    , year_end     = year_end)
        display(df_about)

        file_out = PATH_SERVER / wkbook
        with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
            df_about.to_excel(writer, index=False, sheet_name='About', header=False)
            df      .to_excel(writer, index=False, sheet_name='Data')
        print(); print(); print()

    
        


