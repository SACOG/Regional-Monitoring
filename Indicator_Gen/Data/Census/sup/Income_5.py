
import pandas as pd
from pathlib import Path
from IPython.display import display
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent/'config'))
import helpers
sys.path.append(str(Path(__file__).parent.parent/'config'))
import post


PATH_SERVER = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
PATH_SP = Path.home()/r'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\People and Community\Pop and Demographics\Pop_6 Birth Rates'


EXPORT=True

INDICATOR='Income_5'
SAMP='ACS'
EST='ACS5'
GEO='Counties'


if __name__=='__main__':

    if GEO in ['Congressional Districts', 'State Legislative Lower Districts', 'State Legislative Upper Districts']:
        if GEO == 'Congressional Districts':
            sheet_name='CD'
        if GEO == 'State Legislative Lower Districts':
            sheet_name='SLDL'
        if GEO == 'State Legislative Upper Districts':
            sheet_name='SLDU'
    else:
        sheet_name=GEO

    file_income5 = PATH_SERVER / f'{INDICATOR} {GEO} {EST}.xlsx'
    df_income5 = pd.read_excel(file_income5, sheet_name=sheet_name)
    if 'Wealth Disparity Index' in df_income5.columns:
        df_income5 = df_income5.drop(['Percent Home Ownership', 'Wealth Disparity Index'], axis=1)

    file_cost5 = PATH_SERVER / f'Cost_5 {GEO} {EST}.xlsx'
    df_cost5=pd.read_excel(file_cost5, sheet_name=sheet_name)
    df_cost5 = df_cost5[df_cost5['Variable']=='Owner occupied'][['NAME', 'Year', 'Race/Ethnicity', 'Percent']].rename(columns={'Percent':'Percent Home Ownership'})

    df_income5 = df_income5.merge(df_cost5, on=['NAME', 'Year', 'Race/Ethnicity'], how='left')
    df_income5['Wealth Disparity Index'] = (df_income5['Median Home Value'] * df_income5['Percent Home Ownership'])
    df_income5 = helpers.clean_fips(df_income5)
    display(df_income5)

    params = {
        'project': 'Monitoring and Reporting'
        , 'indicator': INDICATOR
        , 'sample': SAMP
        , 'estimate': EST
        , 'geo': GEO
        , 'mpo': False
        , 'start_year': df_income5['Year'].max()
        , 'end_year': df_income5['Year'].min()
        , 'moe_thresh': 0.05
        , 'update': False
        , 'about': True
        , 'server': True
        , 'export_loc': Path.home()/r'Sacramento Area Council of Governments\Regional Monitoring and Reporting - Documents\Data\Vibrant and Inclusive Places\Economy\Income\Income_5 Wealth'
    }

    if GEO=='MPO':
        params['mpo']=True

    params = post.write_about_master(df_income5, params)
    print("About documentation of the output for:", params['indicator'])
    display(params['df_about'])

    if EXPORT:
        post.acs_export(df_income5, params)

