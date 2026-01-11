import pandas as pd 


import os 
print('\n')
for file in os.listdir("Lineup Data/Game Lineups"):
    if file.endswith(".csv"):
        df = pd.read_csv(f"Lineup Data/Game Lineups/{file}")
        minutes_sum = df["team_poss_total"].mean()
        print(f"{file[-10:]}: {minutes_sum}")