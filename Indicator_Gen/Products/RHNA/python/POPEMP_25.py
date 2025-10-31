


from pathlib import Path


PATH_CONFIG = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'config'

import sys
sys.path.append(str(PATH_CONFIG))
import rhna
FILE_YAML = rhna.load_yaml()



if __name__ == '__main__':

        
    indicator = 'RHNA_POPEMP_25'
    source='temp'

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
            rhna.export_rhna_temp(county, jurisdiction, indicator)


