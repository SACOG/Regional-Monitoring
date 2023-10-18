import pandas as pd
import re
from typing import Optional, List
from .helpers import *
from .mapping import *

def process_data_group(data_input, data_group: str, *column_names) -> pd.DataFrame:
    df_copy = input_processing(data_input)
    column_names = list(column_names)

    ### RACE DATA GROUP ###

    if data_group.lower() == 'race':
        if not column_names:
            column_names = ['label']

        df_copy = (df_copy
                   .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
                   .pipe(lambda x: x[x['Race'].str.lower() != 'total'])
                   .pipe(map_race_group, 'Race'))

    ### AGE DATA GROUP ###

    elif data_group.lower() == 'age':
        if not column_names:
            column_names = ['label']
        
        df_copy = (df_copy
                   .assign(Age=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
                   .pipe(map_age_group))

    ### GENDER DATA GROUP ###

    elif data_group.lower() == 'gender':
        if not column_names:
            column_names = ['label']
        
        df_copy = df_copy.assign(Gender=lambda x: x[column_names[0]].apply(lambda y: 'Male' if 'Male:' in y else ('Female' if 'Female:' in y else None)))

    ### EMPLOYMENT DATA GROUP ###

    elif data_group.lower() == 'employment':
        if not column_names:
            column_names = ['concept', 'label']
        elif len(column_names) == 1:
            if 'label' in column_names:
                column_names.append('concept')
            else:
                column_names.append('label')
        elif 'label' in column_names and column_names[0] == 'label':
            column_names = ['concept', 'label']

        df_copy = df_copy.assign(
            **{"Employment Status": df_copy[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None)}
        ).pipe(map_race_group, column_name=column_names[0]) \
        .pipe(map_age_group_labor, column_name=column_names[1])





    ### HOUSEHOLD INCOME DATA GROUPS ###

    elif data_group.lower() == 'household income':
        if not column_names:
            column_names = ['concept', 'label']
        elif len(column_names) == 1:
            if 'label' in column_names:
                column_names.append('concept')
            else:
                column_names.append('label')
        elif 'label' in column_names and column_names[0] == 'label':
            column_names = ['concept', 'label']
    
        df_copy = (df_copy
               .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
               .assign(Income=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
               .pipe(lambda x: x[x['Race'].str.lower() != 'total'])
               .pipe(map_race_group, 'Race')
               .pipe(map_income_group, 'Income'))



    elif data_group.lower() == 'median income':
        if not column_names:
            column_names = ['concept']

        df_copy = df_copy.pipe(map_race_group, column_name=column_names[0])

    
    ### EDUCATION DATA GROUP ###

    elif data_group.lower() == 'education':
        if not column_names:
            column_names = ['concept', 'label']
        elif len(column_names) == 1:
            if 'label' in column_names:
                column_names.append('concept')
            else:
                column_names.append('label')
        elif 'label' in column_names and column_names[0] == 'label':
            column_names = ['concept', 'label']

        df_copy = (df_copy
                   .pipe(map_race_group, column_name=column_names[0])
                   .pipe(map_education_level, column_name=column_names[1]))

    
    ### POVERTY DATA GROUP ###

    elif data_group.lower() == 'commute':
        if not column_names:
            column_names = ['label']

        df_copy = (df_copy
                   .pipe(map_commute_group, column_name=column_names[0])
                   .pipe(map_peer_msa, 'MSA')
                   .query("`Commute Group` != 'Total'"))

    ### POVERTY DATA GROUP ###

    elif data_group.lower() == 'poverty':
        if not column_names:
            column_names = ['concept', 'label']
        elif len(column_names) == 1:
            if 'label' in column_names:
                column_names.append('concept')
            else:
                column_names.append('label')
        elif 'label' in column_names and column_names[0] == 'label':
            column_names = ['concept', 'label']
        df_copy = (df_copy
            .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
            .assign(Age=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
            .assign(Gender=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -2) if pd.notnull(y) else None))
            .assign(Poverty=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -3) if pd.notnull(y) else None))
            .pipe(map_race_group, 'Race')
            .pipe(map_age_group, 'Age')
            .pipe(map_poverty_status, 'Poverty')
            )

    elif data_group.lower() == 'median income':
        if not column_names:
            column_names = ['concept', 'label']
        elif len(column_names) == 1:
            if 'label' in column_names:
                column_names.append('concept')
            else:
                column_names.append('label')
        elif 'label' in column_names and column_names[0] == 'label':
            column_names = ['concept', 'label']
        df_copy = (df_copy
            .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
            .pipe(map_race_group, 'Race')
            )


    elif data_group.lower() == 'broadband':

        if not column_names:
            column_names = ['concept', 'label']
        elif len(column_names) == 1:
            if 'label' in column_names:
                column_names.append('concept')
            else:
                column_names.append('label')
        elif 'label' in column_names and column_names[0] == 'label':
            column_names = ['concept', 'label']

        df_copy = (df_copy
           .assign(Race=lambda x: x[column_names[0]].apply(lambda y: extract_content_between_parentheses(y, -1) if pd.notnull(y) else None))
           .assign(Broadband=lambda x: x[column_names[1]].apply(lambda y: extract_content_between_excl(y, -1) if pd.notnull(y) else None))
           .pipe(map_race_group, 'Race')
           )


    ### OTHER DATA GROUP ###

    else:
        df_copy['No Data Group'] = df_copy['Variable Name']
        print(f'{data_group} is not a valid data group. No processing was performed.')

    return df_copy
