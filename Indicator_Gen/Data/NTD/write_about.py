
def print2(): print(); print()
def print3(): print(); print(); print()
print3()




import pandas as pd
from pathlib import Path
from IPython.display import display
import sys


PATH_GIT = Path(__file__).parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_SP = Path.home()/'Sacramento Area Council of Governments'/'Regional Monitoring and Reporting - Documents'/'Data'/'Next Gen of Mobility Solutions'/'Transit'

sys.path.append(str(PATH_CONFIG0))
import functions as func






# Main ----------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':


    indicators = ['Transit_1', 'Transit_2', 'Transit_4', 'Transit_5', 'Transit_6', 'Transit_7']
    # indicators = ['Transit_1', 'Transit_2']

    dt_ntd = {
            'Transit_1' : ['Service Hours SACOG', 'Service Hours'],
            'Transit_2' : ['Ridership SACOG', 'Ridership'],
            'Transit_4' : ['Fares SACOG', 'Fares'],
            'Transit_5' : ['Operating Expenses SACOG', 'Operating Expenses'],
            'Transit_6' : ['Revenue Sources SACOG', 'Revenue Sources'],
            'Transit_7' : ['Cost Effectiveness SACOG', 'Cost Effectiveness']
    }

    sample_type = 'NTD'
    paths = [PATH_SERVER, PATH_SP]


    for indicator in indicators:
        print(indicator); print()
        for ii in dt_ntd[indicator]:
            wkbook = f'{indicator} {ii}.xlsx'
            file_in = PATH_SERVER / wkbook
            df = pd.read_excel(file_in, sheet_name='Data')
            print(wkbook)
            # display(df)

            year_start = df['Year'].min()
            year_end   = df['Year'].max()

            df_about = func.write_about(sample_type  = sample_type
                                        , indicator  = indicator
                                        , year_start = year_start
                                        , year_end   = year_end)
            # display(df_about)

            if 'SACOG' in ii:
                df_about.loc[df_about['Indicator']=='Geography', indicator] = 'SACOG 6-County Region'

            for path in paths:
                file_out = path / wkbook
                with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
                    df_about.to_excel(writer, index=False, sheet_name='About', header=False)
                    df      .to_excel(writer, index=False, sheet_name='Data')
                print(f'Exported to {str(file_out)}')
            print()
        print2()
    print3()

    
        


