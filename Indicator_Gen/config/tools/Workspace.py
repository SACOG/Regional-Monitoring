



## Packages ---

# General
import numpy as np
import pandas as pd
import os
from tqdm import tqdm
import re
from datetime import date
import math
import seaborn as sns
import time
import requests
import ast
import functools as ft

# Plotting
import matplotlib.pyplot as plt
import plotly
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
from plotly.offline import plot
import plotly.subplots as sp
from plotly.subplots import make_subplots
pd.options.display.float_format = '{:.2f}'.format


## File Paths ---

# Define user
user = os.getlogin()
path_users = os.path.join('C:\\Users', user)

if user == 'jfontes':
    # Git
    path_git     = os.path.join(path_users, 'Documents', 'Projects', 'Regional-Monitoring', 'Indicator_Gen')
    path_config0 = os.path.join(path_git, 'config')


## User defined functions
exec(open(os.path.join(path_config0, 'Functions.py')).read())