# Regional-Monitoring
The Regional Progress Report tracks change across economic growth, development, travel, and other important indicators in the Sacramento region.  By assessing where the region is on a range of key topics, the Progress Report serves as a first step for updating the Metropolitan Transportation Plan/Sustainable Communities Strategy (MTP/SCS), SACOG’s long-range plan updated every four years to pro-actively link land use, air quality, and transportation needs in the Sacramento region. The Progress Report is provided in part to help identify important issues that should be prioritized in the next MTP/SCS update.  There is a live public-facing ArcGIS Online Dashboard that supports the Regional Progress Report, which can be found here:

This repository contains a majority of the Python code used to collect, process, and interpret the data required for the report and dashbaord.  

__Note from the owner__:  (For the data sources that have an API) The data pipelines built for regional monitoring can be used by anyone who would like to streamline their approach to data collection using an API with Python.  The data processing steps can also be used by anyone, but they are geared towards how SACOG wants to track indicators (specific estimate groupings, inflation adjustments, income brackets, race/ethnicity definitions, ...).  I tried to build the pipelines in a simple and user-friendly approach that anyone can use with some practice.


## Repository organization:

(1) __code__ folders:
- The __Python Code__ folder has a folder for each data source we collect
- Data sources with an API available: Census Bureau, BLS, ...
    - Data pipeline:
        1) Importing
        2) Processing
        3) Data Visualization
        4) Exporting to Dashboard
      *Steps 2-4 are specific processing steps for SACOG specific indicators
- Data sources without an API available: TIMS, DOF, RTIS, Zillow, ... (technically, Zillow has an API, SACOG just doesn't meet the terms of use requirements)

(2) __config__ folders:
- There is an overall config folder and a subsequent config folder for the data sources that have an API
- The overall __config__ folder:
    - "Area Codes.xlsx" - a workbook that has all needed area code mappings (counties to PUMA's, counties to MSA's, census tracts to counties, ...) required for all indicators
    - "CA State Income Brackets by Household Size.xlsx" - a table that shows the CA state income brackets by household size by county (for indicators that require income brackets)
    - "CPI Inflation Adjustment Factors.xlsx" - a workbook that has various inflation adjustment factors (for indicators that include $-USD)
    - "about_indicators.yaml" - a _.yaml_ file used to create the documentation files associated with each indicator
    - "Functions.py" - a python script with user defined functions that all data sources utilize
 - Data source __config__ folder:
    - "Configuration File.xlsx" - a workbook that initializes the data pipeline (requires user to set which geographies, estimates, years, ... are needed to make the API request)
    - "Functions.py" - a python script with user defined functions that the specific data source requires



## How to use:


Each pipeline run requires the "Configuration File.xlsx" excel workbook.  This workbook allows the user to set up exactly which geographies and estimates they want to pull.  The user needs to define an "indicator" that is linked to those estimates... (summary in progress)
