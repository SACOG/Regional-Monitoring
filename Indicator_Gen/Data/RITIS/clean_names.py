import os
import re
import zipfile
import tempfile
# Script to label and clean zip filenames from mdd
def get_zip_label(zip_path):
    """
    Read Contents.txt from zip and return appropriate label (TAP, T, or P).
    Returns None if no label should be applied.
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check if Contents.txt exists in the zip
            if 'Contents.txt' not in zip_ref.namelist():
                print(f"  Warning: Contents.txt not found in {os.path.basename(zip_path)}")
                return None
            
            # Read Contents.txt
            with zip_ref.open('Contents.txt') as f:
                contents_text = f.read().decode('utf-8', errors='ignore')
            
            # Check for Trucks and Passengers (case-insensitive)
            has_trucks = "trucks" in contents_text.lower()
            has_passengers = "passenger" in contents_text.lower()
            has_both= "trucks and passenger" in contents_text.lower()
            
            # Determine label
            if has_both:
                return "TAP"
            elif has_trucks:
                return "T"
            elif has_passengers:
                return "P"
            else:
                print(f"  Warning: Neither 'Trucks' nor 'Passengers' found in Contents.txt")
                return None
    
    except Exception as e:
        print(f"  Error reading zip file: {e}")
        return None

def is_correctly_labeled(filename, label):
    """
    Check if the zip file already has the correct label.
    Examples: 2024_06T.zip, 2024_06P.zip, 2024_06TAP.zip
    """
    if not filename.lower().endswith('.zip'):
        return False
    
    name_without_ext = filename[:-4]  # Remove .zip
    
    # Check if it ends with the correct label (case-insensitive check for flexibility)
    if label and name_without_ext.upper().endswith(label.upper()):
        return True
    
    return False

# Define the folder path
folder_path = r"I:\Projects\Josh\Regional Monitoring\Congestion\monthly csv"

# Loop through all files in the folder
for filename in os.listdir(folder_path):
    # Only process files (not directories)
    if os.path.isfile(os.path.join(folder_path, filename)):
        old_path = os.path.join(folder_path, filename)
        new_filename = filename
        
        # Handle ZIP files - add label based on Contents.txt
        if filename.lower().endswith('.zip'):
            # Get what the label should be based on Contents.txt
            label = get_zip_label(old_path)
            
            if not label:
                # If no label could be determined, just clean up the filename
                name_without_ext = filename[:-4]
                name_without_ext = re.sub(r'\(\d+\)', '', name_without_ext)
                name_without_ext = name_without_ext.replace(' ', '')
                new_filename = f"{name_without_ext}.zip"
            else:
                # Check if already correctly labeled
                if is_correctly_labeled(filename, label):
                    # Check if it also needs cleaning (removing spaces or (1), (2), etc.)
                    clean_check = filename[:-4]  # Remove .zip
                    clean_check = re.sub(r'\(\d+\)', '', clean_check)
                    clean_check = clean_check.replace(' ', '')
                    
                    if f"{clean_check}.zip" == filename:
                        print(f"Already correctly labeled: '{filename}'")
                        continue
                
                # Build the new filename
                name_without_ext = filename[:-4]  # Remove .zip
                
                # Remove (1), (2), (3), etc. and spaces
                name_without_ext = re.sub(r'\(\d+\)', '', name_without_ext)
                name_without_ext = name_without_ext.replace(' ', '')
                
                # Remove existing label if present (to avoid duplicates like 2024_06TT.zip)
                for existing_label in ['TAP', 'T', 'P']:
                    if name_without_ext.upper().endswith(existing_label):
                        name_without_ext = name_without_ext[:-len(existing_label)]
                        break
                
                # Add the correct label
                new_filename = f"{name_without_ext}{label}.zip"
        
        else:
            # For non-zip files, just remove (1), (2), (3), etc. and spaces
            new_filename = re.sub(r'\(\d+\)', '', new_filename)
            new_filename = new_filename.replace(' ', '')
        print(f"Original filename: '{filename}'")
        print(f"  New filename: '{new_filename}'")
        
        # Only rename if the filename has changed
        if new_filename != filename:
            print("TRIPPED")
            new_path = os.path.join(folder_path, new_filename)
            
            # Check if the new filename already exists
            if os.path.exists(new_path):
                print(f"Warning: Cannot rename '{filename}' to '{new_filename}' - file already exists")
            else:
                os.rename(old_path, new_path)
                print(f"Renamed: '{filename}' -> '{new_filename}'")
        else:
            print(f"Skipped (no changes needed): '{filename}'")

print("\nRenaming complete!")