cat         = df_api['category'   ].values[0]
route1      = df_api['route1'     ].values[0]
route2      = df_api['route2'     ].values[0]
facetOption = df_api['facetOption'].values[0]
facet       = df_api['facet'      ].values[0]
freq        = freq.lower()


print('')
print('')
print('API request: ')
print('')
print(cat)
print(route1)
try:
    print(route2)
except:
    pass
try:
    print(facetOption)
except:
    pass
try:
    print(facet)
except:
    pass
try:
    print(datatype)
except:
    pass
print(freq)
print('')


if (cat in categories_no_data_api) & (route1 in route1_no_data_api):
    if (cat in categories_no_facets_api) & (route1 in route1_no_facets_api):
        params = {
            'api_key': api_key,
            "data[0]": 'value',
            "frequency": freq,
            'start': 2000
        }
    else:
        params = {
            'api_key': api_key,
            "data[0]": 'value',
            f'facets[{facetOption}][]': facet,
            "frequency": freq,
            'start': 2000
        }
else:
    if (cat in categories_no_facets_api) & (route1 in route1_no_facets_api):
        params = {
        'api_key': api_key,
        f"data[]": datatype,
        "frequency": freq,
        'start': 2000
    }
    else:
        params = {
        'api_key': api_key,
        f"data[]": datatype,
        f'facets[{facetOption}][]': facet,
        "frequency": freq,
        'start': 2000
    }

    
root_ = 'https://api.eia.gov/v2'
if (cat in categories_no_route2_api) & (route1 in route1_no_route2_api):
    route_ = f'/{cat}/{route1}'
else:
    route_ = f'/{cat}/{route1}/{route2}'
data_ = f'/data'

url = f"{root_}{route_}{data_}"

response = requests.get(url, params=params)
response = response.json()

print('')
print('API response: ')
print('')

display(response)