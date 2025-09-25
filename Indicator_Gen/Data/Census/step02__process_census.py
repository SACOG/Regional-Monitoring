






# TODO:
# write_about functions need work on specificity - being able to adjust easily what to label the geography


print(); print(); print()





rerun=True
export=True
about=True
update=False
server=False
mpo = 'Yes'
unincorporated = 'Yes'




# Workspace -----------------------------------------------------------------------------------------------------------------------------------------


import pandas as pd
from pathlib import Path
import re
from xlwt.Workbook import *
from IPython.display import display
import sys


path_git = Path(__file__).parent.parent.parent
path_code    = path_git / 'Data' / 'Census'
path_config0 = path_git / 'config'
path_config  = path_code / 'config'

sys.path.append(str(path_config0))
import functions as func
import plot as pt

sys.path.append(str(path_config))
import pre
import get
import post



# SharePoint OneDrive paths
path_sp = Path.home() / 'Sacramento Area Council of Governments' / 'Regional Monitoring and Reporting - Documents'
path_orig = path_sp / 'Process Revamp' / 'Task 9. Collect new data' / 'Census'
path_main = path_sp / 'Data'
path_prod = path_sp / 'Products'
path_about = path_sp / 'Process Revamp' / 'Task 6. Process Map'
path_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")

    




