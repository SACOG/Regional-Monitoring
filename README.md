# Regional-Monitoring
The Regional Progress Report tracks change across economic growth, development, travel, and other important indicators in the Sacramento region.  By assessing where the region is on a range of key topics, the Progress Report serves as a first step for updating the Metropolitan Transportation Plan/Sustainable Communities Strategy (MTP/SCS), SACOG’s long-range plan updated every four years to pro-actively link land use, air quality, and transportation needs in the Sacramento region. The Progress Report is provided in part to help identify important issues that should be prioritized in the next MTP/SCS update.  There is a live public-facing ArcGIS Online Dashboard that supports the Regional Progress Report, which can be found here:

This repository contains a majority of the Python code used to collect, process, and interpret the data required for the report and dashbaord.  

__Note from the owner__:  (For the data sources that have an API) The data pipelines built for regional monitoring can be used by anyone who would like to streamline their approach to data collection using an API with Python.  The data processing step is geared towards how SACOG wants to track indicators (specific estimate groupings, inflation adjustments, income brackets, race/ethnicity definitions, ...) but can still be used by others as needed.  I tried to build the pipelines in a simple and user-friendly approach that anyone can use with some practice.


## Repository organization:

(1) [__Data__](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/Data):
- This folder contains all code used to import/process data used for regional monitoring (pipelines for data sources with an API)
- Each data source has their own folder
- Data sources with an API available: Census Bureau, BLS, EPA, and EIA
    - Data pipeline:
        1) Importing
        2) Processing
      
      *The processing step is specific processing steps for SACOG specific indicators
- Data sources without an API available: TIMS, DOF, RTIS, Zillow, ... (technically, Zillow has an API, SACOG just doesn't meet the terms of use requirements)
      - These data sources typically have one "processing" script, since we have no way of importing the data through an API (we download the data manually and store locally or on our SQL server)

(2) [__config__](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/config):
- These folders contain all necessary files needed to configure a data pipeline located in the data folder
- There is an overall config folder and a subsequent config folder for the data sources that have an API
- The overall __config__ folder:
    - [Area Codes.xlsx](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/Area%20Codes.xlsx) - a workbook that has all needed area code mappings (counties to PUMA's, counties to MSA's, census tracts to counties, ...) required for all indicators
    - [CA State Income Brackets by Household Size.xlsx](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/CA%20State%20Income%20Brackets%20by%20Household%20Size.xlsx) - a table that shows the CA state income brackets by household size by county (for indicators that require income brackets)
    - [CPI Inflation Adjustment Factors.xlsx](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/CPI%20Inflation%20Adjustment%20Factors.xlsx) - a workbook that has various inflation adjustment factors (for indicators that include $-USD)
    - [about_indicators.yaml](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/about_indicators.yaml) - a _yaml_ file used to create the documentation files associated with each indicator
    - [config_indicators.yaml](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/config_indicators.yaml) - a _yaml_ file used to configure the data pipeline that pulls/processes data
    - [Functions.py](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/Functions.py) - a python script with user defined functions that all data sources utilize
 - Data source __config__ folder:
    - "configuration_file.xlsx" - a workbook that initializes the data pipeline (requires user to set which geographies, estimates, years, ... are needed to make the API request)
    - "functions.py" - a python script with user defined functions that the specific data source requires

(3) [__AGOL Dashboard__](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/AGOL%20Dashboard):
- This folder contains all code that is used to build the plots/charts used in the online public-facing AGOL dashboard
- The _plotly_ library is used for all data visualizations
- Each data source has their own script
- Each plot is exported as an _html_ file to our internal server, which is then linked to the dashboard


## How to use data pipeline for data sources with an API:

This is only relevant to the [BLS](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/Data/BLS), [EPA](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/Data/EPA), [EIA](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/Data/EIA) and [Census](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/Data/Census) folders.  Using the Census Bureau and ACS data as an example:

Before running any code, make sure your Python environment is compatible with all or most packages listed in the [requirements.txt](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/requirements.txt) page.  For ACS data, check to make sure we are up to date with any data releases at the [American Community Survey Data Releases](https://www.census.gov/programs-surveys/acs/news/data-releases.html).  If there is a new data release (usually December of each year), update the variables using the [update_vars.py](https://github.com/SACOG/Regional-Monitoring/blob/joshmain3/Indicator_Gen/Data/Census/config/step0/update_vars.py) script, update the area codes using the [update_FIPS.py](https://github.com/SACOG/Regional-Monitoring/blob/joshmain3/Indicator_Gen/Data/Census/config/step0/update_FIPS.py) script, and update the URL’s using the [update_URL.py](https://github.com/SACOG/Regional-Monitoring/blob/joshmain3/Indicator_Gen/Data/Census/config/step0/update_URL.py) script.

To update any indicator pulled from ACS data, start in the [Census](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/Data/Census) Data folder.  Then check/update both configuration files: [config_indicators.yaml](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/config_indicators.yaml) and [census_configuration_file2.xlsx](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/Data/Census/config/census_configuration_file2.xlsx).  Also, check the [census_functions.py](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/Data/Census/config/census_functions.py) script.  All of these files are used to make the API request and/or process the requested data, as well as some files already mentioned in the overall [config](https://github.com/SACOG/Regional-Monitoring/tree/main/Indicator_Gen/config) folder.

Open the [census_configuration_file2.xlsx](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/Data/Census/config/census_configuration_file2.xlsx) workbook.  This workbook summarizes the Census Bureau API data structure. The survey tabs (ACS, PUMS, etc…) is where the user configures variables for the data pipeline, meaning they organize the variable IDs, labels, years, etc… and set the name of the indicator.  The geography tabs (Counties, State, and MSA, depending on which geography you wish to pull data from) is also where the user sets which geographies they would like to pull data from.  This workbook helps organize which estimates and which geographies are set for the API request in Python.

Open the [config_indicators.yaml](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/config/config_indicators.yaml) file.  This helps organize indicators by project and where to export the file, what sample they come from, the number of variables, whether to calculate percentages by the user defined groups, and what the desired margin of error threshold is.  This config file also has parameters for each sample and geography level, like years available and which geography to use for importing.  The user needs to make sure this is configured properly if setting up a new indicator.

After checking/modifying the configurations files, run the Python script [step01__request_census.py](https://github.com/SACOG/Regional-Monitoring/blob/main/Indicator_Gen/Data/Census/step01__request_census.py).  The code imports the configuration files to form the API request.  Here is an example:
1.	Which project are you pulling data for? – __Monitoring and Reporting__
2.	Which indicator do you need to rerun? – __Commute_1__
3.	Which estimate do you want to pull data from? – __ACS5__
4.	Which geography do you want to pull data for? – __MSA__
5.	Do you want to pull data for all years?  Select Yes/No: - __Yes__
6.	Do you want to pull the Margin of Error estimates?  Select Yes/No: - __Yes__

*Note – These user inputs will request data from the ACS sample all ACS 5-year estimate data and margin of errors for all input MSA’s for all variables that are linked to Commute_1 from the years 2009 to 2023.  Notice how the each question offers a list of input options provided from the config_indicators.yaml file.  To see which variables are currently linked to the Commute_1 indicator, in the census_configuration_file2.xlsx workbook, navigate to the “ACS” tab and filter the “Indicator Name” to Commute_1.  To see which MSAs are set to import, navigate to the “MSA” tab. These mappings can be updated as needed.*
