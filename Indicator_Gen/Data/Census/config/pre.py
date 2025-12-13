



'''

Functions:

load_yaml()
api_request_params()

'''



import numpy as np
import pandas as pd
from pathlib import Path
import os
import re
from datetime import datetime
import yaml
from IPython.display import display


PATH_GIT = Path(__file__).parent.parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'Census'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')


def load_yaml():

    PATH_YAML = PATH_CONFIG / 'census.yaml'

    try:
        with open(PATH_YAML, 'r') as yaml_file:
            yaml_census = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {PATH_YAML} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return yaml_census




def api_request_params(yaml_census, rerun):
    
    print(); print()
    print('Census Bureau import parameters:')
    print()


    if rerun:
        PATH_RUNS = PATH_CONFIG / 'runs'
        list_files = [str(entry) for entry in PATH_RUNS.iterdir() if entry.is_file()]
        dt_mod = {}

        for file in list_files:
            time_mod = os.path.getmtime(file)
            time_mod = datetime.fromtimestamp(time_mod).strftime("%Y-%m-%d %H:%M:%S")
            dt_mod[time_mod] = file

        most_recent = sorted(list(dt_mod.keys()), reverse=True)[0]
        file_run = dt_mod[most_recent]
        df_run = pd.read_csv(file_run, sep=': ', names=['Parameter', 'Input'])
        print(); display(df_run); print()

        def remove_colon(x):
            return x.replace(':', '')

        df_run['Parameter'] = df_run['Parameter'].apply(remove_colon)
        project         = df_run[df_run['Parameter'] == 'Project'        ]['Input'].values[0]
        indicator       = df_run[df_run['Parameter'] == 'Indicator Name' ]['Input'].values[0]
        sample_type     = df_run[df_run['Parameter'] == 'Sample'         ]['Input'].values[0]
        estimate        = df_run[df_run['Parameter'] == 'Estimate'       ]['Input'].values[0]
        geography       = df_run[df_run['Parameter'] == 'Geography'      ]['Input'].values[0]
        years_to_import = df_run[df_run['Parameter'] == 'Years Imported' ]['Input'].values[0]
        import_tab      = df_run[df_run['Parameter'] == 'Import Tab'     ]['Input'].values[0]
        margin_of_error = df_run[df_run['Parameter'] == 'Margin of Error']['Input'].values[0]
        export_loc  = yaml_census['Indicators'][project][indicator]['sp_location'        ]
        folder      = yaml_census['Indicators'][project][indicator]['folder'             ]
        MOE_thresh  = yaml_census['Indicators'][project][indicator]['MOE_threshold'      ]
        num_vars    = yaml_census['Indicators'][project][indicator]['number_of_variables']
        percentages = yaml_census['Indicators'][project][indicator]['percentages'        ]
        weighted_by = yaml_census['Indicators'][project][indicator]['weighted_by'        ]
        metric      = yaml_census['Indicators'][project][indicator]['metric'             ]
        if sample_type != 'LEHD':
            years_to_import = years_to_import.split(', ')
            years_to_import = [int(year) for year in years_to_import]
            year_end   = np.max(years_to_import)
            year_start = np.min(years_to_import)


    else:

        print('---------------------------------------------------------------------------------------------------------------------------------------')
        print()
        print('Projects available: ')
        display(yaml_census['Project']); print()
        print('Which project are you pulling data for?'); print()
        project = input()
        assert project in yaml_census['Project'], 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()
        print('Indicators available:'); print()
        display(list(yaml_census['Indicators'][project].keys())); print()
        print('Which indicator do you need to rerun?'); print()
        indicator = input()
        assert indicator in list(yaml_census['Indicators'][project].keys()), 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        export_loc  = yaml_census['Indicators'][project][indicator]['sp_location'        ]
        folder      = yaml_census['Indicators'][project][indicator]['folder'             ]
        MOE_thresh  = yaml_census['Indicators'][project][indicator]['MOE_threshold'      ]
        num_vars    = yaml_census['Indicators'][project][indicator]['number_of_variables']
        percentages = yaml_census['Indicators'][project][indicator]['percentages'        ]
        weighted_by = yaml_census['Indicators'][project][indicator]['weighted_by'        ]
        metric      = yaml_census['Indicators'][project][indicator]['metric'             ]

        print()
        display(yaml_census['Indicators'][project][indicator])
        sample_types = yaml_census['Indicators'][project][indicator]['sample']
        if isinstance(sample_types, list):
            print('Samples available:')
            display(sample_types); print()
            print('Which sample do you want to pull data from?')
            sample_type = input()
            assert sample_type in sample_types, 'Unacceptable input, please choose from options displayed above'
        else:
            sample_type = yaml_census['Indicators'][project][indicator]['sample']

        print()
        print('Estimates available:')
        display(list(yaml_census['Samples'][sample_type].keys())); print()
        print('Which estimate do you want to pull data from?'); print()
        estimate = input()
        assert estimate in list(yaml_census['Samples'][sample_type].keys()), 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')


        print()
        print('Geographies available:'); print()
        display(yaml_census['Samples'][sample_type][estimate]['geographies_available']); print()
        print('Which geography do you want to pull data for?'); print()
        geography = input()
        assert geography in yaml_census['Samples'][sample_type][estimate]['geographies_available'], 'Unacceptable input, please choose from options displayed above'
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()
        if sample_type != 'LEHD':
            print('Years available:')
            display(yaml_census['Samples'][sample_type][estimate]['years_available']); print()
            print('Do you want to pull data for all years available?  Select Yes/No: '); print()
            all_years = input()
            if all_years == 'Yes':
                years_to_import = yaml_census['Samples'][sample_type][estimate]['years_available']
                years = ', '.join([str(year) for year in years_to_import])
            elif all_years == 'No':
                print()
                print('Please type which years you want to pull data from, separated by commas:'); print()
                years = input()
                if ',' in years:
                    years_to_import = years.split(', ')
                    years_to_import = [int(year) for year in years_to_import]
                else:
                    years_to_import = [int(years)]
            else:
                assert all_years in ['Yes', 'No'], "Unacceptable input, please type 'Yes' or 'No'"
            
            print()
            year_end   = np.max(years_to_import)
            year_start = np.min(years_to_import)
        else:
            print()
            print("LEHD organizes data quarterly and the API requires a 'timeseries' call.")
            years_to_import = 'timeseries'
            years = 'timeseries'
            year = 'timeseries' # TODO: might need to include this on return statement for LEHD
            print()


        import_tab = yaml_census['Import Geographies'][geography]

        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()
        if sample_type not in ['LEHD', 'DEC']:
            print('Do you want to pull the Margin of Error estimates?  Select Yes/No: '); print()
            margin_of_error = input()
        else:
            print(); print('LEHD has margin of error terms available but not through API.  DEC has no margin of error terms available')
            margin_of_error = 'No'
        assert margin_of_error in ['Yes', 'No'], "Unacceptable input, please type 'Yes' or 'No'"

        file_run_set = Path(__file__).parent / 'runs' / f'{indicator}.txt'
        with open(file_run_set, 'w') as f:
            f.write(f"Project: {project}\n")
            f.write(f"Indicator Name: {indicator}\n")
            f.write(f"Export Location: {export_loc}\n")
            f.write(f"Folder: {folder}\n")
            f.write(f"Sample: {sample_type}\n")
            f.write(f"Estimate: {estimate}\n")
            f.write(f"Geography: {geography}\n")
            f.write(f"Years Imported: {years}\n")
            f.write(f"Import Tab: {import_tab}\n")
            f.write(f"Margin of Error: {margin_of_error}\n")

    return project, indicator, sample_type, estimate, geography, years_to_import, year_start, year_end, import_tab, margin_of_error, export_loc, folder, MOE_thresh, num_vars, percentages, weighted_by, metric




def set_download_name(indicator, estimate, sample_type, geography, margin_of_error):

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
    print(PATH_ORIG)
    print()

    return export_name


