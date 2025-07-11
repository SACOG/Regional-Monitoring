

import numpy as np
import pandas as pd
import os
import json
from tqdm import tqdm
import re
from datetime import date
import requests
import ast
import xlwt
from xlwt.Workbook import *
from pandas import ExcelWriter
import xlsxwriter
import yaml

# Plotting
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio






"""
User defined function to organize Series ID's into structure that the BLS API can understand https://www.bls.gov/developers/api_signature_v2.htm
Using the workbook "BLS Configuration File.xlsx", we create a dictionary of all Series ID's and what years we want to request data for.  The
structure of the Series ID depends on the survey we want data from https://www.bls.gov/help/hlpforma.htm#EN.
"""

def dict_maker(survey, geography, seasonal, df=None, list_sectors=None, data_type=None, measure_code=None):

    keys = []
    vals = []

    if geography == 'MSA':
        
        # Loop through each MSA code
        # Construct the Series ID
        # Add Series ID and MSA label to lists
        
        for i in range(len(df)):
            
            area_code = str(df.loc[i, 'area_code'])
    
            if survey in ['LA']:
                series_id = [str(survey) + str(seasonal) + str(area_code)  + str(measure_code)]

            if survey in ['SM', 'CE']:
                state     = str(df.loc[i, 'State FIPS'])
                series_id = list(map(lambda sector: str(survey) + str(seasonal) + str(state) + str(area_code) + str(sector) + str(data_type), list_sectors))
                
            keys.append(str(df.loc[i, 'area_text']))
            vals.append(series_id)
        
    if geography == 'National':

        # Pull National level area code
        # Construct the Series ID
        # Add Series ID and National label to lists

        if survey in ['LA']:
                series_id = str(survey) + str(seasonal) + str(area_code)  + str(measure_code)
        if survey in ['SM', 'CE']:
            series_id = list(map(lambda sector: str(survey) + str(seasonal) + str(sector) + str(data_type), list_sectors))
                
        keys.append('National')
        vals.append(series_id)


    # Convert list of keys and values to dictionary
    result = {k: v for k, v in zip(keys, vals)}
    
    return result

        



