import os
import pickle
import hashlib
from datetime import datetime, timedelta
from .get_raw_vars import raw_vars

def check_and_update_pickle(pickle_file_name):
    """
    Check if a pickle file needs to be updated based on the output of raw_vars() 
    and update it if necessary.

    Parameters:
    -----------
    pickle_file_name : str
        The name/path of the pickle file.

    Returns:
    --------
    bool
        True if the pickle file was updated, otherwise False.
    """
    # Function to compute MD5 hash of a file

    print(f'Checking if {pickle_file_name} needs to be updated')
    def compute_md5(file_path):
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

    # Check if pickle file exists, if not, create it with content from raw_vars()
    if not os.path.exists(pickle_file_name):
        print(f'{pickle_file_name} not detected. Creating it now.')
        with open(pickle_file_name, 'wb') as f:
            pickle.dump(raw_vars(), f)
        return True  # Since file was just created

    # Check if pickle file's last modified timestamp is more than a year old
    one_year_ago = datetime.now() - timedelta(days=365)
    pickle_file_timestamp = datetime.fromtimestamp(os.path.getmtime(pickle_file_name))

    if pickle_file_timestamp < one_year_ago:
        (f'{pickle_file_name} is more than one year old and may need to be updated.')
        # Compute hash of the pickle file
        current_pickle_hash = compute_md5(pickle_file_name)
        
        # Compute hash of the output of raw_vars()
        raw_vars_data = raw_vars()
        raw_vars_hash = hashlib.md5(pickle.dumps(raw_vars_data)).hexdigest()

        # If the hashes don't match, update the pickle file and return True
        if current_pickle_hash != raw_vars_hash:
            with open(pickle_file_name, 'wb') as f:
                pickle.dump(raw_vars_data, f)
            return True

    return False


if check_and_update_pickle("all_raw_vars.pkl"):
    print("Pickle file was updated.")
else: 
	print("No update needed.")
