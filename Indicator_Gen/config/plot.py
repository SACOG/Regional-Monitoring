

from pathlib import Path
from datetime import date
from datetime import datetime
PATH_PLOTS = Path(r"\\webmapping-svr\c$\inetpub\wwwroot\monitoring")

font_family = 'Microsoft YaHei'
# font_family = 'Arial Black, Arial, sans-serif'
template = 'plotly_white'
config={'modeBarButtonsToRemove': ['select', 'lasso', 'toImage'], 'displaylogo': False}
# config={'modeBarButtonsToRemove': ['select', 'lasso'], 'displaylogo': False}


def plot_agol(fig, export, title, indicator, plot_name):
    fig.update_layout(
        legend_title=None
        , title=title
        , template=template
        , font_family=font_family
        , xaxis_title=None
        , yaxis_title=None
        , yaxis=dict(tickfont=dict(size=12))
        , xaxis=dict(tickfont=dict(size=12))
        )

    fig.show(config=config)
    
    if export:

        file_html = PATH_PLOTS / f'{indicator}_{plot_name}.html'
        file_png  = PATH_PLOTS / 'png' / f'{indicator}_{plot_name}.png'
        fig.write_html( file=file_html, config=config)
        fig.write_image(file=file_png, scale=1, width=1000, height=500)
       


plots_link = 'https://mapping.sacog.org/monitoring/Data/'


sacog_colors = {
    # Main
    'orange': '#E57149'
    , 'olive greenish': '#7EB460'
    , 'green': '#00A97D'
    , 'blue': '#27AAE1'
    , 'purple': '#6764A6'
    , 'magenta': '#A24F82'

    # Secondary
    , 'navy': '#006883'
    , 'blue grey': '#149ABF'
    , 'light blue': '#55C8E8'
    , 'very light blue': '#96D2E8'
    , 'grey': '#808285'
}

colors_source = {
    'ACS5': "#7EB460"
    , 'ACS1': '#27AAE1'
}


colors_counties = {
    'Sacramento': '#7EB460'
    , 'Placer': '#A24F82'
    , 'Yolo': '#27AAE1'
    , 'El Dorado': '#6764A6'
    , 'Sutter': '#E57149'
    , 'Yuba': '#00A97D'
}

colors_peers = {
    
    'SACOG': '#E57149'
    , 'Sacramento, CA': "#E57149"
    , 'Yuba City, CA': "#E57149"

    , 'National': "#7EB460"
    , 'Peer MSA': '#27AAE1'

    , 'Austin, TX': "#27AAE1"
    , 'Charlotte, NC': "#27AAE1"
    , 'Cincinnati, OH': "#27AAE1"
    , 'Cleveland, OH': "#27AAE1"
    , 'Columbus, OH': "#27AAE1"
    , 'Detroit, MI': "#27AAE1"
    , 'Indianapolis, IN': "#27AAE1"
    , 'Kansas City, MO': "#27AAE1"
    , 'Miami, FL': "#27AAE1"
    , 'Orlando, FL': "#27AAE1"
    , 'Phoenix, AZ': "#27AAE1"
    , 'Pittsburgh, PA': "#27AAE1"
    , 'Portland, OR': "#27AAE1"
    , 'Riverside, CA': "#27AAE1"
    , 'Salt Lake City, UT': "#27AAE1"
    , 'San Antonio, TX': "#27AAE1"
    , 'San Diego, CA': "#27AAE1"
    , 'San Francisco, CA': "#27AAE1"
    , 'San Jose, CA': "#27AAE1"
    , 'St. Louis, MO': "#27AAE1"
    , 'Tampa, FL': "#27AAE1"

    ,  'Sacramento':'#E57149'
    , 'Austin':'#27AAE1'
    , 'Charlotte':'#27AAE1'
    , 'Cincinnati':'#27AAE1'
    , 'Cleveland':'#27AAE1'
    , 'Columbus':'#27AAE1'
    , 'Detroit':'#27AAE1'
    , 'Indianapolis':'#27AAE1'
    , 'Kansas City':'#27AAE1'
    , 'Miami':'#27AAE1'
    , 'Orlando':'#27AAE1'
    , 'Phoenix-Mesa':'#27AAE1'
    , 'Pittsburgh':'#27AAE1'
    , 'Portland':'#27AAE1'
    , 'Riverside-San Bernardino':'#27AAE1'
    , 'San Antonio':'#27AAE1'
    , 'San Diego':'#27AAE1'
    , 'San Francisco-Oakland':'#27AAE1'
    , 'San Jose':'#27AAE1'
    , 'St Louis':'#27AAE1'
    , 'Tampa-St Petersburg':'#27AAE1'
}

