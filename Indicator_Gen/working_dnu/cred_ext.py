import os

## API KEY EXTRACTION

def extract_api_key(resource_dir = None, resource_file = None):
    
    """
    This function will extract the API key from a text file in the 'resource' folder if present. 
    """
    resource_file = f"{resource_file}.txt"
    file = os.path.join(resource_dir, resource_file)
    with open(file, 'r') as f:
        for line in f:
            if 'ACS:' in line:
                return line.split('ACS:')[1].strip()
    return 'WARNING: API KEY NOT FOUND'

### PW extraction

def extract_agol_password(resource_dir = None, resource_file = None):
    
    """
    This function will extract the AGOL password from a text file in the 'resource' folder if present. 
    """
    
    resource_file = f"{resource_file}.txt"
    file = os.path.join(resource_dir, resource_file)
    with open(file, 'r') as f:
        for line in f:
            if 'AGOL:' in line:
                return line.split('AGOL:')[1].strip()
    return None