## Main ----------------------------------------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':


    # Rerun prep work to read in census data collected in step 1
    file_api = path_config / 'api_key.txt'
    with open(file_api, 'r') as file:
        api_key = file.read()

    yaml_census = pre.load_yaml(path_config)
    project, indicator, sample_type, estimate, geography, years_to_import, year_start, year_end, import_tab, margin_of_error, export_loc, folder, MOE_thresh, num_vars, percentages, weighted_by, metric = pre.api_request_params(yaml_census, rerun)

    df_inputs, file_inputs, file_area = get.read_inputs_file(import_tab)
    df_vars = get.read_vars_file(file_inputs, sample_type, indicator, years_to_import, estimate)

    file_in = path_orig / pre.set_download_name(indicator, estimate, sample_type, geography, margin_of_error, path_orig)
    df_census = pd.read_csv(file_in)
    display(df_census.head())




    # Processing
    print(); print()


    # ACS, DP, SUBJECT, DEC
    if sample_type in ['ACS', 'DP', 'SUBJECT', 'DEC']:
        if sample_type == 'SUBJECT': estimate = re.sub('SUBJECT', 'ACS', estimate)
        if sample_type == 'DP': estimate = re.sub('DP', 'ACS', estimate)

        # Replace weird missing values with np.nan
        # Reshape data from wide to long
        # Convert data types to numeric as needed
        # Manually check column names and clean as needed
        # Adjust dollars for inflation, if needed
        # Reorganize margin of error fields
        df_census = post.acs_processing_1(df_census, df_vars, geography, margin_of_error, mpo, import_tab)
        print(df_census.Year.unique()); display(df_census.head(3))


        # Merge cleam label field, variable mapping, race/ethnicity, and sorting field
        # Remove unneeded columns
        # Sort by geography, variable mapping, and race/ethnicity
        df_census = post.acs_processing_2(df_census, df_vars, estimate, indicator, geography, margin_of_error, year_end, path_main, path_config0, weighted_by, unincorporated)
        print(df_census.Year.unique()); display(df_census.head(3))


        # Final processing step for ACS data
        # Link various FIPS codes
        # Roll up population/households/SE's to the desired geography and variable groupings
        # Calculate percentages by geography, race/ethnicity, and variables
        if geography == 'Counties' and mpo == 'Yes':
            df_census, df_mpo = post.acs_processing_3(df_census, estimate, sample_type, indicator, geography, percentages, margin_of_error, MOE_thresh, num_vars, weighted_by, project, export_loc, path_server, metric, unincorporated, mpo)
        else:
            df_census = post.acs_processing_3(df_census, estimate, sample_type, indicator, geography, percentages, margin_of_error, MOE_thresh, num_vars, weighted_by, project, export_loc, path_server, metric, unincorporated, mpo)
        print(df_census.Year.unique()); display(df_census.head(3))




    # PUMS, FOODSEC
    if sample_type in ['PUMS', 'FOODSEC']:

        if sample_type == 'PUMS':
            if 'H' in df_vars['Table Type'].unique():
                table_type = 'H'
                weight = 'WGTP'
            else:
                table_type = 'P'
                weight = 'PWGTP'
        
        # Clean missing values, standardize how the categories are assigned by number, standardize state FIPS code
        # Convert weighted column to integer, convert value fields to string to use as merge field
        # Reshape data dictionary of values/descriptions and reorganize columns
        # Merge meaningful value descriptions onto imported data
        df_census, groups = post.pums_processing_1(df_census, df_vars, sample_type, weight)
        print('Groups: ' + ', '.join(groups)); display(df_census.head(3))

        # Remove rows with missing values
        # Only keep description mappings, remove the original PUMS values
        df_census = post.pums_processing_2(df_census, estimate, sample_type, groups)
        display(df_census.head(3))

        # Cleans race/ethnicity fields
        # Creates additional grouping variables for certain indicators
        # Adjusts income variables by inflation for the latest year
        df_census, groups = post.pums_processing_3(df_census, groups, indicator, path_config0)
        print('Groups: ' + ', '.join(groups)); display(df_census.head(3))

        # Roll up using suggested weight field
        # Roll up to PUMA, counties, MSA, and MPO
        if sample_type == 'PUMS':
            df_puma, df_counties, df_msa, df_mpo, groups = post.pums_processing_4(df_census, indicator, weight, margin_of_error, MOE_thresh, percentages, groups)
            display(df_puma.head(3), df_counties.head(3), df_msa.head(3), df_mpo.head(3))

        # Roll up using suggested weight field
        # Roll up to counties and MPO
        if sample_type == 'FOODSEC':
            df_counties, df_mpo, groups = post.foodsec_processing_4(df_census, weight, percentages, groups)
            display(df_counties.head(3), df_mpo.head(3))


    # LEHD
    if sample_type == 'LEHD':
        if geography == 'Counties':
            df_census, df_mpo = post.lehd_processing(df_census, geography, indicator, percentages, df_fips)
            display(df_census.head(3), df_mpo.head(3))
        if geography == 'MSA':
            df_census = post.lehd_processing(df_census, geography, indicator, percentages)
            display(df_census.head(3))





    # Final organization of tables for cleanliness
    # Renaming columns, subsetting to only desired columns, ...

    print(); print()
    print('Final Results: ')
    print()

    if geography == 'PUMA':
        df_puma, df_counties, df_msa, df_mpo = post.rename_census(df_puma             = df_puma
                                                                    , df_counties     = df_counties
                                                                    , df_msa          = df_msa
                                                                    , df_mpo          = df_mpo
                                                                    , geography       = geography
                                                                    , indicator       = indicator
                                                                    , metric          = metric
                                                                    , margin_of_error = margin_of_error
                                                                    , percentages     = percentages
                                                                    , sample_type     = sample_type
                                                                    , groups          = groups
                                                                    , table_type      = table_type)
        display(df_puma, df_counties, df_msa, df_mpo)
    elif geography == 'Counties':
        if sample_type in ['ACS', 'DP', 'SUBJECT', 'DEC']:
            if mpo == 'Yes':
                df_census, df_mpo = post.rename_census(df_census          = df_census
                                                        , df_mpo          = df_mpo
                                                        , geography       = geography
                                                        , indicator       = indicator
                                                        , metric          = metric
                                                        , margin_of_error = margin_of_error
                                                        , percentages     = percentages
                                                        , sample_type     = sample_type
                                                        , df_vars         = df_vars
                                                        , mpo             = mpo)
                display(df_census, df_mpo)
    else:
        df_census = post.rename_census(df_census          = df_census
                                        , geography       = geography
                                        , indicator       = indicator
                                        , metric          = metric
                                        , margin_of_error = margin_of_error
                                        , percentages     = percentages
                                        , sample_type     = sample_type)
        display(df_census); print(); print()







    # Write about page if needed
    if about:
        if geography == 'Counties' and mpo == 'Yes':
            df_about, df_about_mpo = post.write_about_master(df_census, indicator, sample_type, geography, estimate, mpo, MOE_thresh, path_config0, update, path_about)
        else:
            df_about = post.write_about_master(df_census, indicator, sample_type, geography, estimate, mpo, MOE_thresh, path_config0, update, path_about)
        print("About documentation of the output for:", indicator)
        display(df_about)
        
    print(); print()




    # Exporting
    if export:
        print(); print()


        if sample_type == 'SUBJECT': estimate = re.sub('ACS', 'SUBJECT', estimate)
        if sample_type == 'DP': estimate = re.sub('ACS', 'DP', estimate)

        if geography == 'PUMA':
            estimate = re.sub('ACS', 'PUMS', estimate)
            workbook_name1 = f"{indicator} PUMA {estimate}.xlsx"; print(workbook_name1)
            workbook_name2 = f"{indicator} Counties {estimate}.xlsx"; print(workbook_name2)
            workbook_name3 = f"{indicator} MSA {estimate}.xlsx"; print(workbook_name3)
            workbook_name4 = f"{indicator} MPO {estimate}.xlsx"; print(workbook_name4)
                    
        elif geography == 'Counties':
            workbook_name = f"{indicator} {geography} {estimate}.xlsx"; print(workbook_name)
            if mpo == 'Yes':
                workbook_name2 = f"{indicator} MPO {estimate}.xlsx"; print(workbook_name2)
        else:
            if sample_type == 'LEHD':
                workbook_name = f"{indicator} {geography} {sample_type}.xlsx"
            else:
                workbook_name = f"{indicator} {geography} {estimate}.xlsx"
            print(workbook_name)
        print()
        
        path_out_server = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring\Data")
        path_out_sp = Path(export_loc) / f"{indicator} {folder}"
        
        if project != 'Monitoring and Reporting':
            path_out_sp = Path(export_loc)

        if project == 'Monitoring and Reporting' and server == True:
            paths = [path_out_server, path_out_sp]
        else:
            paths = [path_out_sp]
        

        for path_ in paths:

            try: path_wb = path_ / workbook_name
            except: pass
            

            if sample_type in ['ACS', 'DP', 'SUBJECT', 'DEC', 'LEHD']:

                if geography == 'Places':
                    if about: df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Census Designated Places (Jurisdictions)'
                if geography == 'Counties' and mpo == 'Yes':
                    path_mpo = path_ / workbook_name2
                    if about: post.export_indicator(geography, df_mpo, path_mpo, about, df_about_mpo)
                    else:     post.export_indicator(geography, df_mpo, path_mpo, about)
                if about: post.export_indicator(geography, df_census, path_wb, about, df_about)
                else:     post.export_indicator(geography, df_census, path_wb, about)


            if sample_type == 'PUMS':

                path_wb = path_ / workbook_name1
                if about: post.export_indicator(geography, df_puma, path_wb, about, df_about)
                else:     post.export_indicator(geography, df_puma, path_wb, about)

                path_wb = path_ / workbook_name2
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Counties'
                    post.export_indicator(geography, df_counties, path_wb, about, df_about)
                else:
                    post.export_indicator(geography, df_counties, path_wb, about)

                path_wb = path_ / workbook_name3
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MSA'
                    post.export_indicator(geography, df_msa, path_wb, about, df_about)
                else:
                    post.export_indicator(geography, df_msa, path_wb, about)

                path_wb = path_ / workbook_name4
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                    post.export_indicator(geography, df_mpo, path_wb, about, df_about)
                else:
                    post.export_indicator(geography, df_mpo, path_wb, about)

            
            if sample_type == 'FOODSEC':

                path_wb = path_ / workbook_name1
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Counties'
                    post.export_indicator(geography, df_counties, path_wb, about, df_about)
                else:
                    post.export_indicator(geography, df_counties, path_wb, about)

                path_wb = path_ / workbook_name2
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                    post.export_indicator(geography, df_mpo, path_wb, about)
                else:
                    post.export_indicator(geography, df_mpo, path_wb, about)


    print(); print()      