colors_sac_yuba = {
         'Sacramento, CA': "#7EB460",
         'Yuba City, CA': "#E57149",
         "Peer MSA": "#27AAE1"
}

colors_ca = {
    'Sacramento': '#E57149'
    , 'SACOG': '#E57149'
    , 'Yuba City': '#7EB460'
    , 'MTC': '#A24F82'
    , 'Bay Area': '#A24F82'
    , 'San Francisco': '#A24F82'
    , 'San Francisco Bay Area': '#A24F82'
    , 'San Jose': '#55C8E8'
    , 'Greater LA': "#6764A6"
    , 'Los Angeles': '#6764A6'
    , 'SCAG': '#6764A6'
    , 'Riverside': '#149ABF'
    , 'San Joaquin Valley':"#149ABF"
    , 'San Diego': "#808285"
    , 'SANDAG': "#808285"
    , 'California': "#00A97D"
    , 'Rest of State':"#55C8E8"
}

colors_tims_peers = {
    'Sacramento Region': '#27AAE1'
    , 'SACOG': '#27AAE1'
    , 'MTC': '#A24F82'
    , 'SCAG': '#6764A6'
    , 'SANDAG': "#7EB460"
    , 'California': '#E57149'
}

colors_ca_tims = {
    'Sacramento Region': '#27AAE1'
    , 'California': '#E57149'
}

colors_ca_housing = {
    "State Total":"#7EB460"
    , "Rest of State": "#27AAE1"
    , "San Diego": "#27AAE1"
    , "Los Angeles": "#27AAE1"
    , "San Francisco Bay Area": "#27AAE1"
    , "San Joaquin Valley": "#27AAE1"
    , "Sacramento": "#E57149"

    , 'Number of New Housing Units Built':'#27AAE1'
    , 'Estimated Number of Households Added':'#E57149'

    , "Multi Family":"#27AAE1"
    , "Single Family Large Lot": "#7EB460"
    , "Single Family Small Lot": "#E57149"
}

colors_com = {
    'Rural Residential':"#7EB460"
       , 'Established Communities':"#E57149"
       , 'Centers and Corridors':'#27AAE1'
       , 'Developing Communities':"#6764A6"
       , 'Agriculture Land':"#A24F82"
}

colors_ag = {
    'Unique Farmland':"#E57149"
       , 'Farmland of Statewide Importance':"#7EB460"
       , 'Prime Farmland':'#27AAE1'
       , 'Farmland of Local Importance/Potential':"#A24F82"
}

colors_nd = {
    'Flood Zone':"#27AAE1"
       , 'Fire Zone':"#E57149"
}

colors_race  = {
    'American Indian or Alaska Native (NH)': '#96D2E8'
    , 'American Indian or Alaska Native': '#96D2E8'
    , 'American Indian or<br>Alaska Native (NH)': '#96D2E8'
    , 'American Indian or<br>Alaska Native': '#96D2E8'
    , 'Native Hawaiian or other Pacific Islander (NH)': '#55C8E8'
    , 'Native Hawaiian or other Pacific Islander': '#55C8E8'
    , 'Native Hawaiian or<br>other Pacific Islander (NH)': '#55C8E8'
    , 'Native Hawaiian or<br>other Pacific Islander': '#55C8E8'
    , 'Some other race (NH)': '#00A97D'
    , 'Some other race': '#00A97D'
    , 'Two or more races (NH)': '#6764A6'
    , 'Two or more races': '#6764A6'
    , 'Asian (NH)': '#27AAE1'
    , 'Asian': '#27AAE1'
    , 'Black or African American (NH)': '#7EB460'
    , 'Black or African American': '#7EB460'
    , 'Black or<br>African American (NH)': '#7EB460'
    , 'Black or<br>African American': '#7EB460'
    , 'Black': '#7EB460'
    , 'Hispanic or Latino': "#E57149"
    , 'Hispanic or<br>Latino': "#E57149"
    , 'Hispanic': "#E57149"
    , 'White (NH)': "#A24F82"
    , 'White': "#A24F82"
    , 'Socioeconomically Disadvantaged': '#00A97D'
    , 'Socioeconomically<br>Disadvantaged': '#00A97D'
    , 'Total': '#006883'
}

