



RERUN=False
EXPORT=False




# Workspace --------------------------------------------------------------------------------------------------------


from pathlib import Path
from IPython.display import display


PATH_GIT = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen'
PATH_CODE    = PATH_GIT / 'Data' / 'BLS'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'

FILE_API = PATH_CONFIG / 'api_key.txt'

import sys
sys.path.append(str(PATH_CONFIG))
import pre
import get


PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\BLS')





# Main ---------------------------------------------------------------------------------------------------------------------------------



if __name__ == '__main__':

    # Read API key from ignored txt file
    with open(FILE_API, 'r') as file:
        api_key = file.read()

    # Prepare API request inputs
    yaml_bls = pre.load_yaml()
    dt_params = pre.api_request_params(yaml_bls, RERUN)

    # Send API requests
    df_bls = get.get_data_any(api_key, dt_params, yaml_bls)
    display(df_bls)


    if EXPORT:

        file_out = PATH_ORIG / pre.set_download_name(dt_params['Indicator'], dt_params['Geography'])
        df_bls.to_csv(file_out, index=False)
        print('Successfully exported!')

