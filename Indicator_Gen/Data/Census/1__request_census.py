

print();print();print()



'''

This script is the first step in the pipeline to update indicators organized from data at the Census Bureau
Obtain API Key from the following source
https://api.census.gov/data/key_signup.html

Request parameters need to be updated using the config folder

'''



rerun=True
export=True
mpo='Yes'
unincorporated='Yes'




# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



from pathlib import Path
from xlwt.Workbook import *
from IPython.display import display
import sys

PATH_GIT = Path(__file__).parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'

FILE_API = PATH_CONFIG / 'api_key.txt'

sys.path.append(str(PATH_CONFIG))
import pre
import get


# SharePoint OneDrive paths
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')





# Main -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    # Read API key from ignored txt file
    with open(FILE_API, 'r') as file:
        api_key = file.read()

    # Prepare API request inputs
    yaml_census = pre.load_yaml()
    project, indicator, sample_type, estimate, geography, years_to_import, year_start, year_end, import_tab, margin_of_error, export_loc, folder, MOE_thresh, num_vars, percentages, weighted_by, metric = pre.api_request_params(yaml_census, rerun)

    # Send API requests
    df_census = get.get_data_any(api_key, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)
    display(df_census)


    # Export
    if export:

        file_out = PATH_ORIG / pre.set_download_name(indicator, estimate, sample_type, geography, margin_of_error)
        df_census.to_csv(file_out, index=False)
        print('Successfully exported!')