colors_age = {
    'Under 18': '#27AAE1'
    , '18 to 64': '#E57149'
    , '65+': '#7EB460'
}

colors_commute = {
    'Car, truck, or van Drove alone':"#006883"
       , 'Car, truck, or van':'#006883'
       , 'Car, truck, or van Carpooled':"#00A97D"
       , 'Public transportation (excluding taxicab)':'#A24F82'
       , 'Public transportation (bus, subway, or rail)':'#A24F82'
       , 'Bicycle':"#6764A6"
       , 'Walked':"#7EB460"
       , 'Other means': '#E57149'
       , 'Other method': '#E57149'
       , 'Worked from home':'#27AAE1'
       
       , 'Walk':'#7EB460'
       , 'Bike': '#6764A6'
       , 'Public Transit':"#A24F82"
       , 'Drive':"#006883"
}

colors_trips = {
       'Walking':'#7EB460'
       , 'Biking': '#6764A6'
}

colors_edu  = {
    'Total Less than high school diploma':'#27AAE1'
    , 'Total High school graduate or GED':'#E57149'
    , "Total Some college or associate's degree":'#7EB460'
    , "Total Bachelor's degree or higher":'#A24F82'

    , 'Less than high school diploma':'#27AAE1'
    , 'High school graduate or GED':'#E57149'
    , "Some college or associate's degree":'#7EB460'
    , "Bachelor's degree or higher":'#A24F82'

    , 'Graduate':'#006883'
    , "Bachelor":'#A24F82'
    , "Associate":'#7EB460'
    
    , 'STEM':'#27AAE1'
    , "AHSS":'#E57149'
    , "Education":'#7EB460'
    , 'Health': '#A24F82'
    , 'Business': '#006883'
    , 'Trades': '#6764A6'
    , 'Multi':'#00A97D'
}

colors_broadband  = {
    'Low Speed':'#27AAE1'
    , 'High Speed':'#E57149'
    , "No Internet or No Computer":'#7EB460'
}

colors_burden  = {
    'Cost burden >50%': '#E57149'
    , 'Cost burden >30% to <=50%': '#7EB460'
    , 'Cost burden <30%': '#27AAE1'

}

colors_labor = {
         "Employed":"#E57149",
         "Unemployed": "#27AAE1",
         "Not in Labor Force": "#7EB460"
}

colors_veh = {
       'No vehicles':"#E57149"
       , '3 or more vehicles':"#27AAE1"
       , '2 vehicles': '#7EB460'
       , '1 vehicle':'#A24F82'
       , 'N/A (GQ/vacant)': '#808285'
}

colors_commute_time = {
    'No commute (worked from home)':"#E57149"
       , '0 to 15 minutes':"#27AAE1"
       , '15 to 30 minutes': '#7EB460'
       , 'More than 30 minutes':'#A24F82'
}

colors_goods_services = {
    'Goods Producing': '#E57149'
    , 'Service-Providing':'#27AAE1'
}

colors_safety = {
    'Fatal Collisions': '#27AAE1'
    , 'Serious Injury Collisions': '#E57149'
    , 'Total Injury Collisions': '#7EB460'
    , 'Bicyclists': '#27AAE1'
    , 'Pedestrians': '#E57149'

    , 'Fatality': '#27AAE1'
    , 'Serious Injury': '#E57149'
    , 'All Collisions': '#7EB460'

    , 'EPC': '#7EB460'
    , 'Non-EPC': '#27AAE1'
}

colors_transit  = {
    'Demand Response': '#E57149'
    , 'Light Rail': '#27AAE1'
    , 'Local Bus': '#7EB460'
    , 'Commuter Bus': '#A24F82'

    , 'Over-the-road Bus': '#E57149'
    , 'Light Rail Vehicle': '#A24F82'
    , 'Bus': '#27AAE1'
    , 'Van': '#6764A6'
    , 'Cutaway': '#7EB460'
    , 'Double Decker Bus': '#00A97D'
}

colors_hwy = {
    'Interstate':'#E57149'
    , 'Non-Interstate':'#27AAE1'
}

