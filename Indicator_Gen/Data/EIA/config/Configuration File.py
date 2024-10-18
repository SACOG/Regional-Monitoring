
print('Importing API data to help with preparing API request...')


df_api = pd.read_excel(os.path.join(path_config, 'All Routes and Facets FINAL.xlsx'))
display(df_api.head())



print('')
print('')



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



## Facet Options


df_api = df_api[df_api['route2_name'] == route2]
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
df_api = df_api[df_api['facetOption'] == facetOption]
facets = list(df_api['facet_name'].unique())

print('')
print("Facet Options: ");print(facets)

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


df_api = df_api[df_api['facet_name'] == facet]


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
            # print("You selected:", freqs)
            # print('')
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
print(route2)
print(facetOption)
print(facet)
print(freq)
print('')
display(df_api)