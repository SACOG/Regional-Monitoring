




'''

This script is the first step in the pipeline to update indicators organized from data at the Census Bureau
Obtain API Key from the following source
https://api.census.gov/data/key_signup.html

'''




rerun=False
export=True
mpo='Yes'
unincorporated='Yes'




# Workspace ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



from pathlib import Path
import re
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



def set_workbook_name(indicator, estimate, sample_type, geography, margin_of_error, path_orig):

    if geography == 'PUMA':
        estimate = re.sub('ACS', 'PUMS', estimate)
    if sample_type == 'SUBJECT':
        estimate = re.sub('ACS', 'SUBJECT', estimate)
    if sample_type == 'DP':
        estimate = re.sub('ACS', 'DP', estimate)
    
    if margin_of_error == 'No':
        end = 'NoME_raw.csv'
    else:
        end = 'raw.csv'

    if sample_type == 'LEHD':
        export_name = f"{indicator}_{geography}_{sample_type}_{end}"
    else:
        export_name = f"{indicator}_{geography}_{estimate}_{end}"
    
    print(); print()
    print(f"Exporting {export_name} to the following location: ")
    print(path_orig)
    print()

    return export_name






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
    df_census = get.get_data_any(api_key, indicator, estimate, sample_type, geography, years_to_import, margin_of_error, import_tab)
    display(df_census)


    # Export
    if export:

        file_out = path_orig / set_workbook_name(indicator, estimate, sample_type, geography, margin_of_error, path_orig)
        df_census.to_csv(file_out, index=False)
        print('Successfully exported!')