colors_homeless = {
    'Sheltered':'#E57149'
    , 'Unsheltered':'#27AAE1'
}

colors_mortgage = {
    'Female to Male': '#E57149'
    , 'Hispanic or Latino to Not Hispanic or Latino': '#27AAE1'
    , 'Non-White to White': "#7EB460"
    , 'Asian to White': "#A24F82"
    , 'Black or African American to White': '#00A97D'
}

colors_mtip = {
    'Exempt':'#7EB460'
    , 'Nonexempt':'#55C8E8'

    , 'Highways': '#E57149'
    , 'Streets & Roads': '#00A97D'
    , 'Streets/Roads': '#00A97D'
    , 'Transit': '#6764A6'
    , 'Other': '#27AAE1'
    , 'Bridges': '#A24F82'
}

colors_tradeable = {
    'Local': '#E57149'
    , 'Tradeable': '#27AAE1'
    , 'Public Administration': '#7EB460'
}

colors_tradeable_sub = {
    'Professional, Business, and Tech Services': '#27AAE1'
    , 'Wholesale and Transportation': '#E57149'
    , 'Manufacturing': '#7EB460'
    , 'Tourism and Entertainment': '#A24F82'
    , 'Resource': '#00A97D'
}

colors_burden2 = { 
    'Cost burden <=30%': '#27AAE1'
    , 'Cost burden >30% to <=50%': '#7EB460'
    , 'Cost burden >50%': '#E57149'
    
    , 'Cost burden >30%': '#7EB460'

}

# colors_tradeable_sub = {
#     'Professional, Business, and Tech Services': '#6764A6'
#     , 'Wholesale and Transportation': '#006883'
#     , 'Manufacturing': '#96D2E8'
#     , 'Tourism and Entertainment': '#808285'
#     , 'Resource': '#149ABF'
# }

# sacog_colors = {
#     # Main
#     'orange': '#E57149'
#     , 'olive greenish': '#7EB460'
#     , 'green': '#00A97D'
#     , 'blue': '#27AAE1'
#     , 'purple': '#6764A6'
#     , 'magenta': '#A24F82'

#     # Secondary
#     , 'navy': '#006883'
#     , 'blue grey': '#149ABF'
#     , 'light blue': '#55C8E8'
#     , 'very light blue': '#96D2E8'
#     , 'grey': '#808285'
# }

colors_banking = {
    'Unbanked': '#006883'
    , 'Underbanked': '#7EB460'
}

colors_vmt = {
    'SB150': '#E57149'
    , 'HPMS': '#27AAE1'
    , 'Replica': '#7EB460'
}

colors_overcrowding = {
    'One or less occupants per room': '#27AAE1'
    , 'More than one occupant per room': '#7EB460'
}

sort_peers = [
    'Sacramento, CA'
    , 'Yuba City, CA'
    , 'Austin, TX'
    , 'Charlotte, NC'
    , 'Cincinnati, OH'
    , 'Cleveland, OH'
    , 'Columbus, OH'
    , 'Detroit, MI'
    , 'Indianapolis, IN'
    , 'Kansas City, MO'
    , 'Miami, FL'
    , 'Orlando, FL'
    , 'Phoenix, AZ'
    , 'Pittsburgh, PA'
    , 'Portland, OR'
    , 'Riverside, CA'
    , 'Salt Lake City, UT'
    , 'San Antonio, TX'
    , 'San Diego, CA'
    , 'San Francisco, CA'
    , 'San Jose, CA'
    , 'St. Louis, MO'
    , 'Tampa, FL'
    , 'National'
]

pop_eth_labels  = {
    'All': 'All'
    , 'American Indian or Alaska Native (NH)': 'American Indian or Alaska Native'
    , 'Asian (NH)': 'Asian'
    , 'Black or African American (NH)': 'Black or African American'
    , 'Hispanic or Latino': 'Hispanic or Latino'
    , 'Native Hawaiian or other Pacific Islander (NH)': 'Native Hawaiian or other Pacific Islander'
    , 'Some other race (NH)': 'Some other race'
    , 'Two or more races (NH)': 'Two or more races'
    , 'White (NH)': 'White (NH)'
}

