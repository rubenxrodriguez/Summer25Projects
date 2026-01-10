import pandas as pd
from io import StringIO

a10_team_def_ratings = """
Team,TeamDefRtg
George Mason Patriots,85.8
Massachusetts Minutewomen,86.5
Rhode Island Rams, 87.7
Saint Joseph's Hawks, 88.0
Virginia Commonwealth Rams, 88.2
Richmond Spiders, 88.4 
Davidson Wildcats, 89.1
Fordham Rams, 89.6
Dayton Flyers, 89.6
Duquesne Dukes, 90.3
George Washington Revolutionaries
La Salle Explorers, 97.1
Loyola (Chicago) Ramblers, 97.2
Saint Louis Billikens, 99.7
St. Bonaventure Bonnies, 103.7
"""
a10_team_def_df = pd.read_csv(StringIO(a10_team_def_ratings))

a10_team_name_map = {
    # Atlantic 10 Conference Teams
    'VCU': 'Virginia Commonwealth Rams',
    'Virginia Commonwealth': 'Virginia Commonwealth Rams',
    'Massachusetts': 'Massachusetts Minutewomen',
    'UMass': 'Massachusetts Minutewomen',
    'Dayton': 'Dayton Flyers',
    'Fordham': 'Fordham Rams',
    'George Washington': 'George Washington Revolutionaries',
    'GW': 'George Washington Revolutionaries',
    'Davidson': 'Davidson Wildcats',
    'Richmond': 'Richmond Spiders',
    "Saint Joseph's": "Saint Joseph's Hawks",
    "St. Joseph's": "Saint Joseph's Hawks",
    'Rhode Island': 'Rhode Island Rams',
    'URI': 'Rhode Island Rams',
    'Loyola Chicago': 'Loyola (Chicago) Ramblers',
    'Loyola (Chicago)': 'Loyola (Chicago) Ramblers',
    'George Mason': 'George Mason Patriots',
    'GMU': 'George Mason Patriots',
    'St. Bonaventure': 'St. Bonaventure Bonnies',
    'Bonaventure': 'St. Bonaventure Bonnies',
    'Duquesne': 'Duquesne Dukes',
    'Saint Louis': 'Saint Louis Billikens',
    'SLU': 'Saint Louis Billikens',
    'La Salle': 'La Salle Explorers',
}
#------------------------------------
aac_team_def_ratings = """
Team,TeamDefRtg
Texas-(San Antonio) Roadrunners,84.4
North Texas Mean Green,85.3
East Carolina Pirats,87.1
Tulane Green Wave,87.5
Temple Owls,87.7
Tusla Golden Hurricane,88.4
Rice Owls,89.9
South FLorida Bulls,91.0
FLorida Atlantic,94.0
Wichita State Shockers,94.1
UAB Blazers,94.9
Charlotte 49ers,97.7
Memphis Tigers,105.0

"""
aac_team_def_ratings = pd.read_csv(StringIO(aac_team_def_ratings))
aac_team_name_map = {
    # Ordered exactly as requested
    'UTSA': 'Texas-(San Antonio) Roadrunners',
    'North Texas': 'North Texas Mean Green',
    'East Carolina': 'East Carolina Pirates',
    'Tulane': 'Tulane Green Wave',
    'Temple': 'Temple Owls',
    'Tulsa': 'Tulsa Golden Hurricane',
    'Rice': 'Rice Owls',
    'South Fla.': 'South Florida Bulls',
    'Fla. Atlantic': 'Florida Atlantic Owls',
    'Wichita St.': 'Wichita State Shockers',
    'UAB': 'UAB Blazers',
    'Charlotte': 'Charlotte 49ers',
    'Memphis': 'Memphis Tigers'
}
#------------------------------------
ivy_team_def_ratings = """
Team,TeamDefRtg
Harvard Crimson,80.7
Columbia Lions,88.1
Princeton Tigers,89.3
Pennsylvania Quakers, 94.1
Cornell Big Red, 95.4
Brown Bears, 96.5
Dartmouth Big Green, 99.7
Yale Bulldogs, 103.8
"""
ivy_team_def_ratings = pd.read_csv(StringIO(ivy_team_def_ratings))

ivy_team_name_map = {
    'Brown': 'Brown Bears',
    'Harvard': 'Harvard Crimson',
    'Yale': 'Yale Bulldogs',
    'Dartmouth': 'Dartmouth Big Green',
    'Columbia': 'Columbia Lions',
    'Penn': 'Pennsylvania Quakers',  # Note: 'Penn' is the common abbreviation
    'Cornell': 'Cornell Big Red',
    'Princeton': 'Princeton Tigers',
}
#------------------------------------
mvc_team_def_ratings = """
Team,TeamDefRtg
Missouri State Lady Bears,89.8
Belmont Bruins,91.2
Bradley Braves,91.3
Murray State Racers,95.2
Illinois-Chicago Flames,95.4
Drake Bulldogs,97.1
Northern Iowa Panthers,97.9
Valparaiso University,98.0
Illinois State Redbirds,98.5
Evansville Aces,102.0
Indiana State Sycamores,105.2
Southern Illinois Salukis,109.7

"""
mvc_team_def_df = pd.read_csv(StringIO(mvc_team_def_ratings))

