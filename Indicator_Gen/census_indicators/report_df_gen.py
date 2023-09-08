import pandas as pd

### LABOR FORCE PERCENTAGE ###

def labor_force_percentage_county(df: pd.DataFrame) -> pd.DataFrame:
    # Check if required columns are present in the DataFrame
    required_columns = ['County Name', 'Race Group', 'Labor Force Status', 'Total', 'Year']
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"'{column}' column not found in the DataFrame.")
    
    # Calculate None totals for each county, race combination, and year
    none_totals = df[~df['Labor Force Status'].isin(['In labor force', 'Not in labor force'])].groupby(['County Name', 
                                                                                                         'Race Group', 
                                                                                                         'Year'])['Total'].sum().reset_index()
    none_totals.rename(columns={'Total': 'Geog Total'}, inplace=True)

    # Aggregate totals by Labor Force Status for each county and race combination
    totals = df.groupby(['County Name', 'Race Group', 'Labor Force Status', 'Year'])['Total'].sum().reset_index()

    # Merge the None totals to our main DataFrame
    result = pd.merge(totals, none_totals, on=['County Name', 'Race Group', 'Year'])

    # Filter out rows where Labor Force Status is "None"
    result = result[result['Labor Force Status'] != 'None']

    # Calculate the percentage
    result['Labor Force Percentage'] = (result['Total'] / result['Geog Total'] * 100).round(2).astype(str) + '%'

    # Rearrange columns
    result = result[['County Name', 'Race Group', 'Labor Force Status', 'Geog Total', 'Year', 'Labor Force Percentage']]
    
    return result




def agol_labor_force_percentage_county(df):
    # Pivot for 'Total' values
    pivot_total = df.pivot_table(index=['County Name', 'Race Group', 'Year', 'Geog Total'], 
                                 columns='Labor Force Status', 
                                 values='Geog Total', 
                                 aggfunc='sum').reset_index()

    # Pivot for 'Labor Force Percentage' values
    pivot_percentage = df.pivot_table(index=['County Name', 'Race Group', 'Year', 'Geog Total'], 
                                      columns='Labor Force Status', 
                                      values='Labor Force Percentage', 
                                      aggfunc='first').reset_index()

    # Merge both pivot tables
    merged_df = pd.merge(pivot_total, pivot_percentage, on=['County Name', 'Race Group', 'Year', 'Geog Total'])

    # Rename columns
    merged_df.columns = ['County Name', 'Race Group', 'Year', 'Geog Total', 
                         'In Labor Force', 'Not In Labor Force', 
                         'In Labor Force Percentage', 'Not In Labor Force Percentage']
    
    return merged_df

def labor_force_percentage_mpo(df: pd.DataFrame) -> pd.DataFrame:
    # Check if required columns are present in the DataFrame
    required_columns = ['MPO', 'Race Group', 'Labor Force Status', 'Total', 'Year']
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"'{column}' column not found in the DataFrame.")
    
    # Calculate None totals for each county, race combination, and year
    none_totals = df[~df['Labor Force Status'].isin(['In labor force', 'Not in labor force'])].groupby(['MPO', 
                                                                                                         'Race Group', 
                                                                                                         'Year'])['Total'].sum().reset_index()
    none_totals.rename(columns={'Total': 'Geog Total'}, inplace=True)

    # Aggregate totals by Labor Force Status for each county and race combination
    totals = df.groupby(['MPO', 'Race Group', 'Labor Force Status', 'Year'])['Total'].sum().reset_index()

    # Merge the None totals to our main DataFrame
    result = pd.merge(totals, none_totals, on=['MPO', 'Race Group', 'Year'])

    # Filter out rows where Labor Force Status is "None"
    result = result[result['Labor Force Status'] != 'None']

    # Calculate the percentage
    result['Labor Force Percentage'] = (result['Total'] / result['Geog Total'] * 100).round(2).astype(str) + '%'

    # Rearrange columns
    result = result[['MPO', 'Race Group', 'Labor Force Status', 'Geog Total', 'Year', 'Labor Force Percentage']]
    
    return result




def agol_labor_force_percentage_mpo(df):
    # Pivot for 'Total' values
    pivot_total = df.pivot_table(index=['MPO', 'Race Group', 'Year', 'Geog Total'], 
                                 columns='Labor Force Status', 
                                 values='Geog Total', 
                                 aggfunc='sum').reset_index()

    # Pivot for 'Labor Force Percentage' values
    pivot_percentage = df.pivot_table(index=['MPO', 'Race Group', 'Year', 'Geog Total'], 
                                      columns='Labor Force Status', 
                                      values='Labor Force Percentage', 
                                      aggfunc='first').reset_index()

    # Merge both pivot tables
    merged_df = pd.merge(pivot_total, pivot_percentage, on=['MPO', 'Race Group', 'Year', 'Geog Total'])

    # Rename columns
    merged_df.columns = ['MPO', 'Race Group', 'Year', 'Geog Total', 
                         'In Labor Force', 'Not In Labor Force', 
                         'In Labor Force Percentage', 'Not In Labor Force Percentage']
    
    return merged_df
