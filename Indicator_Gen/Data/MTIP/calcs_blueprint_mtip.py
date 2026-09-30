

# TODO: Before running, check functions to make sure all years are updated as needed


# blank = nonexempt = expansion project



# Setup ---------------------------------------------------------------------------------------------------------------------------------------------------

import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from IPython.display import display

pd.set_option('display.float_format', lambda x: f'{x:.3f}')
warnings.filterwarnings("ignore")



def clean_project_list(df, df_cw):

    df = df[~df['Plan Status'].str.contains('Amendment')]
    df = df.merge(df_cw.dropna(), on=['AB350 Category'], how='left')
    df['Plotting Category'   ] = df['AB350 Category'].map(AB350_CAT_MAP   )
    df['Plotting Subcategory'] = df['AB350 Category'].map(AB350_CAT_SUBMAP)
    df['Cost'] = df['Cost'].astype('int64')

    return df


def amendment_summary(df_proj, df_amend):
    df_comp = (
        df_proj[['SACTrak ID', 'Cost']].rename(columns={'Cost': 'Cost_adopted'}) \
            .merge(
                df_amend[['SACTrak ID', 'Cost']].rename(columns={'Cost': 'Cost_amendment'})
                , on='SACTrak ID', how='outer') \
            .fillna(0)
    )

    df_comp['diff_amend_adopt'] = df_comp['Cost_amendment'] - df_comp['Cost_adopted']
    df_comp = df_comp.sort_values('diff_amend_adopt', ascending=False)

    df_proj  = df_proj .merge(df_comp, on='SACTrak ID', how='left')
    df_amend = df_amend.merge(df_comp, on='SACTrak ID', how='left')
    df_comp = pd.concat([df_proj, df_amend])
    df_comp = df_comp.dropna(subset=['Category'])
    df_comp = df_comp.sort_values('diff_amend_adopt', ascending=False).drop_duplicates(subset=['SACTrak ID'])

    conditions = [
        (df_comp['diff_amend_adopt']>0) & (df_comp['Cost_adopted']>0) & (df_comp['Cost_amendment']>0),
        (df_comp['diff_amend_adopt']>0) & (df_comp['Cost_adopted']==0) & (df_comp['Cost_amendment']>0),
        (df_comp['diff_amend_adopt']<0) & (df_comp['Cost_adopted']>0) & (df_comp['Cost_amendment']>0),
        (df_comp['diff_amend_adopt']<0) & (df_comp['Cost_adopted']>0) & (df_comp['Cost_amendment']==0),
    ]
    choices = ['Increase in cost', 'Increase in cost (new project)', 'Decrease in cost', 'Decrease in cost (project removed)']
    df_comp['Source'] = np.select(conditions, choices, default='No change')
    # df_comp.to_excel(Path(PATH_SP)/'Adoption vs Amendment Comparison V2.xlsx', index=False)

    comp_id  = set(df_comp ['SACTrak ID'].unique())
    proj_id  = set(df_proj ['SACTrak ID'].unique())
    amend_id = set(df_amend['SACTrak ID'].unique())

    return df_comp


def organize_indicators(indicator, df_proj, df_amend=None):

    if indicator == 'MTIP_1':
        df_mtip1a = (
            df_proj \
                .groupby(['Plotting Category', 'Plotting Subcategory'], as_index=False) \
                .agg(Cost=('Cost', 'sum'))
        )

        df_mtip1b = (
            df_proj[df_proj['Plan Status']=='Programmed- See MTIP for details'] \
                .groupby(['Plotting Category', 'Plotting Subcategory'], as_index=False) \
                .agg(Cost=('Cost', 'sum'))
        )

        return df_mtip1a, df_mtip1b

    if indicator == 'MTIP_2':
        df_mtip2a = (
            df_proj \
                .groupby(['Exempt Status', 'Plotting Category'], as_index=False) \
                .agg(Cost=('Cost', 'sum'), Projects=('SACTrak ID', 'count'))
        )
        df_mtip2b = (
            df_amend \
                .groupby(['Exempt Status', 'Plotting Category'], as_index=False) \
                .agg(Cost=('Cost', 'sum'), Projects=('SACTrak ID', 'count'))
        )

        df_mtip2a['Source']='2025 Blueprint (MTP/SCS)'
        df_mtip2b['Source']='Most Current Amendment'

        df_mtip2a = df_mtip2a.set_index('Source').reset_index()
        df_mtip2b = df_mtip2b.set_index('Source').reset_index()

        return df_mtip2a, df_mtip2b

    if indicator == 'MTIP_3':
        df_mtip3a = (
            df_proj \
                .groupby(['Plotting Category', 'Plotting Subcategory'], as_index=False) \
                .agg(Cost=('Cost', 'sum'))
        )

        return df_mtip3a


