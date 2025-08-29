





rerun=True
export=False
about=False
update=False
server=False
mpo = 'Yes'
unincorporated = 'Yes'



# TODO:
# Still working on how to incorporate some of the pre, get, post params/functions in here...
# Not going so well, but haven't spent too much time so we will see...

# Post functions had major updates with how I was implementing the mappings of columns and what have you
# This is starting to become a good case for making classes possibly... baby steps!



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


sys.path.append(str(path_config))
import pre
import get
import post


def set_workbook_name(indicator, estimate, sample_type, geography, margin_of_error, path_orig):

    if geography == 'PUMA':
        estimate = re.sub('ACS', 'PUMS', estimate)
    if sample_type == 'SUBJECT':
        estimate = re.sub('ACS', 'SUBJECT', estimate)
    if sample_type == 'DP':
        estimate = re.sub('ACS', 'DP', estimate)
    
    if margin_of_error == 'No':
        end = 'NoME_raw.csv'
    else:
        end = 'raw.csv'

    if sample_type == 'LEHD':
        export_name = f"{indicator}_{geography}_{sample_type}_{end}"
    else:
        export_name = f"{indicator}_{geography}_{estimate}_{end}"
    
    print(); print()
    print(f"Exporting {export_name} to the following location: ")
    print(path_orig)
    print()

    return export_name





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

    file_in = path_orig / set_workbook_name(indicator, estimate, sample_type, geography, margin_of_error, path_orig)
    df_census = pd.read_csv(file_in)
    display(df_census.head())




    # Processing


    print(); print()


    if sample_type in ['ACS', 'DP', 'SUBJECT', 'DEC']:
        if sample_type == 'SUBJECT':
            estimate = re.sub('SUBJECT', 'ACS', estimate)
        if sample_type == 'DP':
            estimate = re.sub('DP', 'ACS', estimate)

        # Replace weird missing values with np.nan
        # Melt data from wide to long
        # Convert imported values to numeric
        # Manually check column names and clean as needed
        # Adjust dollars for inflation, if needed
        # Reorganize margin of error fields
        if geography == 'Counties':
            df_census = post.acs_processing_1(df_census, df_vars, geography, margin_of_error, post.dt_clean_cols, post.dt_geoid_clean, mpo, df_fips)
        else:
            df_census = post.acs_processing_1(df_census, df_vars, geography, margin_of_error, post.dt_clean_cols, post.dt_geoid_clean, mpo)
        print(df_census.Year.unique())
        display(df_census.head(3))


        # Merge cleam label field, variable mapping, race/ethnicity, and sorting field
        # Remove unneeded columns
        # Sort by geography, variable mapping, and race/ethnicity
        df_census = post.acs_processing_2(df_census, df_vars, estimate, indicator, geography, margin_of_error, year_end, 
                                            path_main, path_config0, weighted_by, post.dt_geoid_clean, post.dt_geo_sheets, unincorporated)
        print(df_census.Year.unique())
        display(df_census.head(3))


        # Final processing step for ACS data
        # Link various FIPS codes
        # Roll up population/households/SE's to the desired geography and variable groupings
        # Calculate percentages by geography, race/ethnicity, and variables

        if geography == 'Counties':
            if mpo == 'Yes':
                df_census, df_mpo = post.acs_processing_3(df_census, estimate, indicator, geography, percentages, margin_of_error, MOE_thresh, num_vars, 
                                                            post.dt_geoid_clean, weighted_by, project, export_loc, path_server, metric, unincorporated, mpo)
            else:
                df_census = post.acs_processing_3(df_census, estimate, indicator, geography, percentages, margin_of_error, MOE_thresh, num_vars, 
                                                    post.dt_geoid_clean, weighted_by, project, export_loc, path_server, metric, unincorporated, mpo)
        else:
            df_census = post.acs_processing_3(df_census, estimate, indicator, geography, percentages, margin_of_error, MOE_thresh, num_vars, 
                                                post.dt_geoid_clean, weighted_by, project, export_loc, path_server, metric, unincorporated, mpo)
        print(df_census.Year.unique())
        display(df_census.head(3))





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
        print('Groups: ' + ', '.join(groups))
        display(df_census.head(3))

        # Remove rows with missing values
        # Only keep description mappings, remove the original PUMS values
        df_census = post.pums_processing_2(df_census, estimate, sample_type, groups, df_fips, dt_fips)
        display(df_census.head(3))

        # Cleans race/ethnicity fields
        # Creates additional grouping variables for certain indicators
        # Adjusts income variables by inflation for the latest year
        df_census, groups = post.pums_processing_3(df_census, groups, indicator, path_config0)
        print('Groups: ' + ', '.join(groups))
        display(df_census.head(3))

        # Roll up using suggested weight field
        # Roll up to PUMA, counties, MSA, and MPO
        if sample_type == 'PUMS':
            df_puma, df_counties, df_msa, df_mpo, groups = post.pums_processing_4(df_census, indicator, weight, margin_of_error, MOE_thresh, percentages, groups)
            display(df_puma.head(3), df_counties.head(3), df_msa.head(3), df_mpo.head(3))

        # Roll up using suggested weight field
        # Roll up to counties and MPO
        if sample_type == 'FOODSEC':
            df_counties, df_mpo, groups = food_processing_4(df_census, weight, percentages, groups)
            display(df_counties.head(3), df_mpo.head(3))


    if sample_type == 'LEHD':
        if geography == 'Counties':
            df_census, df_mpo = lehd_processing(df_census, geography, indicator, percentages, df_fips)
            display(df_census.head(3), df_mpo.head(3))
        if geography == 'MSA':
            df_census = lehd_processing(df_census, geography, indicator, percentages)
            display(df_census.head(3))




    # Final organization of tables for cleanliness
    # Renaming columns, subsetting to only desired columns, ...

    print(); print()
    print('Final Results: ')
    print()

    if geography not in ['Counties', 'PUMA']:
        df_census = rename_census(df_census           = df_census
                                    , geography       = geography
                                    , dt_geoid_clean  = dt_geoid_clean
                                    , indicator       = indicator
                                    , margin_of_error = margin_of_error
                                    , percentages     = percentages
                                    , sample_type     = sample_type)
        display(df_census)
    if geography == 'Counties':
        if sample_type in ['ACS', 'DP', 'SUBJECT', 'DEC']:
            if mpo == 'Yes':
                df_census, df_mpo = rename_census(df_census           = df_census
                                                    , df_mpo          = df_mpo
                                                    , geography       = geography
                                                    , dt_geoid_clean  = dt_geoid_clean
                                                    , indicator       = indicator
                                                    , margin_of_error = margin_of_error
                                                    , percentages     = percentages
                                                    , sample_type     = sample_type
                                                    , df_vars         = df_vars)
                display(df_census, df_mpo)
            else:
                df_census = rename_census(df_census           = df_census
                                            , geography       = geography
                                            , dt_geoid_clean  = dt_geoid_clean
                                            , indicator       = indicator
                                            , margin_of_error = margin_of_error
                                            , percentages     = percentages
                                            , sample_type     = sample_type)
                display(df_census)
    if geography == 'PUMA':
        df_puma, df_counties, df_msa, df_mpo = rename_census(df_puma              = df_puma
                                                                , df_counties     = df_counties
                                                                , df_msa          = df_msa
                                                                , df_mpo          = df_mpo
                                                                , geography       = geography
                                                                , indicator       = indicator
                                                                , margin_of_error = margin_of_error
                                                                , percentages     = percentages
                                                                , sample_type     = sample_type
                                                                , groups          = groups
                                                                , table_type      = table_type)
        display(df_puma, df_counties, df_msa, df_mpo)





    ## Exporting ===============================================================================================================


    # if export:
    #     if about:
    #         estimate = re.sub('PUMS', 'ACS', estimate)
    #         if update:
    #             path_about = path_sp / 'Process Revamp' / 'Task 6. Process Map'
    #             year_start = df_census_raw.Year.min()
    #             year_end   = df_census_raw.Year.max()
    #             df_about = write_about(sample_type     = sample_type
    #                                     , indicator    = indicator
    #                                     , year_start   = year_start
    #                                     , year_end     = year_end
    #                                     , path_config0 = path_config0
    #                                     , MOE_thresh   = MOE_thresh
    #                                     , estimate     = estimate)
    #             file_about = path_about / 'About Indicators.xlsx'
    #             with pd.ExcelWriter(file_about, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
    #                 df_about.to_excel(writer, index=False, sheet_name=indicator, header=False)


    # if export:
    #     if about:
    #         if estimate not in ['LEHD', 'CPS']:
    #             df_about = write_about(sample_type     = sample_type
    #                                     , indicator    = indicator
    #                                     , year_start   = year_start
    #                                     , year_end     = year_end
    #                                     , path_config0 = path_config0
    #                                     , geography    = geography
    #                                     , MOE_thresh   = MOE_thresh
    #                                     , estimate     = estimate)
    #             if geography == 'Counties':
    #                 if mpo == 'Yes':
    #                     geography = 'MPO'
    #                     df_about_mpo = write_about(sample_type     = sample_type
    #                                                 , indicator    = indicator
    #                                                 , year_start   = year_start
    #                                                 , year_end     = year_end
    #                                                 , path_config0 = path_config0
    #                                                 , geography    = geography
    #                                                 , MOE_thresh   = MOE_thresh
    #                                                 , estimate     = estimate)
    #                     geography = 'Counties'
    #                 else: pass
    #         else:
    #             df_about = write_about(sample_type     = sample_type
    #                                     , indicator    = indicator
    #                                     , year_start   = year_start
    #                                     , year_end     = year_end
    #                                     , path_config0 = path_config0
    #                                     , geography    = geography
    #                                     , estimate     = estimate)



    if geography == 'Counties':
        if mpo == 'Yes':
            df_about, df_about_mpo = write_about_master(export, about, update, df_census_raw, indicator, sample_type, geography, estimate, mpo, MOE_thresh, path_config0, path_about)
        else:
            df_about = write_about_master(export, about, update, df_census_raw, indicator, sample_type, geography, estimate, mpo, MOE_thresh, path_config0, path_about)
    else:
        df_about = write_about_master(export, about, update, df_census_raw, indicator, sample_type, geography, estimate, mpo, MOE_thresh, path_config0, path_about)
    print("About documentation of the output for:", indicator)
    display(df_about)



    print(); print()

    if export:
        if sample_type == 'SUBJECT':
            estimate = re.sub('ACS', 'SUBJECT', estimate)
        if sample_type == 'DP':
            estimate = re.sub('ACS', 'DP', estimate)

        if geography == 'PUMA':
            estimate = re.sub('ACS', 'PUMS', estimate)
            workbook_name1 = f"{indicator} PUMA {estimate}.xlsx"
            workbook_name2 = f"{indicator} Counties {estimate}.xlsx"
            workbook_name3 = f"{indicator} MSA {estimate}.xlsx"
            workbook_name4 = f"{indicator} MPO {estimate}.xlsx"
            print(workbook_name1)
            print(workbook_name2)
            print(workbook_name3)
            print(workbook_name4)
        
        elif geography == 'Counties':
            workbook_name1 = f"{indicator} {geography} {estimate}.xlsx"
            print(workbook_name1)
            if mpo == 'Yes':
                workbook_name2 = f"{indicator} MPO {estimate}.xlsx"
                print(workbook_name2)
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

        if project == 'Monitoring and Reporting':
            if server:
                paths = [path_out_server, path_out_sp]
            else: paths = [path_out_sp]
        else:
            paths = [path_out_sp]
        
        for path_ in paths:
            try:
                path_wb = path_ / workbook_name
            except: pass
            
            if sample_type in ['ACS', 'DP', 'SUBJECT', 'DEC']:
                if geography == 'Places':
                    if about:
                        df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Census Designated Places (Jurisdictions)'
                if geography != 'Counties':
                    export_indicator(geography, df_census, path_wb, about)
                if geography == 'Counties':
                    path_wb = path_ / workbook_name1
                    if about:
                        df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Counties'
                    export_indicator(geography, df_census, path_wb, about)
                    if mpo == 'Yes':
                        path_wb = path_ / workbook_name2
                        if about:
                            df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                        export_indicator(geography, df_mpo, path_wb, about)
            
            if sample_type == 'PUMS':
                path_wb = path_ / workbook_name1
                export_indicator(geography, df_puma, path_wb, about)
                path_wb = path_ / workbook_name2
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Counties'
                export_indicator(geography, df_counties, path_wb, about)
                path_wb = path_ / workbook_name3
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MSA'
                export_indicator(geography, df_msa, path_wb, about)
                path_wb = path_ / workbook_name4
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                export_indicator(geography, df_mpo, path_wb, about)
            
            if sample_type == 'FOODSEC':
                path_wb = path_ / workbook_name1
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Counties'
                export_indicator(geography, df_counties, path_wb, about)
                path_wb = path_ / workbook_name2
                if about:
                    df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                export_indicator(geography, df_mpo, path_wb, about)
            
            if sample_type == 'LEHD':
                if geography == 'Counties':
                    path_wb = path_ / workbook_name1
                    if about:
                        df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'Counties'
                    export_indicator(geography, df_census, path_wb, about)
                    path_wb = path_ / workbook_name2
                    if about:
                        df_about.loc[df_about['Indicator'] == 'Geography', indicator] = 'MPO'
                    export_indicator(geography, df_mpo, path_wb, about)
                if geography == 'MSA':
                    path_wb = path_ / workbook_name
                    export_indicator(geography, df_census, path_wb, about)






