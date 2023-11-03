import os
import pickle
import hashlib
from datetime import datetime, timedelta
from .get_raw_vars import raw_vars
from .data_group_vars import all_raw_vars, VAR_MAPPING, master_var_gen, master_vars

# Get the current directory of the script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

def check_and_update_pickle(pickle_file_name, data_func, *func_args):
    """
    Check if a pickle file needs to be updated based on the output of a provided function 
    and update it if necessary.

    Parameters:
    -----------
    pickle_file_name : str
        The name/path of the pickle file.
    data_func : callable
        The function to get the data.
    func_args : tuple
        The arguments to pass to the data function.

    Returns:
    --------
    bool
        True if the pickle file was updated, otherwise False.
    """
    def compute_md5(file_content):
        """Compute MD5 hash of given content."""
        return hashlib.md5(file_content).hexdigest()

    full_path = os.path.join(CURRENT_DIR, pickle_file_name)

    print(f'Checking if {full_path} needs to be updated')

    if not os.path.exists(full_path):
        print(f'{full_path} not detected. Creating it now.')
        with open(full_path, 'wb') as f:
            pickle.dump(data_func(*func_args), f)
        return True

    one_week_ago = datetime.now() - timedelta(days=28)
    one_day_ago = datetime.now() - timedelta(days=1)
    pickle_file_timestamp = datetime.fromtimestamp(os.path.getmtime(full_path))

    # Determine the appropriate timestamp for comparison based on the pickle file name
    if pickle_file_name == "master_vars.pkl":
        comparison_timestamp = one_day_ago
    else:
        comparison_timestamp = one_week_ago

    if pickle_file_timestamp < comparison_timestamp:
        print(f'{full_path} may need to be updated.')

        new_data = data_func(*func_args)
        new_data_hash = compute_md5(pickle.dumps(new_data))

        with open(full_path, 'rb') as f:
            current_pickle_hash = compute_md5(f.read())

        if current_pickle_hash != new_data_hash:
            with open(full_path, 'wb') as f:
                pickle.dump(new_data, f)
            return True

    return False

# Check and update for raw_vars_data
if check_and_update_pickle("all_raw_vars.pkl", raw_vars):
    print("all_raw_vars.pkl was updated.")
else:
    print("No update needed for all_raw_vars.pkl.")

# Check and update for master_vars_data
if check_and_update_pickle("master_vars.pkl", master_var_gen, all_raw_vars, VAR_MAPPING):
    print("master_vars.pkl was updated.")
else: 
    print("No update needed for master_vars.pkl.")
