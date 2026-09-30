

'''
NOTE: I don't know why but every solution I've tried cannot remove the updated tag programatically
I'm sure there is a way of doing it, but since you'd have to QC the changes manually, might as well just delete them manually too (only takes a second)

'''


# Setup -----------------------------------------------------------------------------------------------------------------------------------------


from pathlib import Path
import html
from bs4 import BeautifulSoup
import re
import sys
sys.path.append(str(Path(__file__).parent))
import experience as exp






def remove_updated_tag(exp_draft, indicator, yaml_exp):

    # def remove_tag(text):
    #     decoded = html.unescape(text)
    #     soup = BeautifulSoup(decoded, "html.parser")

    #     for span in soup.find_all("span"):
    #         if "Updated" in span.text:
    #             span.decompose()  # removes the tag completely

    #     clean_html = str(soup)
    #     clean_text = html.escape(clean_html)

    #     return clean_text

    def remove_tag(text):
        start = text.find('&lt;span')
        while start != -1:
            end = text.find('&lt;/span&gt;', start)
            if end == -1:
                break
            
            snippet = text[start:end]
            if 'Updated' in snippet:
                end += len('&lt;/span&gt;')
                text = text[:start] + text[end:]
            else:
                start = text.find('&lt;span', end)
                continue
            
            start = text.find('&lt;span')
        
        return text

    print(f'Updating recently updated tag for indicator {indicator} on dashboard...')
    yaml_homepage = yaml_exp['Homepage']
    if isinstance(yaml_homepage[indicator][0], list):
        block_name = yaml_homepage[indicator][0][0]
    else:
        block_name = yaml_homepage[indicator][0]
    widget = exp.get_widget(exp_draft, block_name)
    text = exp_draft['widgets'][widget]['config']['text']
    # tag = """<span style="  font-size: 10.5px;  font-family: 'Microsoft YaHei';  color: rgb(0, 125, 200);  background-color: rgb(240, 240, 240);  padding: 2px 6px;  border-radius: 4px;  margin-left: 6px;"> Updated Recently </span>"""
    tag = """<span style="  font-size: 10.5px;  font-family: \'Microsoft YaHei\';  color: rgb(0, 125, 200);  background-color: rgb(240, 240, 240);  padding: 2px 6px;  border-radius: 4px;  margin-left: 6px;"> Updated Recently </span>"""

    if tag in text:
        # exp_draft['widgets'][widget]['config']['text'] = re.sub(f'>{title}</a></strong>{tag}', f'>{title}</a></strong>', text)
        # exp_draft['widgets'][widget]['config']['text'] = 
        breakpoint()
        text = remove_tag(text)



    return exp_draft




# Main --------------------------------------------------------------------------------------------------------------------------------------



UPDATE = True


# indicator = 'Production_1'
# indicator = ['Production_1', 'Production_2', 'Production_3', 'Production_4', 'Production_6', 'Production_7']
indicator = 'Jobs_1'

if __name__ == '__main__':

    yaml_exp = exp.read_yaml_exp()
    gis = exp.connect_to_agol()
    item, exp_builder_app, exp_draft = exp.get_draft_exp_builder_app(gis, exp.ID_REGIONAL_INDICATORS_DASHBOARD)

    if isinstance(indicator, str):
        exp_draft = remove_updated_tag(exp_draft, indicator, yaml_exp)
    if isinstance(indicator, list):
        for ind in indicator:
            exp_draft = remove_updated_tag(exp_draft, ind, yaml_exp)

    if UPDATE:
        exp.save_draft_exp_builder_app(exp_builder_app, exp_draft)



