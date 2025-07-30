


# Packages
import pandas as pd
import getpass
from pathlib import Path
from IPython.display import display



# File paths
user = getpass.getuser()
path_users = Path.home()
path_git = path_users / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
path_config0 = path_git / 'config'
path_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")



# Functions
path_func = path_config0 / 'Functions.py'

with path_func.open("r") as f:
    exec(f.read())



# Main ----------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    export=False

    indicators = ['Transit_1', 'Transit_2', 'Transit_4', 'Transit_5', 'Transit_6']

    dt_ntd = {
            'Transit_1' : 'Service Hours',
            'Transit_2' : 'Ridership',
            'Transit_4' : 'Fares',
            'Transit_5' : 'Operating Expenses',
            'Transit_6' : 'Revenue Sources'
    }

    sample_type = 'NTD'
  

    for indicator in indicators:
        print()
        print(indicator)
        wkbook = f'{indicator} {dt_ntd[indicator]}.xlsx'
        file_in = path_server / wkbook
        df = pd.read_excel(file_in, sheet_name='Data')

        year_start = df['Year'].min()
        year_end   = df['Year'].max()

        df_about = write_about(sample_type     = sample_type
                                , indicator    = indicator
                                , year_start   = year_start
                                , year_end     = year_end
                                , path_config0 = path_config0)
        display(df_about)

        file_out = path_server / wkbook
        with pd.ExcelWriter(file_out, engine='xlsxwriter') as writer:
            df_about.to_excel(writer, index=False, sheet_name='About', header=False)
            df      .to_excel(writer, index=False, sheet_name='Data')

    
        


