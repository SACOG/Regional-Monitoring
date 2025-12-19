


def print2(): print(); print()



'''

Functions:

load_yaml()
api_request_params()

'''



import numpy as np
import pandas as pd
from pathlib import Path
import os
from datetime import datetime
import yaml
from IPython.display import display


PATH_GIT = Path(__file__).parent.parent.parent.parent
PATH_CODE    = PATH_GIT / 'Data' / 'BLS'
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_CODE / 'config'
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')


def load_yaml():

    PATH_YAML = PATH_CONFIG / 'bls.yaml'

    try:
        with open(PATH_YAML, 'r') as yaml_file:
            yaml_bls = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {PATH_YAML} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return yaml_bls




def api_request_params(yaml_bls, rerun):
    
    print2()
    print('BLS import parameters:')
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
        project   = df_run[df_run['Parameter'] == 'Project'  ]['Input'].values[0]
        indicator = df_run[df_run['Parameter'] == 'Indicator']['Input'].values[0]
        survey    = df_run[df_run['Parameter'] == 'Survey'   ]['Input'].values[0]

        # if survey in ['SM', 'CE', 'EN']:
        #     data_type_text = df_run[df_run['Parameter'] == 'Data Type']['Input'].values[0]
        #     if survey in ['EN']:
        #         size_code_text  = df_run[df_run['Parameter'] == 'Employer Size' ]['Input'].values[0]
        #         owner_code_text = df_run[df_run['Parameter'] == 'Ownership Type']['Input'].values[0]
        # if survey in ['LA']:
        #     measure_type_text = df_run[df_run['Parameter'] == 'Measure Type']['Input'].values[0]
        data_type_text = df_run[df_run['Parameter'] == 'Data Type']['Input'].values[0]
        size_code_text  = df_run[df_run['Parameter'] == 'Employer Size' ]['Input'].values[0]
        owner_code_text = df_run[df_run['Parameter'] == 'Ownership Type']['Input'].values[0]
        measure_type_text = df_run[df_run['Parameter'] == 'Measure Type']['Input'].values[0]
        seasonal_code   = df_run[df_run['Parameter'] == 'Seasonal Adjustment' ]['Input'].values[0]
        geography       = df_run[df_run['Parameter'] == 'Geography'           ]['Input'].values[0]
        years_to_import = df_run[df_run['Parameter'] == 'Years Imported'      ]['Input'].values[0]

        export_loc  = yaml_bls['Indicators'][project][indicator]['sp_location']
        folder      = yaml_bls['Indicators'][project][indicator]['folder'     ]
        percentages = yaml_bls['Indicators'][project][indicator]['percentages']
        weighted_by = yaml_bls['Indicators'][project][indicator]['weighted_by']

        years_to_import = years_to_import.split(', ')
        years_to_import = [int(year) for year in years_to_import]
        year_end   = np.max(years_to_import)
        year_start = np.min(years_to_import)



    else:

        while True:
            try:
                print('---------------------------------------------------------------------------------------------------------------------------------------')
                print()
                print('Projects available: ')
                projects = yaml_bls['Project']
                display(projects); print()
                print('Which project are you pulling data for?'); print()
                project = input()
                if project in projects:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(projects)
                print()
                print('---------------------------------------------------------------------------------------------------------------------------------------')


        while True:
            try:
                print()
                print('Indicators available:'); print()
                indicators = list(yaml_bls['Indicators'][project].keys())
                display(indicators); print()
                print('Which indicator do you need to rerun?'); print()
                indicator = input()
                if indicator in indicators:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(indicators)
                print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        export_loc  = yaml_bls['Indicators'][project][indicator]['sp_location']
        folder      = yaml_bls['Indicators'][project][indicator]['folder'     ]
        percentages = yaml_bls['Indicators'][project][indicator]['percentages']
        weighted_by = yaml_bls['Indicators'][project][indicator]['weighted_by']


        while True:
            try:
                print()
                display(yaml_bls['Indicators'][project][indicator])
                surveys = yaml_bls['Indicators'][project][indicator]['survey']
                if isinstance(surveys, list):
                    print('Surveys available:')
                    display(surveys); print()
                    print('Which survey do you want to pull data from?')
                    survey = input()            
                else:
                    survey = yaml_bls['Indicators'][project][indicator]['survey']
                if survey in surveys:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(surveys)
                print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()

        if survey in ['SM', 'CE', 'EN']:
            while True:
                try:
                    print('Data types available:'); print()
                    data_types = yaml_bls['Surveys'][survey]['data_type']
                    display(data_types); print()
                    print('Which data type do you want to request?'); print()
                    data_type_text = input()
                    if data_type_text in data_types:
                        print()
                        break
                    else:
                        print()
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print()
                    print("Invalid choice. Please choose from options outlined here: ");print(data_types)
                    print()
        else:
            data_type_text=None
            pass

        if survey in ['EN']:
            while True:
                try:
                    print()
                    print('Employer sizes available:'); print()
                    size_types = yaml_bls['Surveys'][survey]['size_type']
                    display(size_types); print()
                    print('Which employer size category do you want to request?'); print()
                    size_code_text = input()
                    if size_code_text in size_types:
                        print()
                        break
                    else:
                        print()
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print()
                    print("Invalid choice. Please choose from options outlined here: ");print(size_types)
                    print()
        else:
            size_code_text=None
            pass

        if survey in ['EN']:
            while True:
                try:
                    print()
                    print('Ownership categories available:'); print()
                    owner_types = yaml_bls['Surveys'][survey]['owner_type']
                    display(owner_types); print()
                    print('Which ownership category do you want to request?'); print()
                    owner_code_text = input()
                    if owner_code_text in owner_types:
                        print()
                        break
                    else:
                        print()
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print()
                    print("Invalid choice. Please choose from options outlined here: ");print(owner_types)
                    print()
        else:
            owner_code_text=None
            pass
        
        if survey in ['LA']:
            while True:
                try:
                    print('Measure types available:'); print()
                    measure_types = yaml_bls['Surveys'][survey]['measure_type']
                    display(measure_types); print()
                    print('Which measure type do you want to request?'); print()
                    measure_type_text = input()
                    if measure_type_text in measure_types:
                        print()
                        break
                    else:
                        print()
                        print("Invalid choice. Please try again.")
                except ValueError:
                    print()
                    print("Invalid choice. Please choose from options outlined here: ");print(measure_types)
                    print()
        else:
            measure_type_text=None
            pass



        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')


        while True:
            try:
                print()
                print('Do you want seasonally adjusted estimates?  Select Yes/No: '); print()
                seasonal_adj = input()
                if seasonal_adj == 'Yes':
                    seasonal_code = 'S'
                if seasonal_adj == 'No':
                    seasonal_code = 'U'
                if seasonal_code in ['U', 'S']:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(['U', 'S'])
                print()
        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')



        while True:
            try:
                print()
                print('Geographies available:'); print()
                geographies = yaml_bls['Surveys'][survey]['geographies_available']
                display(geographies); print()
                print('Which geography do you want to pull data for?'); print()
                geography = input()
                if geography in geographies:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(['U', 'S'])
                print()

        print()
        print('---------------------------------------------------------------------------------------------------------------------------------------')

        while True:
            try:
                print()
                print('Years available:')
                display(yaml_bls['Surveys'][survey]['years_available']); print()
                print('Do you want to pull data for all years available?  Select Yes/No: '); print()
                all_years = input()
                if all_years == 'Yes':
                    years_to_import = yaml_bls['Surveys'][survey]['years_available']
                    years = ', '.join([str(year) for year in years_to_import])
                if all_years == 'No':
                    print()
                    print('Please type which years you want to pull data from, separated by commas:'); print()
                    years = input()
                    if ',' in years:
                        years_to_import = years.split(', ')
                        years_to_import = [int(year) for year in years_to_import]
                    else:
                        years_to_import = [int(years)]
                if all_years in ['Yes', 'No']:
                    print()
                    break
                else:
                    print()
                    print("Invalid choice. Please try again.")
            except ValueError:
                print()
                print("Invalid choice. Please choose from options outlined here: ");print(['U', 'S'])
                print()
        
        print()
        year_end   = np.max(years_to_import)
        year_start = np.min(years_to_import)

        print('---------------------------------------------------------------------------------------------------------------------------------------')

        print()


        file_config_set = PATH_CONFIG / 'runs' / f'{indicator}.txt'
        with open(file_config_set, 'w') as f:
            f.write(f"Project: {project}\n")
            f.write(f"Indicator: {indicator}\n")
            f.write(f"Export Location: {export_loc}\n")
            f.write(f"Folder: {folder}\n")
            f.write(f"Survey: {survey}\n")
            f.write(f"Data Type: {data_type_text}\n")
            f.write(f"Employer Size: {size_code_text}\n")
            f.write(f"Ownership Type: {owner_code_text}\n")
            f.write(f"Measure Type: {measure_type_text}\n")
            f.write(f"Seasonal Adjustment: {seasonal_code}\n")
            f.write(f"Geography: {geography}\n")
            f.write(f"Years Imported: {years}\n")

    dt_result = {
        'Project': project,
        'Indicator': indicator,
        'Survey': survey,
        'Geography': geography,
        'Years': years_to_import,
        'Seasonal Code': seasonal_code,
        'Percentages': percentages,
        'Weighted By': weighted_by,
        'Data Type': data_type_text,
        'Size Code': size_code_text,
        'Owner Code': owner_code_text,
        'Measure Type': measure_type_text,
        'Export Location': export_loc,
        'SP Folder': folder
    }

    return dt_result




def set_download_name(indicator, geography):

    end = 'raw'
    export_name = f"{indicator}_{geography}_BLS_{end}.csv"
    
    print2()
    print(f"Exporting {export_name} to the following location: ")
    print(PATH_ORIG)
    print()

    return export_name


