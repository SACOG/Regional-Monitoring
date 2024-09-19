# Regional-Monitoring
The Regional Progress Report tracks change across economic growth, development, travel, and other important indicators in the Sacramento region.  By assessing where the region is on a range of key topics the Progress Report serves as a first step for updating the Metropolitan Transportation Plan/Sustainable Communities Strategy (MTP/SCS), SACOG’s long-range plan updated every four years to pro-actively link land use, air quality, and transportation needs in the Sacramento region. The Progress Report is provided in part to help identify important issues that should be prioritized in the next MTP/SCS update.  There is a live public-facing ArcGIS Online Dashboard that supports the Regional Progress Report, which can be found here:

This repository contains a majority of the Python code used to collect, process, and interpret the data required for the report and dashbaord.

Repository organization:
(1) __code__ folders:
- The "Python Code" folder has a folder for each data source we collect
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
- The overall config folder:
    - "Area Codes.xlsx" - a workbook that has all needed area code mappings (counties to PUMA's, counties to MSA's, census tracts to counties, ...)
    - "CA State Income Brackets by Household Size.xlsx" - a workbook that 

