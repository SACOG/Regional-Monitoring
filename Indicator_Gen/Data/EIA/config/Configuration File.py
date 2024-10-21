
indicator_name = input("Indicator Name: ")

print('')
print('')

print('Importing API routes to help with preparing API request...')
print('(it takes a few minutes)')

df_api = pd.read_excel(os.path.join(path_config, 'Routes.xlsx'))
display(df_api.head())

print('')
print('')


## Subsets ---

df_sub = df_api.copy()

df_sub = df_sub[df_sub['route2'].isna()]
df_sub = df_sub[['category', 'route1', 'category_name', 'route1_name']].drop_duplicates()

categories_no_route2 = list(df_sub['category_name'].unique())
route1_no_route2     = list(df_sub['route1_name'  ].unique())

categories_no_route2_api = list(df_sub['category'].unique())
route1_no_route2_api     = list(df_sub['route1'  ].unique())


df_sub = df_api.copy()

df_sub = df_sub[df_sub['facetOption'].isna()]
df_sub = df_sub[['category', 'route1', 'route2','category_name', 'route1_name', 'route2_name']].drop_duplicates()

categories_no_facets = list(df_sub['category_name'].unique())
route1_no_facets     = list(df_sub['route1_name'  ].unique())

categories_no_facets_api = list(df_sub['category'].unique())
route1_no_facets_api     = list(df_sub['route1'  ].unique())


df_sub = df_api.copy()

df_sub = df_sub[df_sub['data_type'].isna()]
df_sub = df_sub[['category', 'route1', 'route2','category_name', 'route1_name', 'route2_name']].drop_duplicates()

categories_no_data = list(df_sub['category_name'].unique())
route1_no_data     = list(df_sub['route1_name'  ].unique())
route2_no_data     = list(df_sub['route2_name'  ].unique())

categories_no_data_api = list(df_sub['category'].unique())
route1_no_data_api     = list(df_sub['route1'  ].unique())
route2_no_data_api     = list(df_sub['route2'  ].unique())



## Inputs ---


## Category
categories = list(df_api['category_name'].unique())
print("Categories: ");print(categories)

while True:
    try:
        print('')
        cat = input("Enter your choice: ")
        if cat in categories:
            print('')
            break
        else:
            print('')
            print("Invalid choice. Please choose from options outlined here: ");print(categories)
    except ValueError:
        print('')
        print("Invalid choice. Please choose from options outlined here: ")



## Route 1
df_api = df_api[df_api['category_name'] == cat]
routes1 = list(df_api['route1_name'].unique())

print('')
print("Routes 1: ");print(routes1)

while True:
    try:
        print('')
        route1 = input("Enter your choice: ")
        if route1 in routes1:
            print('')
            break
        else:
            print('')
            print("Invalid choice. Please choose from options outlined here: ");print(routes1)
    except ValueError:
        print('')
        print("Invalid choice. Please choose from options outlined here: ")



## Route 2
df_api = df_api[df_api['route1_name'] == route1]

if (cat in categories_no_route2) & (route1 in route1_no_route2):
    pass
else:
    routes2 = list(df_api['route2_name'].unique())
    print('')
    print("Routes 2: ");print(routes2)
    
    while True:
        try:
            print('')
            route2 = input("Enter your choice: ")
            if route2 in routes2:
                print('')
                break
            else:
                print('')
                print("Invalid choice. Please choose from options outlined here: ");print(routes2)
        except ValueError:
            print('')
            print("Invalid choice. Please choose from options outlined here: ")

if (cat in categories_no_route2) & (route1 in route1_no_route2):
    pass
else:
    df_api = df_api[df_api['route2_name'] == route2]

## Facet Options

if (cat in categories_no_facets) & (route1 in route1_no_facets):
    pass
else:
    facetOptions = list(df_api['facetOption'].unique())
    
    print('')
    print("Facet Options: ");print(facetOptions)
    
    while True:
        try:
            print('')
            facetOption = input("Enter your choice: ")
            if facetOption in facetOptions:
                print('')
                break
            else:
                print('')
                print("Invalid choice. Please choose from options outlined here: ");print(facetOptions)
        except ValueError:
            print('')
            print("Invalid choice. Please choose from options outlined here: ")




## Facets
if (cat in categories_no_facets) & (route1 in route1_no_facets):
    pass
else:
    df_api = df_api[df_api['facetOption'] == facetOption]
    facets = list(df_api['facet_name'].unique())
    
    print('')
    print("Facets: ");print(facets)
    
    while True:
        try:
            print('')
            facet = input("Enter your choice: ")
            if facet in facets:
                print('')
                break
            else:
                print('')
                print("Invalid choice. Please choose from options outlined here: ");print(facets)
        except ValueError:
            print('')
            print("Invalid choice. Please choose from options outlined here: ")


if (cat in categories_no_facets) & (route1 in route1_no_facets):
    pass
else:
    df_api = df_api[df_api['facet_name'] == facet]


## Data Types

if (cat in categories_no_data) & (route1 in route1_no_data):
    pass          
else:
    datatypes = list(df_api['data_type'].unique())
        
    print('')
    print("Data Type Options: ");print(datatypes)
    
    while True:
        try:
            print('')
            datatype = input("Enter your choice: ")
            if datatype in datatypes:
                print('')
                break
            else:
                print('')
                print("Invalid choice. Please choose from options outlined here: ");print(datatypes)
        except ValueError:
            print('')
            print("Invalid choice. Please choose from options outlined here: ")

if (cat in categories_no_data) & (route1 in route1_no_data):
    pass
else:
    df_api = df_api[df_api['data_type'] == datatype]




## Frequency
freqs = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Annual']
print('')
print("Frequency Options: ");print(freqs)

while True:
    try:
        print('')
        freq = input("Enter your choice: ")
        if freq in freqs:
            print('')
            break
        else:
            print('')
            print("Invalid choice. Please choose from options outlined here: ");print(freqs)
    except ValueError:
        print('')
        print("Invalid choice. Please choose from options outlined here: ")



print('')
print('')
print('Your request: ')
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
display(df_api)