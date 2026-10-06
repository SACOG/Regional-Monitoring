
from pathlib import Path
import yaml
import getpass
from arcgis.gis import GIS
from arcgis.apps.expbuilder import WebExperience


ID_REGIONAL_INDICATORS_DASHBOARD = '37547feca64546dbbd0a4030dd84bb42'
# ID_REGIONAL_INDICATORS_DASHBOARD = '1f9de462663043d38102a822d430a3ea' # BACKUP COPY USED FOR TESTING


def read_yaml_exp():

    '''
    Function to import the user defined exp.yaml file
    The exp.yaml file contains a mapping of all theme/indicator combinations to their respective widgets on the Regional Indicators Dashboard experience builder app

    Returns a python dictionary of the yaml file
    '''

    print('\nReading in yaml configuration file...\n')
    path_yaml = Path(__file__).parent / 'experience.yaml'
    
    try:
        with open(path_yaml, 'r') as yaml_file:
            yaml_exp = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    except FileNotFoundError:
        print(f"Error: The file at {path_yaml} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")
    
    return yaml_exp


def connect_to_agol():

    '''
    Function to connect to your ArcGIS Online account
    Have your username and password ready!

    Returns a GIS connection object, which can be used to access any app/item on the AGOL account
    '''

    print('\nSACOG AGOL Login:')
    agol_url = "https://sacog.maps.arcgis.com/home"
    agol_username = input('Username: ')
    agol_password = getpass.getpass("Password (hidden during input): ")
    print('\nSetting up AGOL connection...\n')
    gis = GIS(agol_url, agol_username, agol_password)

    return gis


def get_draft_exp_builder_app(gis, exp_id):
    
    '''
    Fetches the item, experience builder app, and draft version of the app

    Inputs:
        gis = the GIS connection object
        exp_id = the feature ID of the experience builder application

    Returns:
        item = experience builder application
        exp_builder_app = WebExperience object of the experience builder application
        exp_draft = python dictionary of the draft version of the experience builder app
    '''
    
    item = gis.content.get(exp_id)
    exp_builder_app = WebExperience(item)
    exp_draft = exp_builder_app._draft

    return item, exp_builder_app, exp_draft


def get_widget(exp_draft, block_name):

    '''
    Fetches the widget ID of the user defined block name (manually named in AGOL experience builder app)

    Inputs:
        exp_draft = python dictionary of the draft version of the experience builder app
        block_name = the actual name of the block in the AGOL experience builder app, for example "Source Production_1"

    Returns:
        widget = name of the widget ID
    '''

    widgets = exp_draft['widgets'].keys()

    for wid in widgets:
        if block_name in exp_draft['widgets'][wid]['label']:
            widget = wid
    
    return widget


def save_draft_exp_builder_app(exp_builder_app, exp_draft):

    '''
    Function used to save/push changes to the draft version of the application
    '''
    print('\nPushing changes to AGOL draft version...\n\n')
    exp_builder_app._draft = exp_draft
    exp_builder_app.save()




# def update_last_updated_date(exp_draft, yaml_exp, theme, indicator):

#     '''
#     Updates local experience bulder draft object with today's date

#     Inputs:
#         exp_draft = fetched json object of the draft version of the regional indicators experience builder app
#         yaml_exp = user defined yaml file that maps each theme/indicator combination to the respective default widget ID's (need to view the app in AGOL to figure this out)
#         theme = Which page on the dashboard do you want to update?
#         indicator = Which indicator on the selected theme page do you want to update?

#     returns a python dictionary that represents the updated experience builder app
#     '''

#     # widget = yaml_exp[theme][indicator]['Source']
#     text = exp_draft['widgets'][widget]['config']['text']
#     today = date.today().strftime("%Y-%m-%d")
    
#     if "Last Updated:" not in text:
#         raise ValueError("Unexpected text format — aborting update")

#     exp_draft['widgets'][widget]['config']['text'] = re.sub(r"Last Updated: \d{4}-\d{2}-\d{2}", f"Last Updated: {today}", text)

#     return exp_draft
