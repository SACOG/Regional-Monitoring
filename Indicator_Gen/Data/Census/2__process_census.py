

'''

This script is the second step in the pipeline to update indicators organized from data at the Census Bureau
The data cleaning/processing approach taken in this script is unique to SACOG's data needs

Request parameters need to be updated using census.xlsx in the config folder
Every data release, the .py files in the config/step0 folder need to be reran


RERUN=True/False -> if True, recycles the last API request
EXPORT=True/False -> if True, exports requested data to desired file path (PATH_SERVER or check census.yaml)

*May need to modify area_codes.xlsx file as needed when setting the following parameters
MPO=True/False -> if True, rolls up county level data to their respective MPOs (for indicators derived from ACS, DP, and SUBJECT)
UNINCORPORATED=True/False -> if True, rolls up Census Designated Place level data to incorporated vs unincorporated jurisdictions


*The following constants are SACOG specific parameters
ABOUT=True
UPDATE=False
SERVER=True


'''


RERUN=False
EXPORT=True

MPO=False
UNINCORPORATED=False

ABOUT=True
UPDATE=False
SERVER=True



# Workspace -----------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
from pathlib import Path
from IPython.display import display
import warnings; warnings.filterwarnings("ignore")
import sys

PATH_GIT = Path(__file__).parent.parent.parent
PATH_CONFIG0 = PATH_GIT / 'config'
PATH_CONFIG  = PATH_GIT / 'Data' / 'Census' / 'config'

FILE_API = PATH_CONFIG / 'api_key.txt'
FILE_AREA = PATH_CONFIG0 / 'area_codes.xlsx'
FILE_CPI = PATH_CONFIG0 / 'CPI_IAF.xlsx'
FILE_INPUTS = PATH_CONFIG / 'census.xlsx'

sys.path.append(str(PATH_CONFIG0))
import help; help.print3()

sys.path.append(str(PATH_CONFIG))
import pre
import get
import post


# Network file paths for importing/exporting
PATH_ORIG = Path(r'I:\Projects\Josh\Regional Monitoring\Task 9. Collect new data\Census')
PATH_SERVER = Path(r'\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data')




## Main ----------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    # Rerun prep work to read in census data collected in step 1
    with open(PATH_CONFIG / 'api_key.txt', 'r') as file:
        api_key = file.read()

    yaml_census = pre.load_yaml()
    params = pre.api_request_params(yaml_census, RERUN)

    if params['geo']=='Counties': params['mpo']=MPO
    else: params['mpo']=False
    if params['geo']=='Places': params['unincorporated']=UNINCORPORATED
    else: params['unincorporated']=False
    params['about']=ABOUT
    params['update']=UPDATE
    params['export']=EXPORT
    params['server']=SERVER

    # Import variable mappings
    df_vars = get.read_vars_file(params)

    # Import requested data
    file_in = PATH_ORIG / pre.set_download_name(params)
    df_census = pd.read_csv(file_in)
    display(df_census.head())
    help.print2()




    ## ACS, DP, SUBJECT, DEC ----------

    # Processing Steps:

    # Replace weird missing values with np.nan
    # Reshape data from wide to long
    # Convert data types to numeric as needed
    # Reorganize margin of error fields
    # Manually check column names and clean as needed
    # Merge cleam label field, variable mapping, race/ethnicity, and sorting field
    # Adjust dollars for inflation, if needed
    # Aggregate estimates across variables and geographies as needed

    if params['sample'] in ['ACS', 'DP', 'SUBJECT', 'DEC']:

        df_census = post.acs_main(df_census, params, df_vars)


        if ABOUT:
            params = post.write_about_master(df_census, params)
            print("About documentation of the output for:", params['indicator'])
            display(params['df_about'])

            
        if EXPORT:
            post.acs_export(df_census, params)
    


    ## PUMS, FOODSEC ----------

    # Processing steps:

    # Clean missing values, standardize how the categories are assigned by number, standardize state FIPS code
    # Convert weighted column to integer, convert value fields to string to use as merge field
    # Reshape data dictionary of values/descriptions and reorganize columns
    # Merge meaningful value descriptions onto imported data
    # Only keep description mappings, remove the original PUMS values
    # Creates grouping variables for certain indicators
    # Adjusts income variables by inflation for the latest year
    # Roll up using suggested weight field
    # Roll up to PUMA, counties, MSA, and MPO

    if params['sample'] in ['PUMS', 'FOODSEC']:

        if params['sample'] == 'PUMS':
            if 'H' in df_vars['Table Type'].unique():
                table_type = 'H'
                weight = 'WGTP'
            else:
                table_type = 'P'
                weight = 'PWGTP'

        if params['sample'] == 'PUMS':
            df_puma, df_counties, df_msa, df_mpo = post.pums_main(df_census, params, weight, df_vars)

        # if params['sample'] == 'FOODSEC':
        #     df_counties, df_mpo, groups = post.foodsec_processing_4(df_census, params, weight, groups)
        #     display(df_counties.head(3), df_mpo.head(3))

        if ABOUT:
            df_about = post.write_about_master(df_census, params)
            print("About documentation of the output for:", params['indicator'])
            display(df_about)

        if EXPORT:
            post.pums_export(df_puma, df_counties, df_msa, df_mpo, params)



    ## LEHD ----------

    if params['sample'] == 'LEHD':
        if params['geo'] == 'Counties':
            df_census, df_mpo = post.lehd_processing(df_census, params)
            display(df_census.head(3), df_mpo.head(3))
        if params['geo'] == 'MSA':
            df_census = post.lehd_processing(df_census, params)
            display(df_census.head(3))


help.print3()


