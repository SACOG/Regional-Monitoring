# Regional-Monitoring
The Regional Progress Report tracks change across economic growth, development, travel, and other important indicators in the Sacramento region.  By assessing where the region is on a range of key topics, the Progress Report serves as a first step for updating the Metropolitan Transportation Plan/Sustainable Communities Strategy (MTP/SCS), SACOG’s long-range plan updated every four years to pro-actively link land use, air quality, and transportation needs in the Sacramento region. The Progress Report is provided in part to help identify important issues that should be prioritized in the next MTP/SCS update.  There is a live public-facing ArcGIS Online Dashboard that supports the Regional Progress Report, which can be found here:

This repository contains a majority of the Python code used to collect, process, and interpret the data required for the report and dashbaord.  

__Note from the owner__:  (For the data sources that have an API) The data pipelines built for regional monitoring can be used by anyone who would like to streamline their approach to data collection using an API with Python.  The data processing step is geared towards how SACOG wants to track indicators (specific estimate groupings, inflation adjustments, income brackets, race/ethnicity definitions, ...) but can still be used by others as needed.  I tried to build the pipelines in a simple and user-friendly approach that anyone can use with some practice.


## Repository organization:

(1) __Data__:
- This folder contains all code used to import/process data used for regional monitoring (pipelines for data sources with an API)
- Each data source has their own folder
- Data sources with an API available: Census Bureau, BLS, ...
    - Data pipeline:
        1) Importing
        2) Processing
      
      *The processing step is specific processing steps for SACOG specific indicators
- Data sources without an API available: TIMS, DOF, RTIS, Zillow, ... (technically, Zillow has an API, SACOG just doesn't meet the terms of use requirements)
      - These data sources typically have one "processing" script, since we have no way of importing the data through an API (we download the data manually and store locally or on our SQL server)

(2) __config__:
- These folders contain all necessary files needed to configure a data pipeline located in the data folder
- There is an overall config folder and a subsequent config folder for the data sources that have an API
- The overall __config__ folder:
    - "Area Codes.xlsx" - a workbook that has all needed area code mappings (counties to PUMA's, counties to MSA's, census tracts to counties, ...) required for all indicators
    - "CA State Income Brackets by Household Size.xlsx" - a table that shows the CA state income brackets by household size by county (for indicators that require income brackets)
    - "CPI Inflation Adjustment Factors.xlsx" - a workbook that has various inflation adjustment factors (for indicators that include $-USD)
    - "about_indicators.yaml" - a _yaml_ file used to create the documentation files associated with each indicator
    - "Functions.py" - a python script with user defined functions that all data sources utilize
 - Data source __config__ folder:
    - "Configuration File.xlsx" - a workbook that initializes the data pipeline (requires user to set which geographies, estimates, years, ... are needed to make the API request)
    - "Functions.py" - a python script with user defined functions that the specific data source requires

(3) __AGOL Dashboard__:
- This folder contains all code that is used to build the plots/charts used in the online public-facing AGOL dashboard
- The _plotly_ library is used for all data visualizations
- Each data source has their own script
- Each plot is exported as an _html_ file to our internal server, which is then linked to the dashboard


## How to use data pipeline for data sources with an API:

This is only relevant to the _BLS_ and _Census_ folders.  Using the Census Bureau as an example:

The data pipeline for the Census Bureau can be found in the _Regional-Monitoring/Indicator_Gen/Data/Census_ folder.  The Census Bureau has data from multiple surveys and samples that can be accessed through an API.  This link here https://api.census.gov/data.html, tells you exactly which surveys have data available through their API and how to access them (which geographies are available, what variables are available, which years, and exactly how to write the API request query).  The "Census Configuration File.xlsx" workbook found in the _config_ folder summarizes their API data structure.  This is where a user configures the data pipeline, meaning they can set up which survey/sample, years, variables, and geographies they would like to pull data from.

For example, suppose a user would like to pull data for the Sacramento region on means of transportation to work from the American Community Survey (Table ID B08301):
(1) Start with the "ACS" tab.  This contains all the tables/variables that can be pulled from ACS (https://api.census.gov/data/2022/acs/acs5/variables.html). The user sets the "Indicator Name" and "Include" columns to define which variables they would like to pull data for (columns I through L are used for the processing step, if needed).  The "Indicator Name" is a user defined reference table name.  The "Include" column requires a Yes/No input.  For Table ID B08301, the indicator name is currently defined as "Commute_1" and the estimates are set to include _Estimate!!Total:!!Car, truck, or van:!!Drove alone_, _Estimate!!Total:!!Car, truck, or van:!!Carpooled:_, etc...
(2) 




(Detailed instructions in progress)
