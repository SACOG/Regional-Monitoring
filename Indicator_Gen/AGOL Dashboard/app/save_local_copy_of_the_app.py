

'''
Used to get local copy json objects of the experience builder live and draft versions
'''

from pathlib import Path
import json
import sys
sys.path.append(str(Path(__file__).parent))
import experience as exp


PATH_OUT = r"I:\Projects\Josh\Regional Monitoring\exp_app_json"
EXPORT=True


if __name__ == '__main__':

    yaml_exp = exp.read_yaml_exp()

    gis = exp.connect_to_agol()
    item, exp_builder_app, exp_draft = exp.get_draft_exp_builder_app(gis, exp.ID_REGIONAL_INDICATORS_DASHBOARD)
    exp_live = item.get_data(try_json=True)

    if EXPORT:
        with open(PATH_OUT+'\\exp_live_202606.txt', "w") as file:
            json.dump(exp_live, file, indent=4)
        with open(PATH_OUT+"\\exp_draft_202606.txt", "w") as file:
            json.dump(exp_draft, file, indent=4)
