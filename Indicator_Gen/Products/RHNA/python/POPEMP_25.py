

indicator = 'RHNA_POPEMP_25'


source='temp'
with path_func.open("r") as f: exec(f.read())



counties = ['El Dorado', 'Placer', 'Sacramento', 'Sutter', 'Yolo', 'Yuba']

dt_juris = {
    'El Dorado': ['Placerville', 'South Lake Tahoe', 'Unincorporated'],
    'Placer': ['Auburn', 'Colfax', 'Lincoln', 'Loomis', 'Rocklin', 'Roseville', 'Unincorporated'],
    'Sacramento': ['Citrus Heights', 'Elk Grove', 'Folsom', 'Galt', 'Isleton', 'Rancho Cordova', 'Sacramento', 'Unincorporated'],
    'Sutter': ['Live Oak', 'Yuba City', 'Unincorporated'],
    'Yolo': ['Davis', 'West Sacramento', 'Winters', 'Woodland', 'Unincorporated'],
    'Yuba': ['Marysville', 'Wheatland', 'Unincorporated']
}


print()
for county in counties:
    print(county)
    for jurisdiction in dt_juris[county]:
        export_rhna_temp()



list_indicators.append(indicator)
