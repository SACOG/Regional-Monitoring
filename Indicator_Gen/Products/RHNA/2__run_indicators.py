


def print2(): print();print()
def print3(): print();print();print()
print3()


import time
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
PATH_PY = Path.home() / 'Documents' / 'Projects' / 'Regional-Monitoring' / 'Indicator_Gen' / 'Products' / 'RHNA' / 'python'



if __name__ == '__main__':

    indicators = [
        'POPEMP_1'
        , 'POPEMP_2'
        , 'POPEMP_3'
        , 'POPEMP_4'
        , 'POPEMP_5'
        , 'POPEMP_6'
        , 'POPEMP_7'
        , 'POPEMP_8'
        , 'POPEMP_9'
        , 'POPEMP_10'
        , 'POPEMP_11'
        , 'POPEMP_12'
        , 'POPEMP_13'
        , 'POPEMP_14'
        , 'POPEMP_15'
        , 'POPEMP_16'
        , 'POPEMP_17'
        , 'POPEMP_18'
        , 'POPEMP_19'
        , 'POPEMP_20'
        , 'POPEMP_21'
        , 'POPEMP_22'
        , 'POPEMP_23'
        , 'POPEMP_24'
        , 'POPEMP_25'
        , 'HSG_1'
        , 'HSG_2'
        , 'HSG_3'
        , 'HSG_4'
        , 'HSG_5'
        , 'HSG_6'
        , 'HSG_7'
        , 'HSG_8'
        , 'HSG_9' 
        , 'HSG_10'
        , 'HSG_11'
        , 'RISK_1'
        , 'OVER_1'
        , 'OVER_2'
        , 'OVER_3'
        , 'OVER_4'
        , 'OVER_5'
        , 'OVER_6'
        , 'OVER_7'
        , 'OVER_8'
        , 'OVER_9'
        , 'FARM_1'
        , 'FARM_2'
        , 'LGFEM_1'
        , 'LGFEM_2'
        , 'LGFEM_3'
        , 'LGFEM_4'
        , 'LGFEM_5'
        , 'SEN_1'
        , 'SEN_2'
        , 'SEN_3'
        , 'SEN_4'
        , 'DISAB_1'
        , 'DISAB_2'
        , 'DISAB_3'
        , 'DISAB_4'
        , 'DISAB_5'
        , 'HOMELS_1'
        , 'HOMELS_2'
        , 'HOMELS_3'
        , 'HOMELS_4'
        , 'ELI_1'
        , 'ELI_2'
        , 'ELI_3'
        , 'ELI_4'
        , 'AFFH_1'
        , 'AFFH_2'
        , 'AFFH_3'
        # , 'HHPROJ_1'
    ]

    indicators = ['AFFH_2']

    start_time = time.time()

    list_indicators = []
    for indicator in indicators:

        print2()
        print(indicator)
        path_run = PATH_PY / f'{indicator}.py'
        with path_run.open("r") as f: exec(f.read())
        list_indicators.append(indicator)


    print2()
    print('Finished!! Now go outside.')
    print(f'Process complete.  It took --- {round((time.time() - start_time)/60, 1)} minutes ---')
    print2()
    # takes 45 min to process all indicators



    # Check indicators
    print2()
    print('Indicators processed: '); print()
    print(list_indicators)
    print3()


