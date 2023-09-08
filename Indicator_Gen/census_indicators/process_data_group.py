import pandas as pd
import re
from typing import Optional, List

def process_data_group(df: pd.DataFrame, data_group: str) -> pd.DataFrame:
    """Process DataFrame based on the given data group."""
    # Create a copy of the DataFrame to avoid modifying the original
    df_copy = df.copy()

    def extract_race_from_text(text):
        m = re.search(r'\((.+?)\)', text)  # Changed regex to capture text between parentheses
        return m.group(1) if m else None
    
    def extract_labor_status(text):
        if 'In labor force' in text:
            return 'In labor force'
        elif 'Not in labor force' in text:
            return 'Not in labor force'
        return 'Total'

    def extract_age_gender_labor(text: str):
        parts = text.split(':!!')[2:]
        age, gender, labor = None, None, None
        for part in reversed(parts):
            if 'In labor force' in part:
                labor = 'In labor force'
            elif 'Not in labor force' in part:
                labor = 'Not in labor force'
            elif part == 'Male' or part == 'Female':
                gender = part
            else:
                age = part if not age else age  # Keep the last found age
        return age, gender, labor

    def extract_category(text: str) -> Optional[str]:
        """Extract the education level from the provided text."""
        parts = text.split("!!")
        return parts[-1] if parts else None


    
    
    if data_group.lower() == 'race':
        df_copy['Race'] = df_copy['concept'].apply(extract_race_from_text)
        
    elif data_group.lower() == 'age':
        df_copy['Age'] = df_copy['label'].apply(lambda x: x.split(':!!')[-2] if 'Male' in x or 'Female' in x else None)

    elif data_group.lower() == 'gender':
        df_copy['Gender'] = df_copy['label'].apply(lambda x: 'Male' if 'Male:' in x else ('Female' if 'Female:' in x else None))

    elif data_group.lower() == 'labor force participation rate by race':
        extracted_data = df_copy['label'].apply(extract_age_gender_labor)
        df_copy['Labor Force Status'] = extracted_data.apply(lambda x: x[2])
        df_copy['Age'] = extracted_data.apply(lambda x: x[0])
        df_copy['Gender'] = extracted_data.apply(lambda x: x[1])
        df_copy['Race'] = df_copy['concept'].apply(extract_race_from_text)

    elif data_group.lower() == 'household income by race':
        df_copy['Race'] = df_copy['concept'].apply(lambda x: extract_race_from_text(x) if pd.notnull(x) else None)
        df_copy['Income'] = df_copy['label'].apply(lambda x: re.sub('[^0-9a-zA-Z,$-]', '', x.split('!!')[-1]) if 'Estimate!!Total:!!' in x else None if pd.notnull(x) else None)

    elif data_group.lower() == 'median household income by race':
        df_copy['Race'] = df_copy['concept'].apply(lambda x: extract_race_from_text(x) if pd.notnull(x) else None)
        df_copy['Median Income'] = df_copy['label'].apply(lambda x: re.sub('[^0-9a-zA-Z,$-]', '', x.split('!!')[-1]) if 'Estimate!!Total:!!' in x else None if pd.notnull(x) else None)

    elif data_group.lower()== 'educational attainment by race':
        df_copy['Race'] = df_copy['concept'].apply(extract_race_from_text)
        df_copy['Education Level'] = df_copy['label'].apply(extract_category)

    elif data_group.lower() == 'mode of commute':
        df_copy['Race'] = df_copy['concept'].apply(extract_race_from_text)
        df_copy['Mode of Commute'] = df_copy['label'].apply(extract_category)
        
    else:
        df_copy['No Data Group'] = df_copy['Variable Name']
        print(f'{data_group} is not a valid data group. No processing was performed.')
        
    
    return df_copy
