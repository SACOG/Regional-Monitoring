
import numpy as np
import pandas as pd
from pathlib import Path
from IPython.display import display



def tidy_vmt_3(xlsx_path):

    '''
    Function to reshape the wide format of the VMT_3 pdf report analyzer output
    '''

    # Read raw sheet without assuming a clean header ---------------------------------------------------------------------

    # The sheet has:
    # row 2 = COUNTY / JURISDICTION / years
    # row 3 = metric names: Maintained Miles / Daily VMT (1000s)
    
    sheet_name = "Jurisdiction (Table 6)"
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name, header=None, engine="openpyxl")

    year_header_row = 2
    metric_header_row = 3
    data_start_row = 4

    # Build clean column names ---------------------------------------------------------------------

    years = df.iloc[year_header_row].ffill()
    metrics = df.iloc[metric_header_row]

    df_cols = pd.DataFrame(data={'years': years, 'metrics': metrics})
    df_cols['new_cols'] = df_cols['years'].astype(str) + '|' + df_cols['metrics'].fillna('0').astype(str)
    df_cols['new_cols'] = df_cols['new_cols'].str.replace('|0', '')
    new_cols = df_cols['new_cols'].tolist()


    # Keep data rows only ---------------------------------------------------------------------

    # Drop any fully empty columns that may have come through

    df_wide = df.iloc[data_start_row:].copy()
    df_wide.columns = new_cols
    df_wide = df_wide.loc[:, ~df_wide.columns.astype(str).str.startswith("drop_")]


    # Identify main jurisdiction rows vs. Other Agencies rows ---------------------------------------------------------------------

    # Mark "Other Agencies" row
    # Remove the marker row itself
    # Remove rows without a county/jurisdiction
    # Clean string columns

    other_agencies_mask = df_wide["COUNTY"].astype(str).str.strip().eq("Other Agencies")

    if not other_agencies_mask.any():
        raise ValueError("Could not find the 'Other Agencies' marker row.")

    other_agencies_marker_idx = df_wide.index[other_agencies_mask][0]
    df_wide["Agency Type"] = np.where(df_wide.index > other_agencies_marker_idx, "Other Agency", "Main Jurisdiction")

    df_wide = df_wide.loc[~other_agencies_mask].copy()
    df_wide = df_wide.dropna(subset=["COUNTY", "JURISDICTION"], how="all")
    df_wide["COUNTY"      ] = df_wide["COUNTY"      ].astype(str).str.strip()
    df_wide["JURISDICTION"] = df_wide["JURISDICTION"].astype(str).str.strip()


    # Melt from wide to long ---------------------------------------------------------------------

    # Split combined column name into Year + metric

    df_long = df_wide.melt(id_vars=["Agency Type", "COUNTY", "JURISDICTION"], var_name="Year_Metric", value_name="value")
    df_long[["Year", "Metric"]] = df_long["Year_Metric"].str.split("|", expand=True)
    df_long["Year"] = df_long["Year"].astype(int)


    # Pivot metrics back into separate columns ---------------------------------------------------------------------

    # Remove the columns index name created by pivot_table
    # Ensure desired columns exist and order them
    # Convert numeric columns
    # Drop year rows where both metrics are blank
    # Sort for readability

    df_tidy = (
        df_long
        .pivot_table(index=["Agency Type", "COUNTY", "JURISDICTION", "Year"], columns="Metric", values="value", aggfunc="first")
        .reset_index()
    )

    df_tidy.columns.name = None
    desired_cols = ["Agency Type", "COUNTY", "JURISDICTION", "Year", "Maintained Miles", "Daily VMT (1000s)"]
    df_tidy = df_tidy[desired_cols]

    df_tidy["Maintained Miles"] = pd.to_numeric(df_tidy["Maintained Miles"], errors="coerce")
    df_tidy["Daily VMT (1000s)"] = pd.to_numeric(df_tidy["Daily VMT (1000s)"], errors="coerce")

    df_tidy = df_tidy.dropna(subset=["Maintained Miles", "Daily VMT (1000s)"], how="all")
    df_tidy = df_tidy.sort_values(["Agency Type", "COUNTY", "JURISDICTION", "Year"], kind="stable").reset_index(drop=True)


    # Check ---------------------------------------------------------------------

    display(df_tidy.head())
    print(df_tidy.shape)
    print(df_tidy["Agency Type"].value_counts(dropna=False))

    return df_tidy




PATH_VMT = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Next Gen of Mobility Solutions\VMT')
PATH_DOF = Path(r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\People and Community\Pop and Demographics')


SACOG_COUNTIES = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']
HEAVY_DUTY_REDUCTION_FACTOR = 0.0925821

EXPORT=False


if __name__ == '__main__':
    
    print('\n\nVMT data from HPMS:')
    file_vmt = PATH_VMT/"VMT_3 HPMS.xlsx"
    df_vmt3 = tidy_vmt_3(file_vmt)
    df_vmt3 = df_vmt3.groupby(['Year'], as_index=False).agg(Daily_VMT_1ks=('Daily VMT (1000s)', 'sum'))
    display(df_vmt3.head())

    print('\n\nPopulation data from DOF:')
    file_dof = PATH_DOF/'DOF_E5_and_E8_Jurisdictions.xlsx'
    df_dof = pd.read_excel(file_dof)
    df_dof = df_dof[df_dof['County'].isin(SACOG_COUNTIES)].groupby(['MPO', 'Year'], as_index=False).agg(Population=('Household Population', 'sum'))
    display(df_dof.head())

    print('\n\nHPMS Average Daily VMT: ')
    df_avg = df_vmt3.merge(df_dof, on='Year')
    df_avg['avg_daily_vmt'] = ((df_avg['Daily_VMT_1ks']*1000)/df_avg['Population']) - ((df_avg['Daily_VMT_1ks']*1000)/df_avg['Population'])*HEAVY_DUTY_REDUCTION_FACTOR
    df_avg = df_avg[['MPO', 'Year', 'Daily_VMT_1ks', 'Population', 'avg_daily_vmt']]
    df_avg = df_avg.rename(columns={'Daily_VMT_1ks':'Daily VMT (1000s)', 'avg_daily_vmt':'HPMS Avg Daily VMT'})
    display(df_avg.head())

    if EXPORT:
        print(f'\n\nExporting to {PATH_VMT}...')
        df_avg.to_excel(PATH_VMT/'HPMS Avg Daily VMT_DOF HOUSEHOLD POP.xlsx', index=False)
        print('\nMission accomplished\n\n')