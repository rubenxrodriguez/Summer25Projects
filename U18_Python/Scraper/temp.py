import pandas as pd

df = pd.read_csv('fiba_ncaa_australia.csv')
df.sort_values(by='PER_career')
print(df)