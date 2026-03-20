


## TODO:
# Weird crosswalk issue with the female utility workers


from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent/'config'))
import rhna
yaml_file = rhna.load_yaml()


INDICATOR = Path(__file__).stem
params = yaml_file[INDICATOR]


if __name__ == '__main__':
    rhna.main_acs(INDICATOR, params)
