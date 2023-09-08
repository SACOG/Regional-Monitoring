import pandas as pd
import re
from typing import Optional, List
from .process_data_group import process_data_group


def dc_var_gen(df, 
               csv_path: Optional[str] = None, 
               data_group: Optional[str] = None, 
               variable_list: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
    
    # If neither variable_list nor csv_path is provided
    while variable_list is None and csv_path is None:
        try:
            user_input = input("Please enter a list of variables separated by a comma, semi-colon, or pipe (or type 'skip' to skip): ").strip()
            if user_input.lower() != 'skip':
                variable_list = re.split(r'[;|,]\s*', user_input)
            else:
                csv_path = input("Please enter the path to a CSV file containing the variable list (or type 'skip' to skip): ").strip()
                if csv_path.lower() == 'skip':
                    print("No variables provided. Full variable df output.")
                    return df
        except Exception as e:
            print(f"Exception occurred: {e}")
            return None
    
    # If csv_path is provided
    if csv_path:
        try:
            var_df = pd.read_csv(csv_path)
            variable_list = var_df['Variable Name'].tolist()
        except FileNotFoundError:
            print(f"File {csv_path} not found.")
            return None

    # Check if DataFrame exists
    if df is None:
        print("DataFrame could not be created. Exiting.")
        return None
    
    # Filter DataFrame by variable_list
    if variable_list is not None and len(variable_list) > 0:
        df = df[df['Variable Name'].isin(variable_list)]


    df = process_data_group(df, data_group)

    return df
