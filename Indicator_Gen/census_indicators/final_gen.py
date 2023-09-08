import pandas as pd
import re
from typing import Optional, List, Dict
from .mapping import map_age_group, map_income_group, map_race_group, map_age_group_lpr, map_commute_group





#FINAL GENDER DF GEN ###


def final_gender(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'MPO', 
         'label', 
         'Gender',                                                                         
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)

    return final_df

#FINAL GENDER DF GEN ###


def final_age_group(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'MPO', 
         'label', 
         'Age',                                                                       
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    final_df = map_age_group(final_df)
    
    return final_df

#FINAL RACE DF GEN ###


def final_race(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'label',
         'MPO', 
         'Race',                                                                        
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    final_df = map_race_group(final_df)
    return final_df


#FINAL INCOME DF GEN ###


def final_hhi_gen(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'label',
         'MPO', 
         'Income',
         'Race',
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    final_df = map_income_group(final_df)
    final_df = map_race_group(final_df)
    return final_df


#FINAL MEDIAN INCOME DF GEN ###


def final_medi_gen(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'label',
         'MPO', 
         'label',
         'Race',                                                                         
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    final_df = map_race_group(final_df)
    final_df.rename(columns={'Total': 'Median Income'}, inplace=True)
    return final_df


#FINAL LABOR PARTICIPATION ###


def final_labor_pr(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'label',
         'MPO', 
         'Race',
         'Age',
         'Total',
         'Labor Force Status',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    final_df = map_race_group(final_df)
    final_df = map_age_group_lpr(final_df)

    return final_df

#FINAL EDICATION LEVEL GEN ###


def final_ed_level(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'label',
         'MPO',
         'Race',
         'Education Level',
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    final_df = map_race_group(final_df)

    return final_df


#FINAL MODE OF TRANSPORT GEN ###


def final_commute_mode(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'label',
         'MPO',
         'Mode of Commute',
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    final_df = map_commute_group(final_df)

    return final_df