peer_msa_labels = {
    'Sacramento'                                                               : 'Sacramento, CA' 
    , 'Sacramento-Roseville-Folsom'                                            : 'Sacramento, CA'
    , 'Sacramento-Roseville-Folsom, CA'                                        : 'Sacramento, CA'
    , 'Sacramento--Roseville--Arden-Arcade, CA'                                : 'Sacramento, CA'
    , 'Sacramento-Roseville-Folsom, CA Metro Area'                             : 'Sacramento, CA'
    , 'Sacramento--Roseville--Arden-Arcade, CA Metro Area'                     : 'Sacramento, CA'
    , 'Sacramento--Arden-Arcade--Roseville, CA Metro Area'                     : 'Sacramento, CA'
    , 'Sacramento--Roseville--Arden-Arcade, CA Metropolitan Statistical Area'  : 'Sacramento, CA'
    , 'Yuba City'                                                              : 'Yuba City, CA'
    , 'Yuba City, CA'                                                          : 'Yuba City, CA'
    , 'Yuba City, CA Metro Area'                                               : 'Yuba City, CA'
    , 'Yuba City, CA Metropolitan Statistical Area'                            : 'Yuba City, CA'
    , 'Austin'                                                                 : 'Austin, TX'
    , 'Austin-Round Rock, TX'                                                  : 'Austin, TX'
    , 'Austin-Round Rock-Georgetown'                                           : 'Austin, TX'
    , 'Austin-Round Rock-Georgetown, TX'                                       : 'Austin, TX'
    , 'Austin-Round Rock, TX Metro Area'                                       : 'Austin, TX'
    , 'Austin-Round Rock-Georgetown, TX Metro Area'                            : 'Austin, TX'
    , 'Austin-Round Rock-San Marcos, TX Metro Area'                            : 'Austin, TX'
    , 'Austin-Round Rock, TX Metropolitan Statistical Area'                    : 'Austin, TX'
    , 'Charlotte'                                                              : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia'                                             : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia, NC-SC'                                      : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia, NC-SC Metro Area'                           : 'Charlotte, NC'
    , 'Charlotte-Concord-Gastonia, NC-SC Metropolitan Statistical Area'        : 'Charlotte, NC'
    , 'Cincinnati'                                                             : 'Cincinnati, OH'
    , 'Cincinnati, OH-KY-IN'                                                   : 'Cincinnati, OH'
    , 'Cincinnati, OH-KY-IN Metro Area'                                        : 'Cincinnati, OH'
    , 'Cincinnati, OH-KY-IN Metropolitan Statistical Area'                     : 'Cincinnati, OH'
    , 'Cleveland-Elyria'                                                       : 'Cleveland, OH'
    , 'Cleveland-Elyria, OH'                                                   : 'Cleveland, OH'
    , 'Cleveland, OH Metro Area'                                               : 'Cleveland, OH'
    , 'Cleveland-Elyria, OH Metro Area'                                        : 'Cleveland, OH'
    , 'Cleveland-Elyria-Mentor, OH Metro Area'                                 : 'Cleveland, OH'
    , 'Cleveland-Elyria, OH Metropolitan Statistical Area'                     : 'Cleveland, OH'
    , 'Columbus'                                                               : 'Columbus, OH'
    , 'Columbus, OH'                                                           : 'Columbus, OH'
    , 'Columbus, OH Metro Area'                                                : 'Columbus, OH'
    , 'Columbus, OH Metropolitan Statistical Area'                             : 'Columbus, OH'
    , 'Detroit'                                                                : 'Detroit, MI'
    , 'Detroit-Warren-Dearborn'                                                : 'Detroit, MI'
    , 'Detroit-Warren-Dearborn, MI'                                            : 'Detroit, MI'
    , 'Detroit-Warren-Livonia, MI Metro Area'                                  : 'Detroit, MI'
    , 'Detroit-Warren-Dearborn, MI Metro Area'                                 : 'Detroit, MI'
    , 'Detroit-Warren-Dearborn, MI Metropolitan Statistical Area'              : 'Detroit, MI'
    , 'Indianapolis'                                                           : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson'                                           : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson, IN'                                       : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson, IN Metro Area'                            : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Greenwood, IN Metro Area'                           : 'Indianapolis, IN'
    , 'Indianapolis-Carmel-Anderson, IN Metropolitan Statistical Area'         : 'Indianapolis, IN'
    , 'Kansas City'                                                            : 'Kansas City, MO'
    , 'Kansas City, MO-KS'                                                     : 'Kansas City, MO'
    , 'Kansas City, MO-KS Metro Area'                                          : 'Kansas City, MO'
    , 'Kansas City, MO-KS Metropolitan Statistical Area'                       : 'Kansas City, MO'
    , 'Kansas City, MO-KS (Metropolitan Statistical Area)'                     : 'Kansas City, MO'
    , 'Miami'                                                                  : 'Miami, FL'
    , 'Miami-Fort Lauderdale-Pompano Beach'                                    : 'Miami, FL'
    , 'Miami-Fort Lauderdale-Pompano Beach, FL'                                : 'Miami, FL'
    , 'Miami-Fort Lauderdale-West Palm Beach, FL'                              : 'Miami, FL'
    , 'Miami-Fort Lauderdale-Pompano Beach, FL Metro Area'                     : 'Miami, FL'
    , 'Miami-Fort Lauderdale-West Palm Beach, FL Metro Area'                   : 'Miami, FL'
    , 'Miami-Fort Lauderdale-West Palm Beach, FL Metropolitan Statistical Area': 'Miami, FL'
    , 'Orlando'                                                                : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford'                                              : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford, FL'                                          : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford, FL Metro Area'                               : 'Orlando, FL'
    , 'Orlando-Kissimmee-Sanford, FL Metropolitan Statistical Area'            : 'Orlando, FL'
    , 'Phoenix'                                                                : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Chandler'                                                  : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Chandler, AZ'                                              : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Scottsdale, AZ'                                            : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Chandler, AZ Metro Area'                                   : 'Phoenix, AZ'
    , 'Phoenix-Mesa-Scottsdale, AZ Metropolitan Statistical Area'              : 'Phoenix, AZ'
    , 'Pittsburgh'                                                             : 'Pittsburgh, PA'
    , 'Pittsburgh, PA'                                                         : 'Pittsburgh, PA'
    , 'Pittsburgh, PA Metro Area'                                              : 'Pittsburgh, PA'
    , 'Pittsburgh, PA Metropolitan Statistical Area'                           : 'Pittsburgh, PA'
    , 'Portland'                                                               : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro'                                           : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro, OR-WA'                                    : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro, OR-WA Metro Area'                         : 'Portland, OR'
    , 'Portland-Vancouver-Beaverton, OR-WA Metro Area'                         : 'Portland, OR'
    , 'Portland-Vancouver-Hillsboro, OR-WA Metropolitan Statistical Area'      : 'Portland, OR'
    , 'Riverside'                                                              : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario'                                       : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario, CA'                                   : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario, CA Metro Area'                        : 'Riverside, CA'
    , 'Riverside-San Bernardino-Ontario, CA Metropolitan Statistical Area'     : 'Riverside, CA'
    , 'Salt Lake City'                                                         : 'Salt Lake City, UT'
    , 'Salt Lake City, UT'                                                     : 'Salt Lake City, UT'
    , 'Salt Lake City, UT Metro Area'                                          : 'Salt Lake City, UT'
    , 'Salt Lake City-Murray, UT Metro Area'                                   : 'Salt Lake City, UT'
    , 'Salt Lake City, UT Metropolitan Statistical Area'                       : 'Salt Lake City, UT'
    , 'San Antonio'                                                            : 'San Antonio, TX'
    , 'San Antonio-New Braunfels'                                              : 'San Antonio, TX'
    , 'San Antonio-New Braunfels, TX'                                          : 'San Antonio, TX'
    , 'San Antonio-New Braunfels, TX Metro Area'                               : 'San Antonio, TX'
    , 'San Antonio-New Braunfels, TX Metropolitan Statistical Area'            : 'San Antonio, TX'
    , 'San Diego'                                                              : 'San Diego, CA'
    , 'San Diego-Chula Vista-Carlsbad'                                         : 'San Diego, CA'
    , 'San Diego-Chula Vista-Carlsbad, CA'                                     : 'San Diego, CA'
    , 'San Diego-Carlsbad, CA'                                                 : 'San Diego, CA'
    , 'San Diego-Carlsbad, CA Metro Area'                                      : 'San Diego, CA'
    , 'San Diego-Carlsbad-San Marcos, CA Metro Area'                           : 'San Diego, CA'
    , 'San Diego-Chula Vista-Carlsbad, CA Metro Area'                          : 'San Diego, CA'
    , 'San Diego-Carlsbad, CA Metropolitan Statistical Area'                   : 'San Diego, CA'
    , 'San Francisco'                                                          : 'San Francisco, CA'
    , 'San Francisco-Oakland-Berkeley'                                         : 'San Francisco, CA'
    , 'San Francisco-Oakland-Berkeley, CA'                                     : 'San Francisco, CA'
    , 'San Francisco-Oakland-Hayward, CA'                                      : 'San Francisco, CA'
    , 'San Francisco-Oakland-Berkeley, CA Metro Area'                          : 'San Francisco, CA'
    , 'San Francisco-Oakland-Fremont, CA Metro Area'                           : 'San Francisco, CA'
    , 'San Francisco-Oakland-Hayward, CA Metro Area'                           : 'San Francisco, CA'
    , 'San Francisco-Oakland-Hayward, CA Metropolitan Statistical Area'        : 'San Francisco, CA'
    , 'San Jose'                                                               : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara'                                         : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara, CA'                                     : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara, CA Metro Area'                          : 'San Jose, CA'
    , 'San Jose-Sunnyvale-Santa Clara, CA Metropolitan Statistical Area'       : 'San Jose, CA'
    , 'St. Louis'                                                              : 'St. Louis, MO'
    , 'St. Louis, MO-IL'                                                       : 'St. Louis, MO'
    , 'St. Louis, MO-IL Metro Area'                                            : 'St. Louis, MO'
    , 'St. Louis, MO-IL Metropolitan Statistical Area'                         : 'St. Louis, MO'
    , 'Tampa'                                                                  : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater'                                        : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater, FL'                                    : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater, FL Metro Area'                         : 'Tampa, FL'
    , 'Tampa-St. Petersburg-Clearwater, FL Metropolitan Statistical Area'      : 'Tampa, FL'

    ## Other comparisons
    , 'Ann Arbor, MI Metro Area'                                               : 'Ann Arbor, MI'
    , 'Atlanta-Sandy Springs-Alpharetta, GA'                                   : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Roswell, GA Metro Area'                           : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Marietta, GA Metro Area'                          : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Alpharetta, GA Metro Area'                        : 'Atlanta, GA'
    , 'Atlanta-Sandy Springs-Alpharetta, GA (Metropolitan Statistical Area)'   : 'Atlanta, GA'
    , 'El Centro, CA Metro Area'                                               : 'El Centro, CA'
    , 'Los Angeles-Long Beach-Anaheim, CA Metro Area'                          : 'Los Angeles, CA'
    , 'Los Angeles-Long Beach-Santa Ana, CA Metro Area'                        : 'Los Angeles, CA'
    , 'Minneapolis-St. Paul-Bloomington, MN-WI'                                : 'Minneapolis, MN'
    , 'Minneapolis-St. Paul-Bloomington, MN-WI Metro Area'                     : 'Minneapolis, MN'
    , 'Minneapolis-St. Paul-Bloomington, MN-WI (Metropolitan Statistical Area)': 'Minneapolis, MN'
    , 'Monroe, MI Metro Area'                                                  : 'Monroe, MI'
    , 'Napa, CA Metro Area'                                                    : 'Napa, CA'
    , 'Oxnard-Thousand Oaks-Ventura, CA Metro Area'                            : 'Oxnard, CA'
    , 'Santa Rosa, CA Metro Area'                                              : 'Santa Rosa, CA'
    , 'Santa Rosa-Petaluma, CA Metro Area'                                     : 'Santa Rosa, CA'
    , 'Seattle-Tacoma-Bellevue, WA'                                            : 'Seattle, WA'
    , 'Seattle-Tacoma-Bellevue, WA Metro Area'                                 : 'Seattle, WA'
    , 'Seattle-Tacoma-Bellevue, WA (Metropolitan Statistical Area)'            : 'Seattle, WA'
    , 'Vallejo, CA Metro Area'                                                 : 'Vallejo, CA'
    , 'Vallejo-Fairfield, CA Metro Area'                                       : 'Vallejo, CA'
}

