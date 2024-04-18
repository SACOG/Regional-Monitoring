def acs1_state_county(api_Key, variables, year, state, county):
    
    '''
    User defined function to import ACS 1 year estimates at the county level
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which state and counties
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = '/acs/acs1'
    g_ = '?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)
    location_ = '&for=county:' + county + '&in=state:' + state
    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs


def acs5_state_county(api_Key, variables, year, state, county):
    
    '''
    User defined function to import ACS 5 year estimates at the county level
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which state and counties
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = '/acs/acs5'
    g_ = '?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)
    location_ = '&for=county:' + county + '&in=state:' + state
    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs




def acs5_state_county_tract(api_Key, variables, year, state, county):
    
    '''
    User defined function to import ACS 5 year estimates at the tract level
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which state and counties
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = '/acs/acs5'
    g_ = '?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)
    location_ = '&for=tract:*' + '&in=state:' + state + '&in=county:' + county
    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs



def acs1_msa(api_Key, variables, year, msa):
    
    '''
    User defined function to import ACS 5 year estimates at the MSA level
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which MSAs
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = '/acs/acs1'
    g_ = '?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)
    location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)
    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs




# https://api.census.gov/data/2015/acs/acs5?get=NAME,B00001_001E&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:10420&key=YOUR_KEY_GOES_HERE
def acs5_msa(api_Key, variables, year, msa):
    
    '''
    User defined function to import ACS 5 year estimates at the MSA level
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which MSAs
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = '/acs/acs5'
    g_ = '?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)
    location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)
    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs



def acs1_pums(api_Key, variables, year, state, record_type):
    
    '''
    User defined function to import PUMS1 year estimates
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which state and record type (persons or households)
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = '/acs/acs1'
    g_ = '/pums?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)
    location_ = '&for=state:' + state + '&RT=' + record_type
    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs



# https://api.census.gov/data/2022/acs/acs5/pums?get=SEX,PWGTP,MAR&for=state:*&SCHL=24&key=YOUR_KEY_GOES_HERE
def acs5_pums(api_Key, variables, year, state, record_type):
    
    '''
    User defined function to import PUMS5 year estimates
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which state and record type (persons or households)
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = '/acs/acs5'
    g_ = '/pums?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)
    location_ = '&for=state:' + state + '&RT=' + record_type
    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs




def query_acs(api_Key, estimate, geography, variables, year, state=None, record_type=None, msa=None):
        
    '''
    User defined function to import PUMS5 year estimates
    Fixed inputs: [host_, dataset_, g_] to construct URL
    User inputs: [api_key_, variables_, year_, location_] to tell ACS that we have access with the API key and
                    to tell ACS which variables we want to import, what year, and which state and record type (persons or households)
    '''
    
    # Fixed inputs
    host_ = 'https://api.census.gov/data'
    dataset_ = f'/acs/{estimate}'
    g_ = '/pums?get='
    
    # User inputs
    api_key_ = f"&key={api_Key}"
    variables_ = variables
    year_ = '/' + str(year)


    if geography == 'PUMA':
        location_ = '&for=state:' + state + '&RT=' + record_type
    if geography == 'county':
        location_ = '&for=county:' + county + '&in=state:' + state
    if geography == 'tract':
        location_ = '&for=tract:*' + '&in=state:' + state + '&in=county:' + county
    if geography == 'MSA':
        location_ = '&for=metropolitan%20statistical%20area/micropolitan%20statistical%20area:' + str(msa)

    
    # create url query
    query = f"{host_}{year_}{dataset_}{g_}{variables_}{location_}{api_key_}"
    
    # use requests package to call out to the API
    response = requests.get(query).text
    response = response.replace('null', '"null"')
    response = ast.literal_eval(response)
    
    # convert parsed response text to pandas df
    df_acs = pd.DataFrame(response[1:], columns = response[0])
    
    # apply year tag
    df_acs['Year'] = year
    
    return df_acs