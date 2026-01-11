import pandas as pd 
df = pd.read_csv('progression.csv')
print(df.columns)

['interval_num', 'interval_len',
       'lineup', 'minutes', 'rel_PM_p40', 'PM_p40', 'o_poss',
       'd_poss','plus_minus', 'net_rtg', 'off_rtg', 'def_rtg','poss_total',
       'rel_net_rtg','team_minutes', 'team_plus_minus', 'team_pts_for', 'team_pts_against',
       'team_o_poss', 'team_d_poss', 'team_poss_total', 'team_off_rtg',
       'team_def_rtg', 'team_net_rtg', 'team_PM_p40','interval_start', 'interval_end'
       'pts_for', 'pts_against','net_pts',
       'o_eFG%', 'd_eFG%', 'o_TOV%', 'd_TOV%', 'o_orbR',
       'd_orbR', 'o_ftaR', 'd_ftaR', 
        'rel_off_rtg', 'rel_def_rtg', 
        ]

['interval_num', 'interval_len',
       'lineup', 'minutes', 'rel_PM_p40', 'PM_p40', 'o_poss',
       'd_poss','plus_minus', 'net_rtg', 'off_rtg', 'def_rtg','poss_total',
       'rel_net_rtg','team_minutes', 'team_plus_minus', 'team_pts_for', 'team_pts_against',
       'team_o_poss', 'team_d_poss', 'team_poss_total', 'team_off_rtg',
       'team_def_rtg', 'team_net_rtg', 'team_PM_p40','interval_start', 'interval_end'
       'pts_for', 'pts_against','net_pts',
       'o_eFG%', 'd_eFG%', 'o_TOV%', 'd_TOV%', 'o_orbR',
       'd_orbR', 'o_ftaR', 'd_ftaR', 
        'rel_off_rtg', 'rel_def_rtg', 
        ]