var_race = {
    'American Indian or Alaska Native (NH)': 'American Indian or<br>Alaska Native (NH)'
    , 'American Indian or Alaska Native': 'American Indian or<br>Alaska Native'
    , 'Native Hawaiian or other Pacific Islander (NH)': 'Native Hawaiian or<br>other Pacific Islander (NH)'
    , 'Native Hawaiian or other Pacific Islander': 'Native Hawaiian or<br>other Pacific Islander'
    , 'Some other race (NH)': 'Some other race (NH)'
    , 'Some other race': 'Some other race'
    , 'Two or more races (NH)': 'Two or more races (NH)'
    , 'Two or more races': 'Two or more races'
    , 'Asian (NH)': 'Asian (NH)'
    , 'Asian': 'Asian'
    , 'Black or African American (NH)': 'Black or<br>African American (NH)'
    , 'Black or African American': 'Black or<br>African American'
    , 'Black': 'Black'
    , 'Hispanic or Latino': 'Hispanic or<br>Latino'
    , 'Hispanic': 'Hispanic'
    , 'White (NH)': 'White (NH)'
    , 'White': 'White'
    , 'Socioeconomically Disadvantaged': 'Socioeconomically<br>Disadvantaged'
    , 'Total': 'Total'
}

var_edu = {
    'Total Less than high school diploma':'Less than high school diploma'
    , 'Total High school graduate or GED':'High school graduate or GED'
    , "Total Some college or associate's degree":"Some college or associate's degree"
    , "Total Bachelor's degree or higher":"Bachelor's degree or higher"
}