def export_inticators(indicator, df1, df2=None):
    if indicator in ['MTIP_2']:
        title='Adoption vs Amendments'
        sheet_name1='Adoption'
        sheet_name2='Amendments'
        with pd.ExcelWriter(Path(PATH_SP)/indicator/f'{indicator} {title}.xlsx', mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df1.to_excel(writer, index=False, sheet_name=sheet_name1)
            df2.to_excel(writer, index=False, sheet_name=sheet_name2)
    if indicator in ['MTIP_1', 'MTIP_3']:
        if indicator == 'MTIP_1':
            title='All Projects 2025 Blueprint'
            sheet_name1='All Projects'
        if indicator == 'MTIP_3':
            title='Completed Projects 2023-2025'
            sheet_name='Completed'
        with pd.ExcelWriter(Path(PATH_SP)/indicator/f'{indicator} {title}.xlsx', mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df1.to_excel(writer, index=False, sheet_name=sheet_name)




# Main ---------------------------------------------------------------------------------------------------------------------------------------------------




AB350_CAT_MAP = {
    'Highway Expansion and Major Capital': 'Highways'
    , 'Highway Operations, Maintenance, and Minor Capital': 'Highways'
    , 'Bicycle and Pedestrian Facilities and Trails': 'Other'
    , 'Transportatoin Technnology, Efficienty Improvements, and Traveller Information': 'Other'
    , 'New and Expanded Bridges': 'Bridges'
    , 'Bridge preservation, repair, replacement, and minor capital': 'Bridges'
    , 'Streets and Roads Expansion and Major Capital': 'Streets/Roads'
    , 'Streets and Roads Operations, Maintenance, and Minor Capital': 'Streets/Roads'
    , 'Transit Expansion and Major Capital': 'Transit'
    , 'Transit Operations, Maintenance, and Minor Capital': 'Transit'
    , 'Other Plans, Studies, and Programs': 'Other'
}

AB350_CAT_SUBMAP = {
    'Highway Expansion and Major Capital': 'Expansion'
    , 'Highway Operations, Maintenance, and Minor Capital': 'Operations/Maintenance'
    , 'Bicycle and Pedestrian Facilities and Trails': 'Bike/Ped'
    , 'Transportatoin Technnology, Efficienty Improvements, and Traveller Information': 'Technnology & Traveler Info'
    , 'New and Expanded Bridges': 'Expansion'
    , 'Bridge preservation, repair, replacement, and minor capital': 'Operations/Maintenance'
    , 'Streets and Roads Expansion and Major Capital': 'Expansion'
    , 'Streets and Roads Operations, Maintenance, and Minor Capital': 'Operations/Maintenance'
    , 'Transit Expansion and Major Capital': 'Expansion'
    , 'Transit Operations, Maintenance, and Minor Capital': 'Operations/Maintenance'
    , 'Other Plans, Studies, and Programs': 'Plans, Studies, & Programs'
}


EXEMPT_MAP = {
    'Blank': 'Nonexempt'
    , 'Not Blank': 'Exempt'
}

PATH_SP = r'C:\Users\jfontes\Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Modernize how Pay Infrastructure'
FILE_CW = Path(PATH_SP)/'MTIP_Blueprint AB350 Project Categories.xlsx'

FILE_PROJ_LIST = r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\MTIP\Copy of AB350 Project Lists_LumpSums.xlsx'

EXPORT=False


if __name__ == '__main__':

    df_cw    = pd.read_excel(FILE_PROJ_LIST, sheet_name='AB 350 Types and Definitions', usecols='A:C')
    df_proj  = pd.read_excel(FILE_PROJ_LIST, sheet_name='Current Project List'        , skiprows=1)
    df_amend = pd.read_excel(FILE_PROJ_LIST, sheet_name='Amendment 1'                 , skiprows=1)
    df_done  = pd.read_excel(FILE_PROJ_LIST, sheet_name='Completed Projects'                      )

    display(df_cw   )
    display(df_proj )
    display(df_amend)
    display(df_done )

    df_proj  = df_proj[df_proj['Lump Sum and Programmatic Investments not tracked by MPO']!='X']
    df_amend = df_amend[df_amend['Lump Sums']!='X']


    df_cw = df_cw.rename(columns={'AB350 / Blueprint Categories': 'AB350 Category'})
    df_cw['Exempt Status'] = df_cw['Exempt Category'].map(EXEMPT_MAP)
    df_cw = df_cw[['AB350 Category', 'Exempt Status']].drop_duplicates()

    df_proj  = clean_project_list(df_proj , df_cw)
    df_amend = clean_project_list(df_amend, df_cw)
    df_done  = clean_project_list(df_done , df_cw)

    df_comp = amendment_summary(df_proj, df_amend)

    df_mtip1a, df_mtip1b = organize_indicators('MTIP_1', df_proj)
    df_mtip2a, df_mtip2b = organize_indicators('MTIP_2', df_proj, df_amend)
    df_mtip3a = organize_indicators('MTIP_3', df_done, df_amend)


    if EXPORT:
        export_inticators('MTIP_1', df_mtip1a, df_mtip1b)
        export_inticators('MTIP_2', df_mtip2a, df_mtip2b)
        export_inticators('MTIP_3', df_mtip3a)

    print('\n'*2)

