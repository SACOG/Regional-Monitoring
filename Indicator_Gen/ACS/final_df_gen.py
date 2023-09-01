import pandas as pd

### FINAL RACE GEN ###

def final_race_gen(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'MPO', 
         'label', 
         'Race Group', #here
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    return final_df

### FINAL AGE GEN ###

def final_age_gen(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'MPO', 
         'label', 
         'Age Group', #here
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    return final_df

### FINAL AGE GEN ###

def final_gender_gen(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'MPO', 
         'label', 
         'Gender', #here
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    return final_df

### FINAL HH INCOME BY RACE GEN ###

def final_HHI_by_race_gen(df, vars_df):
    final_df = pd.merge(df, vars_df, on='Variable Name', how='left')[
        ['County Name', 
         'Variable Name',
         'MPO', 
         'label', 
         'Race Group',
	 'Income', # here
         'Total',
         'Year'
        ]
    ]
    
    final_df['Total'] = final_df['Total'].astype(int)
    return final_df
