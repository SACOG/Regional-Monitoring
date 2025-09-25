




'''

This script is the first step in the pipeline to update indicators organized from data at the Census Bureau
Obtain API Key from the following source
https://api.census.gov/data/key_signup.html

Request parameters need to be updated using the config folder

'''



rerun=False
export=True
mpo='Yes'
unincorporated='Yes'



print();print();print()

# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



from pathlib import Path
from xlwt.Workbook import *
from IPython.display import display
import sys

path_git = Path(__file__).parent.parent.parent
path_code    = path_git / 'Data' / 'Census'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'


sys.path.append(str(path_config))
import pre
import get




# SharePoint OneDrive paths
path_sp = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_orig = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'Census'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'


    


# Main -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':

    # Read API key from ignored txt file
    file_api = path_config / 'api_key.txt'
    with open(file_api, 'r') as file:
        api_key = file.read()

    # Prepare API request inputs
    yaml_census = pre.load_yaml(path_config)
    project, indicator, sample_type, estimate, geography, years_to_import, year_start, year_end, import_tab, margin_of_error, export_loc, folder, MOE_thresh, num_vars, percentages, weighted_by, metric = pre.api_request_params(yaml_census, rerun)

    # Send API requests
    df_census = get.get_data_any(api_key, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab, path_config)
    display(df_census)


    # Export
    if export:

        file_out = path_orig / pre.set_download_name(indicator, estimate, sample_type, geography, margin_of_error, path_orig)
        df_census.to_csv(file_out, index=False)
        print('Successfully exported!')