mvc_team_name_map = {
    'Missouri St.': 'Missouri State Lady Bears',
    'Belmont': 'Belmont Bruins',
    'Bradley': 'Bradley Braves',
    'Murray St.': 'Murray State Racers',
    'UIC': 'Illinois-Chicago Flames',
    'Drake': 'Drake Bulldogs',
    'UNI': 'Northern Iowa Panthers',
    'Valparaiso': 'Valparaiso University',
    'Illinois St.': 'Illinois State Redbirds',
    'Evansville': 'Evansville Aces',
    'Indiana St.': 'Indiana State Sycamores',
    'Southern Ill.': 'Southern Illinois Salukis'
}
df_df = pd.read_csv('cbba/mvc_players.csv')
#print('*'*30)
#print(df_df['teamMarket'].unique())

#------------------------------------
mw_team_def_ratings = """
Team,TeamDefRtg
UNLV Rebels,91.1
San Diego State Aztecs,91.6
Wyoming Cowgirls,91.7
Air Force Falcons,93.9
Colorado State Rams,94.5
New Mexico Lobos,95.8
Boise State Broncos,97.1
Fresno State Bulldogs,99.8
Nevada Wolf Pack,100.2
San Jose State Spartans,103.9
Utah State Aggies,105.4

"""
mw_team_def_df = pd.read_csv(StringIO(mw_team_def_ratings))

mwc_team_name_map = {
    # Mountain West Conference Teams in requested order
    'UNLV': 'UNLV Rebels',
    'San Diego St.': 'San Diego State Aztecs',
    'Wyoming': 'Wyoming Cowgirls',
    'Air Force': 'Air Force Falcons',
    'Colorado St.': 'Colorado State Rams',
    'New Mexico': 'New Mexico Lobos',
    'Boise St.': 'Boise State Broncos',
    'Fresno St.': 'Fresno State Bulldogs',
    'Nevada': 'Nevada Wolf Pack',
    'San Jose St.': 'San Jose State Spartans',
    'Utah St.': 'Utah State Aggies'
}
#------------------------------------
["Saint Mary's Gaels" 'Loyola Marymount Lions' 'San Francisco Dons'
 'Portland Pilots' 'Pacific Tigers' 'Santa Clara Broncos'
 'Pepperdine Waves' 'Gonzaga Bulldogs' 'San Diego Toreros']

['LMU (CA)' 'Pepperdine' 'Portland' 'San Diego' 'Pacific' 'Gonzaga'
 'San Francisco' 'Santa Clara' 'Oregon St.' 'Washington St.'
 "Saint Mary's (CA)"]

wcc_team_name_map = {
    "LMU (CA)": "Loyola Marymount Lions",
    "Pepperdine": "Pepperdine Waves",
    "Portland": "Portland Pilots",
    "San Diego": "San Diego Toreros",
    "Pacific": "Pacific Tigers",
    "Gonzaga": "Gonzaga Bulldogs",
    "San Francisco": "San Francisco Dons",
    "Santa Clara": "Santa Clara Broncos",
    "Oregon St.": "Oregon State Beavers",
    "Washington St.": "Washington State Cougars",
    "Saint Mary's (CA)": "Saint Mary's Gaels"
}
wcc_team_def_ratings = """
Team,TeamDefRtg
Saint Mary's Gaels, 94.9
Loyola Marymount Lions, 99.5
Portland Pilots, 90.5 
Pacific Tigers, 92.7
Santa Clara Broncos, 99.3
Pepperdine Waves, 98.9
Gonzaga Bulldogs, 95.9
San Diego Toreros, 99.8
San Francisco Dons, 92.6
Oregon State Beavers, 93.7 
Washington State Cougars, 95.3
"""

wcc_team_def_df = pd.read_csv(StringIO(wcc_team_def_ratings))
all_team_maps = [wcc_team_name_map,
                 a10_team_name_map,
                 aac_team_name_map,
                 ivy_team_name_map,
                 mvc_team_name_map,
                 mwc_team_name_map]

combined_team_def = pd.concat([a10_team_def_df, aac_team_def_ratings, ivy_team_def_ratings, mvc_team_def_df, mw_team_def_df, wcc_team_def_df], ignore_index=True)
combined_team_def.to_csv('data/combined_team_defrtgs.csv',index = False)

print(all_team_maps)