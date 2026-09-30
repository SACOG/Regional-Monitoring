

import pandas as pd
from pathlib import Path
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / 'config'))
import functions as func


PATH_CONFIG  = Path(__file__).parent.parent.parent / 'Data' / 'Census' / 'config'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_SP = Path.home()/'Sacramento Area Council of Governments'/'Regional Monitoring and Reporting - Documents'/'Data'/'Next Gen of Mobility Solutions'/'Transit'
print('\n'*3)




if __name__ == '__main__':


    indicators = ['Transit_1', 'Transit_2', 'Transit_4', 'Transit_5', 'Transit_6', 'Transit_7', 'Transit_8']
    # indicators = ['Transit_1', 'Transit_2']

    dt_ntd = {
            'Transit_1' : 'Service Hours',
            'Transit_2' : 'Ridership',
            'Transit_4' : 'Fares',
            'Transit_5' : 'Operating Expenses',
            'Transit_6' : 'Revenue Sources',
            'Transit_7' : 'Cost Effectiveness',
            'Transit_8' : 'Vehicle Inventories'
    }

    sample_type = 'NTD'
    paths = [PATH_SERVER, PATH_SP]

    for indicator in indicators:
        print(indicator); print()
        wkbook = f'{indicator} {dt_ntd[indicator]}.xlsx'
        file_in = PATH_SERVER / wkbook
        df1 = pd.read_excel(file_in, sheet_name='Transit Operator')
        df2 = pd.read_excel(file_in, sheet_name='SACOG Region'    )
        print(wkbook)
        # display(df)

        year_start = df2['Year'].min()
        year_end   = df2['Year'].max()

        df_about = func.write_about(sample_type  = sample_type
                                    , indicator  = indicator
                                    , year_start = year_start
                                    , year_end   = year_end)
        # display(df_about)

        for path in paths:
            file_out = path / wkbook
            with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
                df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                df1     .to_excel(writer, index=False, sheet_name='Transit Operator'   )
                df2     .to_excel(writer, index=False, sheet_name='SACOG Region'       )
            print(f'Exported to {str(file_out)}')
        print('\n'*2)
    print('\n'*3)

    
        


