

'''
Print functions just because I like using the terminal for work/QC and need more space between code outputs so that I don't get confused
'''
def print2(): print(); print()
def print3(): print(); print(); print()



'''
Before using Python, I coded in R for years so the next few functions just makes things a tad easier in my brain
'''

def unique(list_a):

    # A substitute for list(set(x))

    # initialize a null list
    # traverse for all elements
        # check if exists in unique_list or not

    unique_list = []
    for x in list_a:
        if x not in unique_list:
            unique_list.append(x)

    return unique_list


def setdiff(list_a, list_b):
    set_a = set(list_a)
    set_b = set(list_b)
    in_list_a_but_not_in_list_b = set_a.difference(set_b)
    return in_list_a_but_not_in_list_b


# Function to create list of values inbetween range
def sequence(r1, r2, step):
    return [item for item in range(r1, r2+1, step)]



'''
Common regular expression functions that I modify as needed to extract strings from text
'''
# Remove anything before/after specified string, using regular expression (currently set to remove everything after the first comma)
def remove_post_comma(x, exp=','):
    try: x = x.split(exp, 1)[0]
    except: pass
    return x
def remove_pre_comma(x, exp=','):
    try: x = x.split(exp, 1)[1]
    except: pass
    return x


'''
Function to pop a column to a specific position
'''
# Moves column to position after specified column
def move_column_after(df, col_to_move, after_col):

    # Get a list of all column names
    # Find the index of the column to move and the index of the column to move it after
    # Remove the column to move from its current position
    # Insert the column at the new position
    # Reorder the DataFrame columns using the updated list

    cols = list(df.columns)
    col_idx = cols.index(col_to_move)
    after_col_idx = cols.index(after_col)
    cols.pop(col_idx)
    cols.insert(after_col_idx + 1, col_to_move)

    return df[cols]




'''
FIPS codes are often used across data sources but they don't always come in the same format, especially when using different file types (.csv, .xlsx, ...)
This function standardizes the FIPS format for various FIPS codes
'''

def clean_fips(df):
        
        print('Cleaning FIPS codes to standard format...')
        
        if 'STATEFP' in df.columns:                          df['STATEFP'                         ] = df['STATEFP'                         ].astype(str).apply('{:0>2}'.format)
        if 'State FIPS' in df.columns:                       df['State FIPS'                      ] = df['State FIPS'                      ].astype(str).apply('{:0>2}'.format)
        if 'Place ID' in df.columns:                         df['Place ID'                        ] = df['Place ID'                        ].astype(str).apply('{:0>5}'.format)
        if 'COUNTYFP' in df.columns:                         df['COUNTYFP'                        ] = df['COUNTYFP'                        ].astype(str).apply('{:0>3}'.format)
        if 'County FIPS' in df.columns:                      df['County FIPS'                     ] = df['County FIPS'                     ].astype(str).apply('{:0>3}'.format)
        if 'Congressional District' in df.columns:           df['Congressional District'          ] = df['Congressional District'          ].astype(str).apply('{:0>2}'.format)
        if 'State Legislative Upper District' in df.columns: df['State Legislative Upper District'] = df['State Legislative Upper District'].astype(str).apply('{:0>3}'.format)
        if 'State Legislative Lower District' in df.columns: df['State Legislative Lower District'] = df['State Legislative Lower District'].astype(str).apply('{:0>3}'.format)

        return df



