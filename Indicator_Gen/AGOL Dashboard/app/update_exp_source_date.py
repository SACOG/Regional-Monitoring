

'''
Python script used to update the "Last updated: " and "Recently Updated" tags that are in the unpublished changes of the Regional Indicators Dashboard
https://experience.arcgis.com/experience/37547feca64546dbbd0a4030dd84bb42?draft=true


THEME -> User to input which page needs to be updated
INDICATOR -> User to input which indicator needs to be updated
UPDATE -> True/False -> When user is testing, use False, when user is ready to save draft changes, use True

NOTE: User can access all themes and indicators in the exp.yaml file


TODO:
Need to either try and replace "Updated {old year}" with "Updated {new year}" (could be as easy as find/replace 2025 for 2026?)
OR
Just manually delete the badge in AGOL, then re apply the badge by running this script

'''


# Setup -----------------------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
import re
from datetime import date
import sys
sys.path.append(str(Path(__file__).parent))
import experience as exp



def update_last_updated_date(exp_draft, indicator):

    '''
    Updates local experience bulder draft object with today's date

    Inputs:
        exp_draft = fetched json object of the draft version of the regional indicators experience builder app
        theme = Which page on the dashboard do you want to update?
        indicator = Which indicator on the selected theme page do you want to update?

    returns a python dictionary that represents the updated experience builder app
    '''

    print(f'Updating recently updated tag for indicator {indicator} on dashboard...')
    block_name = f'Source {indicator}'
    widget = exp.get_widget(exp_draft, block_name)
    text = exp_draft['widgets'][widget]['config']['text']
    today = date.today().strftime("%Y-%m-%d")
    
    if "Last Updated:" not in text:
        raise ValueError("Unexpected text format — aborting update")

    exp_draft['widgets'][widget]['config']['text'] = re.sub(r"Last Updated: \d{4}-\d{2}-\d{2}", f"Last Updated: {today}", text)

    return exp_draft


def tag_recently_updated(exp_draft, indicator, yaml_exp):

    print(f'Updating recently updated tag for indicator {indicator} on dashboard...')
    yaml_homepage = yaml_exp['Homepage']
    if isinstance(yaml_homepage[indicator][0], list):
        block_name = yaml_homepage[indicator][0][0]
        title = yaml_homepage[indicator][0][2]
    else:
        block_name = yaml_homepage[indicator][0]
        title = yaml_homepage[indicator][2]
    widget = exp.get_widget(exp_draft, block_name)
    text = exp_draft['widgets'][widget]['config']['text']
    tag = """<span style="  font-size: 10.5px;  font-family: 'Microsoft YaHei';  color: rgb(0, 125, 200);  background-color: rgb(240, 240, 240);  padding: 2px 6px;  border-radius: 4px;  margin-left: 6px;"> Updated 2026 </span>"""

    if f'>{title}</a></strong>{tag}' not in text:
        exp_draft['widgets'][widget]['config']['text'] = re.sub(f'>{title}</a></strong>', f'>{title}</a></strong>{tag}', text)

    return exp_draft




# Main --------------------------------------------------------------------------------------------------------------------------------------

UPDATE = False


# indicator = 'Production_1'
indicator = ['VMT_1']

if __name__ == '__main__':

    yaml_exp = exp.read_yaml_exp()
    gis = exp.connect_to_agol()
    item, exp_builder_app, exp_draft = exp.get_draft_exp_builder_app(gis, exp.ID_REGIONAL_INDICATORS_DASHBOARD)

    if isinstance(indicator, str):
        exp_draft = update_last_updated_date(exp_draft, indicator)
        exp_draft = tag_recently_updated(exp_draft, indicator, yaml_exp)
    if isinstance(indicator, list):
        for ind in indicator:
            exp_draft = update_last_updated_date(exp_draft, ind)
            exp_draft = tag_recently_updated(exp_draft, ind, yaml_exp)

    if UPDATE:
        breakpoint()
        exp.save_draft_exp_builder_app(exp_builder_app, exp_draft)



