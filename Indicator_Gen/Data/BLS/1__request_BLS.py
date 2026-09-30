

# Workspace --------------------------------------------------------------------------------------------------------


from pathlib import Path
from IPython.display import display

import sys
sys.path.append(str(Path(__file__).parent/'config'))
import pre
import get

FILE_API = Path(__file__).parent/'config' / 'api_key.txt'
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\BLS')




# Main ---------------------------------------------------------------------------------------------------------------------------------



RERUN=False
EXPORT=True



if __name__ == '__main__':

    # Read API key from ignored txt file
    with open(FILE_API, 'r') as file:
        api_key = file.read()

    # Prepare API request inputs
    yaml_bls = pre.load_yaml()
    params = pre.api_request_params(yaml_bls, RERUN)

    # Send API requests
    df_bls = get.get_data_any(api_key, params, yaml_bls)
    display(df_bls)


    if EXPORT:

        file_out = PATH_ORIG / pre.set_download_name(params['Indicator'], params['Geography'])
        df_bls.to_csv(file_out, index=False)
        print('Successfully exported!')

