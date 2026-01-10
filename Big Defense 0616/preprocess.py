import pandas as pd

team_name_map = {
    # WCC
    'LMU (CA)': 'Loyola Marymount Lions',
    'Pepperdine': 'Pepperdine Waves',
    'Portland': 'Portland Pilots',
    'San Diego': 'San Diego Toreros',
    'Pacific': 'Pacific Tigers',
    'Gonzaga': 'Gonzaga Bulldogs',
    'San Francisco': 'San Francisco Dons',
    'Santa Clara': 'Santa Clara Broncos',
    'Oregon St.': 'Oregon State Beavers',
    'Washington St.': 'Washington State Cougars',
    "Saint Mary's (CA)": "Saint Mary's Gaels",

    # A-10
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

    # AAC
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
    'Memphis': 'Memphis Tigers',

    # Ivy
    'Brown': 'Brown Bears',
    'Harvard': 'Harvard Crimson',
    'Yale': 'Yale Bulldogs',
    'Dartmouth': 'Dartmouth Big Green',
    'Columbia': 'Columbia Lions',
    'Penn': 'Pennsylvania Quakers',
    'Cornell': 'Cornell Big Red',
    'Princeton': 'Princeton Tigers',

    # MVC
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
    'Southern Ill.': 'Southern Illinois Salukis',

    # Mountain West
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


synergy_df = pd.read_csv('data/merged_synergy.csv')
cbba_df = pd.read_csv('data/merged_cbba.csv')
cbba_df['Team'] = cbba_df['teamMarket']
cbba_df['Player'] = cbba_df['fullName']
cbba_df.drop(columns = ['teamMarket', 'fullName','playerId'], inplace = True)
def apply_team_name_map(df,team_col,maps):
    df[team_col] = df[team_col].map(maps).fillna(df[team_col])
    return df

synergy_df = apply_team_name_map(synergy_df, 'Team', team_name_map)
cbba_df = apply_team_name_map(cbba_df, 'Team', team_name_map)

merged_df = pd.merge(cbba_df, synergy_df, on = ["Player", "Team"],how = "outer", suffixes = ('_cbba','_synergy'))

merged_df['Conf'] = merged_df['conf_synergy'].fillna(merged_df['conf_cbba'])
#print(merged_df.columns)
['height', 'mpg', 'gp', 'drtgPlayer', 'ortgPlayer', 'ws', 'ows', 'dws',
       'rapm', 'orapm', 'drapm', 'stl', 'blk', 'stlPg', 'blkPg', 'conf_cbba',
       'Team', 'Player', 'Poss', 'PPP', 'PPS', 'conf_synergy']


column_order = ['Player','Team','Conf','height', 'mpg', 'gp', 'drtgPlayer', 'ortgPlayer', 'ws', 'ows', 'dws',
       'rapm', 'orapm', 'drapm', 'stl', 'blk', 'stlPg', 'blkPg',
        'Poss', 'PPP', 'PPS']

merged_df = merged_df[column_order]

#merged_df.to_csv('outputs/merged_clean.csv',index = False)

def_rtgs = pd.read_csv('data/combined_team_defrtgs.csv')

merged_with_def = pd.merge(
    merged_df,
    def_rtgs,
    how = 'left',
    left_on = 'Team',
    right_on = 'Team'
)

merged_with_def.to_csv("outputs/merged_def.csv")