

'''

This script is the first step in the pipeline to update indicators organized from data at the Census Bureau
Obtain API Key from the following source
https://api.census.gov/data/key_signup.html

Request parameters need to be updated using census.xlsx in the config folder
Every data release, the .py files in the config/step0 folder need to be reran


RERUN=True/False -> if True, recycles parameters from the most recent API request
EXPORT=True/False -> if True, exports requested data to desired file path

'''




# Workspace -------------------------------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
from IPython.display import display
import sys

sys.path.append(str(Path(__file__).parent/'config'))
import pre
import get

PATH_GIT = Path(__file__).parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'

FILE_API = PATH_CONFIG / 'api_key.txt'


# Network file paths for exporting
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')





# Main -------------------------------------------------------------------------------------------------------------------------------------------------------------



RERUN=False
EXPORT=True



if __name__ == '__main__':

    # Read API key from ignored txt file
    with open(FILE_API, 'r') as file:
        api_key = file.read()

    # Prepare API request inputs
    yaml_census = pre.load_yaml()
    params = pre.api_request_params(yaml_census, RERUN)

    # Send API requests
    df_census = get.get_data_any(api_key, params)
    display(df_census)


    # Export
    if EXPORT:

        file_out = PATH_ORIG / pre.set_download_name(params)
        df_census.to_csv(file_out, index=False)
        print('Successfully EXPORTed!')
        print('\n'*2)