var_counties = {
    'EL DORADO': 'El Dorado'
    , 'El Dorado County': 'El Dorado'
    , 'PLACER': 'Placer'
    , 'Placer County': 'Placer'
    , 'SACRAMENTO': 'Sacramento'
    , 'Sacramento County': 'Sacramento'
    , 'SUTTER': 'Sutter'
    , 'Sutter County': 'Sutter'
    , 'YOLO': 'Yolo'
    , 'Yolo County': 'Yolo'
    , 'YUBA': 'Yuba'
    , 'Yuba County': 'Yuba'
}



# Graveyard for colors

# color_map_eth  = {
#     'Asian': '#9DC209'
#     , 'Asian (NH)': '#9DC209'
#     , 'Black or African American': '#1E90FF'
#     , 'Black or African American (NH)': '#1E90FF'
#     , 'Hispanic or Latino': "#FBB117"
#     , 'White (NH)': "#DC381F"
# }

# color_map_sac_yuba_peermsa = {
#          'Sacramento, CA': "#000000",
#          'Yuba City, CA': "#1F45FC",
#          "Peer MSA": "#9DC209"
# }

# color_map_nat_peermsa = {
#                  "SACOG": "#9DC209",
#                  "National": "#1F45FC",
#                  "Peer MSA": "#1E90FF"
# }

# color_map_comp = {
#                 "SACOG": "#000000",
#                  "California":"#9DC209",
#                  "National": "#DC381F",
#                  "Peer MSA": "#1E90FF"
# }

# color_map_nat_peers = {
#     'Sacramento, CA': "#9DC209"
#     , 'Yuba City, CA': "#9DC209"
#     , 'National': "#1F45FC"
#     , 'Austin, TX': "#1E90FF"
#     , 'Charlotte, NC': "#1E90FF"
#     , 'Cincinnati, OH': "#1E90FF"
#     , 'Cleveland, OH': "#1E90FF"
#     , 'Columbus, OH': "#1E90FF"
#     , 'Detroit, MI': "#1E90FF"
#     , 'Indianapolis, IN': "#1E90FF"
#     , 'Kansas City, MO': "#1E90FF"
#     , 'Miami, FL': "#1E90FF"
#     , 'Orlando, FL': "#1E90FF"
#     , 'Phoenix, AZ': "#1E90FF"
#     , 'Pittsburgh, PA': "#1E90FF"
#     , 'Portland, OR': "#1E90FF"
#     , 'Riverside, CA': "#1E90FF"
#     , 'Salt Lake City, UT': "#1E90FF"
#     , 'San Antonio, TX': "#1E90FF"
#     , 'San Diego, CA': "#1E90FF"
#     , 'San Francisco, CA': "#1E90FF"
#     , 'San Jose, CA': "#1E90FF"
#     , 'St. Louis, MO': "#1E90FF"
#     , 'Tampa, FL': "#1E90FF"
# }